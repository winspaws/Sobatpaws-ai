"""Suggestion engine: menghasilkan saran klinis terstruktur untuk dokter.

Alur:
1. Ambil gejala dari IntakeResult (sudah ter-ekstrak).
2. Prediksi penyakit:
   - model ML symptom->disease (bila artefak tersedia untuk kategori), DAN
   - ranking berbasis grounding gejala (knowledge base).
   Keduanya digabung (ensemble sederhana) untuk robust saat data minim.
3. Grounding: ambil diagnosa, tindakan, produk, red flags, & safety dari KB.
4. (Opsional) LLM augmentation: ringkasan natural + pertanyaan lanjutan,
   tetap di-anchor ke kandidat & konteks grounding (mengurangi halusinasi).
5. Bungkus jadi AISuggestion + disclaimer.
"""
from __future__ import annotations

import json
import logging

from ..config import AISettings
from ..data_loader import KnowledgeBase
from .grounding import DiseaseCandidate, KnowledgeGrounder
from .llm import LLMClient
from .providers import get_provider_registry
from .safety import check_product_safety, collect_safety_warnings
from .schemas import (
    AISuggestion,
    ConsultationContext,
    IntakeResult,
    SuggestedDiagnostic,
    SuggestedDisease,
    SuggestedProduct,
    SuggestedTreatment,
)

logger = logging.getLogger("sobatpaws.ai.engine")


class SuggestionEngine:
    def __init__(self, kb: KnowledgeBase, llm: LLMClient | None = None):
        self.kb = kb
        self.grounder = KnowledgeGrounder(kb)
        self.llm = llm or LLMClient()

    def suggest(
        self, context: ConsultationContext, intake: IntakeResult, top_k: int = 5
    ) -> AISuggestion:
        symptoms = intake.symptom_name_ids()
        category = context.category_slug

        # 1) ensemble prediksi penyakit
        ml_scores = self._ml_predict(category, symptoms, top_k)
        kb_candidates = self.grounder.rank_diseases_by_symptoms(
            category, symptoms, top_k=top_k
        )
        diseases = self._ensemble(ml_scores, kb_candidates, top_k)

        # 2) grounding klinis untuk kandidat teratas
        top_slugs = [d.disease_slug for d in diseases]
        diagnostics = self._collect_diagnostics(top_slugs)
        treatments = self._collect_treatments(top_slugs)
        products = self._collect_products(top_slugs, category)

        red_flags = self.grounder.red_flag_symptoms(category, symptoms)
        # gabungkan sinyal KB + hard-rule kontraindikasi spesies (safety.py)
        safety = self.grounder.safety_signals(category, top_slugs)
        if category:
            for w in collect_safety_warnings(category):
                if w not in safety:
                    safety.append(w)
        # naikkan ke depan bila produk yang disarankan kena flag kontraindikasi
        for p in products:
            if p.safety_flag and p.safety_flag not in safety:
                safety.insert(0, p.safety_flag)
        is_emergency = any(d.is_emergency for d in diseases) or bool(red_flags)

        suggestion = AISuggestion(
            suggestion_type="symptom_to_disease",
            suggested_diseases=diseases,
            suggested_diagnostics=diagnostics,
            suggested_treatments=treatments,
            suggested_products=products,
            red_flags=red_flags,
            safety_warnings=safety,
            is_emergency=is_emergency,
            references=self._references(top_slugs),
        )

        # 3) augmentasi LLM (opsional)
        self._augment_with_llm(context, intake, suggestion)
        if not suggestion.summary:
            suggestion.summary = self._rule_based_summary(intake, suggestion)
        if not suggestion.follow_up_questions:
            suggestion.follow_up_questions = self._default_follow_ups(intake)
        return suggestion

    # ---- prediksi ML ------------------------------------------------------
    def _ml_predict(
        self, category: str | None, symptoms: list[str], top_k: int
    ) -> dict[str, float]:
        if not category or not symptoms:
            return {}
        try:
            from ..ml.predict import predict_diseases

            preds = predict_diseases(category, symptoms, top_k=top_k)
            return {p["disease_slug"]: float(p["confidence"]) for p in preds}
        except FileNotFoundError:
            logger.info("Model ML '%s' belum dilatih; pakai grounding KB saja.", category)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Prediksi ML gagal: %s", exc)
        return {}

    # ---- ensemble ML + KB -------------------------------------------------
    def _ensemble(
        self,
        ml_scores: dict[str, float],
        kb_candidates: list[DiseaseCandidate],
        top_k: int,
    ) -> list[SuggestedDisease]:
        kb_by_slug = {c.slug: c for c in kb_candidates}
        kb_max = max((c.score for c in kb_candidates), default=0.0) or 1.0

        merged: dict[str, dict] = {}
        for slug, conf in ml_scores.items():
            merged[slug] = {"ml": conf, "kb": 0.0}
        for c in kb_candidates:
            merged.setdefault(c.slug, {"ml": 0.0, "kb": 0.0})
            merged[c.slug]["kb"] = c.score / kb_max

        out: list[SuggestedDisease] = []
        for slug, parts in merged.items():
            cand = kb_by_slug.get(slug)
            disease = self.kb.disease_by_slug(slug) or {}
            # bobot: ML 0.6, grounding KB 0.4 (KB memberi recall saat ML kosong)
            has_ml = bool(ml_scores)
            conf = (0.6 * parts["ml"] + 0.4 * parts["kb"]) if has_ml else parts["kb"]
            sources = []
            if parts["ml"] > 0:
                sources.append("ml")
            if parts["kb"] > 0:
                sources.append("knowledge_base")
            matched = cand.matched_symptoms if cand else []
            rationale = (
                f"Cocok dengan gejala: {', '.join(matched)}" if matched else None
            )
            out.append(SuggestedDisease(
                disease_slug=slug,
                name_id=disease.get("name_id"),
                confidence=round(min(conf, 1.0), 4),
                rationale=rationale,
                is_emergency=bool(disease.get("is_emergency", False)),
                source="+".join(sources) or "ml",
            ))
        out.sort(key=lambda d: (d.is_emergency, d.confidence), reverse=True)
        return out[:top_k]

    # ---- pengumpulan struktur klinis -------------------------------------
    def _collect_diagnostics(self, slugs: list[str]) -> list[SuggestedDiagnostic]:
        seen, out = set(), []
        for slug in slugs:
            for d in self.grounder.diagnostics_for(slug):
                key = (d.get("name"), slug)
                if key in seen:
                    continue
                seen.add(key)
                out.append(SuggestedDiagnostic(
                    name=d.get("name", ""), type=d.get("type"),
                    step_order=d.get("step_order"),
                    is_gold_standard=bool(d.get("is_gold_standard", False)),
                    expected_finding=d.get("expected_finding"),
                    for_disease=slug,
                ))
        return out

    def _collect_treatments(self, slugs: list[str]) -> list[SuggestedTreatment]:
        seen, out = set(), []
        for slug in slugs:
            for t in self.grounder.treatments_for(slug):
                key = (t.get("name"), slug)
                if key in seen:
                    continue
                seen.add(key)
                out.append(SuggestedTreatment(
                    name=t.get("name", ""), type=t.get("type"),
                    line_of_therapy=t.get("line_of_therapy"),
                    procedure_steps=t.get("procedure_steps"),
                    recommendation=t.get("recommendation"),
                    for_disease=slug,
                ))
        return out

    def _collect_products(
        self, slugs: list[str], category: str | None = None
    ) -> list[SuggestedProduct]:
        seen, out = set(), []
        for slug in slugs:
            for p in self.grounder.products_for(slug):
                name = p.get("name", "")
                if name in seen:
                    continue
                seen.add(name)
                ingredient = p.get("active_ingredient")
                safety_flag = (
                    check_product_safety(category, ingredient) if category else None
                )
                out.append(SuggestedProduct(
                    name=name, kind=p.get("kind"),
                    active_ingredient=ingredient,
                    route=p.get("route"), dosage_guide=p.get("dosage_guide"),
                    cautions=p.get("cautions"),
                    safety_flag=safety_flag,
                ))
        return out

    def _references(self, slugs: list[str]) -> list[dict]:
        refs = []
        for slug in slugs:
            d = self.kb.disease_by_slug(slug) or {}
            refs.append({
                "type": "disease",
                "slug": slug,
                "name_id": d.get("name_id"),
                "overview": d.get("overview"),
            })
        return refs

    # ---- ringkasan rule-based (fallback tanpa LLM) ------------------------
    def _rule_based_summary(self, intake: IntakeResult, s: AISuggestion) -> str:
        if not s.suggested_diseases:
            return (
                "Belum ada gejala yang dikenali dari input. Mohon perjelas keluhan "
                "(durasi, bagian tubuh, perubahan perilaku) atau lampirkan foto/suara."
            )
        top = s.suggested_diseases[0]
        parts = [
            f"Berdasarkan {len(intake.symptoms)} gejala terdeteksi, kemungkinan "
            f"teratas: {top.name_id or top.disease_slug} "
            f"(keyakinan {round(top.confidence * 100)}%)."
        ]
        if s.is_emergency:
            parts.append("PERHATIAN: terdapat indikasi DARURAT — prioritaskan stabilisasi.")
        if s.suggested_diagnostics:
            gold = [d.name for d in s.suggested_diagnostics if d.is_gold_standard]
            if gold:
                parts.append(f"Pemeriksaan utama yang disarankan: {gold[0]}.")
        return " ".join(parts)

    def _default_follow_ups(self, intake: IntakeResult) -> list[str]:
        return [
            "Sudah berapa lama gejala ini berlangsung?",
            "Apakah nafsu makan & minum berubah?",
            "Apakah ada perubahan pada urin/feses?",
            "Adakah riwayat vaksinasi & pengobatan terakhir?",
        ]

    # ---- augmentasi LLM (opsional, mode smart hemat token) ----------------
    def _should_augment_with_llm(
        self, context: ConsultationContext, intake: IntakeResult, suggestion: AISuggestion
    ) -> tuple[bool, str | None]:
        mode = (AISettings().augmentation_mode or "smart").lower()
        if mode == "never":
            return False, "mode_never"
        chain = get_provider_registry().get_chain()
        if not chain and not self.llm.available:
            return False, "llm_unavailable"
        if mode == "always":
            ok, reason = self.llm.telemetry.can_spend(AISettings().max_tokens)
            return ok, reason

        # smart: hemat token — lewati LLM bila rule-based sudah cukup
        if not intake.symptoms:
            return False, "no_symptoms"
        top = suggestion.suggested_diseases[0] if suggestion.suggested_diseases else None
        threshold = AISettings().skip_llm_confidence
        if top and top.confidence >= threshold and not suggestion.is_emergency:
            return False, f"confidence_{top.confidence:.2f}_gte_{threshold}"
        if top and top.confidence >= 0.65 and len(intake.symptoms) >= 4:
            return False, "enough_symptoms_high_confidence"
        ok, reason = self.llm.telemetry.can_spend(AISettings().max_tokens)
        if not ok:
            return False, reason
        return True, None

    def _augment_with_llm(
        self,
        context: ConsultationContext,
        intake: IntakeResult,
        suggestion: AISuggestion,
    ) -> None:
        should, skip_reason = self._should_augment_with_llm(context, intake, suggestion)
        if not should:
            if skip_reason and skip_reason not in ("llm_unavailable", "mode_never"):
                self.llm.telemetry.record_skip(
                    "augmentation", skip_reason,
                    provider=self.llm.provider, model=self.llm.model,
                    org_id=context.org_id,
                )
            return

        # grounding ringkas — kurangi token input
        grounding = {
            "penyakit": [
                {"slug": d.disease_slug, "name": d.name_id, "conf": d.confidence,
                 "emergency": d.is_emergency}
                for d in suggestion.suggested_diseases[:3]
            ],
            "diagnosa": [d.name for d in suggestion.suggested_diagnostics[:5]],
            "tindakan": [t.name for t in suggestion.suggested_treatments[:5]],
            "red_flags": suggestion.red_flags[:5],
        }
        system = (
            "Asisten klinis vet Sobatpaws. Ringkas HANYA dari grounding. "
            "JSON: {\"summary\": str (max 3 kalimat), \"follow_up_questions\": [str max 4], "
            "\"prioritized_disease_slugs\": [str]}"
        )
        user = (
            f"{context.category_slug}|ras:{context.breed_slug}|umur:{context.age_years}|"
            f"bb:{context.weight_kg}\n"
            f"Keluhan:{intake.complaint_text[:400]}\n"
            f"Gejala:{intake.symptom_name_ids()[:12]}\n"
            f"Ground:{json.dumps(grounding, ensure_ascii=False)}"
        )
        data = self._chat_with_fallback(
            system, user,
            max_tokens=min(AISettings().max_tokens, 600),
            operation="augmentation",
            org_id=context.org_id,
        )
        if not data:
            return
        if isinstance(data.get("summary"), str):
            suggestion.summary = data["summary"].strip()
        fu = data.get("follow_up_questions")
        if isinstance(fu, list):
            suggestion.follow_up_questions = [str(q) for q in fu][:6]
        # re-order kandidat sesuai prioritas LLM (tetap dalam himpunan grounding)
        order = data.get("prioritized_disease_slugs")
        if isinstance(order, list) and order:
            rank = {slug: i for i, slug in enumerate(order)}
            suggestion.suggested_diseases.sort(
                key=lambda d: rank.get(d.disease_slug, 999)
            )
        suggestion.generated_by = "llm_augmented"

    def _chat_with_fallback(
        self,
        system: str,
        user: str,
        *,
        max_tokens: int,
        operation: str,
        org_id: int | None = None,
    ) -> dict | None:
        """Panggil LLM dengan fallback chain (Anthropic → OpenAI → lokal)."""
        for prov in get_provider_registry().get_chain():
            client = LLMClient.for_provider(prov)
            if not client.available:
                continue
            data = client.chat_json(
                system, user, max_tokens=max_tokens,
                operation=operation, org_id=org_id,
            )
            if data:
                return data
        return None
