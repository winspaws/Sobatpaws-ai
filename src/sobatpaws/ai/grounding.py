"""Grounding / retrieval knowledge base untuk konsultasi.

Memberi konteks faktual (penyakit, gejala, diagnosa, tindakan, produk, safety)
sehingga saran AI ter-anchor ke data Sobatpaws, bukan halusinasi LLM.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from ..data_loader import KnowledgeBase

FREQ_WEIGHT = {
    "very_high": 1.0, "high": 0.8, "moderate": 0.5, "low": 0.25, "very_low": 0.1,
    None: 0.5,
}


@dataclass
class DiseaseCandidate:
    """Kandidat penyakit hasil pencocokan gejala terhadap knowledge base."""

    slug: str
    name_id: str | None
    name: str | None
    score: float
    matched_symptoms: list[str] = field(default_factory=list)
    is_emergency: bool = False
    body_system: str | None = None
    raw: dict = field(default_factory=dict)


class KnowledgeGrounder:
    """Mesin retrieval ringan di atas KnowledgeBase."""

    def __init__(self, kb: KnowledgeBase):
        self.kb = kb

    # ---- pencocokan gejala -> penyakit ------------------------------------
    def rank_diseases_by_symptoms(
        self, category_slug: str | None, symptom_name_ids: list[str], top_k: int = 6
    ) -> list[DiseaseCandidate]:
        if not symptom_name_ids:
            return []
        target = set(symptom_name_ids)
        diseases = (
            self.kb.diseases_for_category(category_slug)
            if category_slug else self.kb.diseases
        )
        candidates: list[DiseaseCandidate] = []
        for d in diseases:
            score = 0.0
            matched: list[str] = []
            for s in d.get("symptoms", []):
                nid = s.get("name_id") or s.get("name")
                if nid in target:
                    w = FREQ_WEIGHT.get(s.get("frequency"), 0.5)
                    bonus = 0.5 if s.get("is_pathognomonic") else 0.0
                    score += w + bonus
                    matched.append(nid)
            if matched:
                candidates.append(DiseaseCandidate(
                    slug=d["slug"],
                    name_id=d.get("name_id"),
                    name=d.get("name"),
                    score=round(score, 3),
                    matched_symptoms=matched,
                    is_emergency=bool(d.get("is_emergency", False)),
                    body_system=d.get("body_system"),
                    raw=d,
                ))
        candidates.sort(key=lambda c: (c.is_emergency, c.score), reverse=True)
        return candidates[:top_k]

    def disease(self, slug: str) -> dict | None:
        return self.kb.disease_by_slug(slug)

    # ---- ekstraksi struktur klinis dari satu penyakit ---------------------
    def diagnostics_for(self, disease_slug: str) -> list[dict]:
        d = self.kb.disease_by_slug(disease_slug) or {}
        items = sorted(
            d.get("diagnostics", []),
            key=lambda x: (not x.get("is_gold_standard", False), x.get("step_order", 99)),
        )
        return [{**x, "for_disease": disease_slug} for x in items]

    def treatments_for(self, disease_slug: str) -> list[dict]:
        d = self.kb.disease_by_slug(disease_slug) or {}
        items = sorted(
            d.get("treatments", []), key=lambda x: x.get("line_of_therapy", 99)
        )
        return [{**x, "for_disease": disease_slug} for x in items]

    def products_for(self, disease_slug: str) -> list[dict]:
        d = self.kb.disease_by_slug(disease_slug) or {}
        products: list[dict] = []
        for t in d.get("treatments", []):
            for p in t.get("products", []):
                products.append(p)
        return products

    # ---- sinyal keselamatan ----------------------------------------------
    def safety_signals(
        self, category_slug: str | None, disease_slugs: list[str]
    ) -> list[str]:
        """Kumpulkan peringatan keselamatan (cautions produk + disclaimer spesies)."""
        warnings: list[str] = []
        # disclaimer level kategori (mis. kucing sensitif obat)
        if category_slug:
            for d in self.kb.diseases_for_category(category_slug):
                disc = d.get("_category_disclaimer")
                if disc and disc not in warnings:
                    warnings.append(disc)
                break
        for slug in disease_slugs:
            d = self.kb.disease_by_slug(slug) or {}
            for t in d.get("treatments", []):
                for p in t.get("products", []):
                    caution = p.get("cautions")
                    if caution and caution not in warnings:
                        warnings.append(f"{p.get('name', 'Produk')}: {caution}")
        return warnings

    def red_flag_symptoms(
        self, category_slug: str | None, symptom_name_ids: list[str]
    ) -> list[str]:
        target = set(symptom_name_ids)
        flags: list[str] = []
        diseases = (
            self.kb.diseases_for_category(category_slug)
            if category_slug else self.kb.diseases
        )
        for d in diseases:
            for s in d.get("symptoms", []):
                nid = s.get("name_id") or s.get("name")
                if nid in target and s.get("is_red_flag") and nid not in flags:
                    flags.append(nid)
        return flags

    def breed_context(self, breed_slug: str | None) -> dict:
        if not breed_slug:
            return {}
        breed = self.kb.breed_by_slug(breed_slug)
        if not breed:
            return {}
        susceptible = self.kb.diseases_for_breed(breed_slug)
        return {
            "breed": breed.get("name") or breed.get("name_id"),
            "size_class": breed.get("size_class"),
            "predisposed_diseases": [
                {"slug": d["slug"], "name_id": d.get("name_id"),
                 "risk": d.get("_risk"), "prevalence_pct": d.get("_prevalence_pct")}
                for d in susceptible
            ],
        }
