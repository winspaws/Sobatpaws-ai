"""Orkestrator sesi konsultasi — perekat seluruh komponen AI Sobatpaws.

Siklus hidup satu konsultasi (chat / video):
1. start(context, intake)         -> proses keluhan pertama + saran awal
2. add_turn(id, intake)           -> giliran berikutnya, saran diperbarui
3. record_doctor_input(id, input) -> simpan keputusan dokter (bahan pembelajaran)
4. record_feedback(id, feedback)  -> penilaian dokter atas saran AI

Semua langkah otomatis dicatat ke LearningStore. State sesi disimpan in-memory
(untuk produksi: ganti dengan tabel ai_conversations / Redis).
"""
from __future__ import annotations

from dataclasses import dataclass, field

from ..data_loader import KnowledgeBase, load_knowledge_base
from .intake import IntakeProcessor
from .learning_store import LearningStore, get_store
from .llm import LLMClient
from .schemas import (
    AISuggestion,
    ConsultationContext,
    DoctorInput,
    IntakePayload,
    IntakeResult,
    SuggestionFeedback,
)
from ..integration.identity import (
    entities_from_context,
    get_identity_registry,
    new_consultation_id,
    normalize_context,
)


@dataclass
class ConsultationState:
    consultation_id: str
    context: ConsultationContext
    intakes: list[IntakeResult] = field(default_factory=list)
    suggestions: list[AISuggestion] = field(default_factory=list)
    accumulated_symptoms: dict[str, dict] = field(default_factory=dict)


@dataclass
class ConsultationResult:
    consultation_id: str
    intake: IntakeResult
    suggestion: AISuggestion


class ConsultationService:
    """Service tingkat aplikasi untuk mengelola konsultasi."""

    def __init__(
        self,
        kb: KnowledgeBase | None = None,
        store: LearningStore | None = None,
        llm: LLMClient | None = None,
    ):
        self.kb = kb or load_knowledge_base()
        self.store = store or get_store()
        self.llm = llm or LLMClient()
        self.engine = SuggestionEngine(self.kb, llm=self.llm)
        self._sessions: dict[str, ConsultationState] = {}

    # ---- mulai konsultasi -------------------------------------------------
    def start(
        self,
        context: ConsultationContext,
        payload: IntakePayload,
        consultation_id: str | None = None,
    ) -> ConsultationResult:
        context = normalize_context(context)
        cid = new_consultation_id(
            consultation_id or context.external_consultation_id,
            context.external_consultation_id,
        )
        if cid in self._sessions:
            raise ValueError(f"Konsultasi '{cid}' sudah ada — gunakan add_turn.")
        payload.is_first_contact = True
        state = ConsultationState(consultation_id=cid, context=context)
        self._sessions[cid] = state
        entities = entities_from_context(context, consultation_id=cid)
        get_identity_registry().register(
            cid, entities, context_snapshot=context.model_dump(mode="json"),
        )
        self.store.record_consultation_start(cid, context)
        return self._run_turn(state, payload)

    # ---- giliran lanjutan -------------------------------------------------
    def add_turn(
        self, consultation_id: str, payload: IntakePayload
    ) -> ConsultationResult:
        state = self._sessions.get(consultation_id)
        if state is None:
            raise KeyError(f"Konsultasi '{consultation_id}' tidak ditemukan.")
        return self._run_turn(state, payload)

    def _run_turn(
        self, state: ConsultationState, payload: IntakePayload
    ) -> ConsultationResult:
        processor = IntakeProcessor(
            self.kb, category_slug=state.context.category_slug, llm=self.llm
        )
        intake = processor.process(payload)

        # akumulasi gejala lintas giliran (ambil skor tertinggi)
        for s in intake.symptoms:
            prev = state.accumulated_symptoms.get(s.name_id)
            if not prev or s.score > prev.get("score", 0):
                state.accumulated_symptoms[s.name_id] = s.model_dump()

        # gabungkan gejala kumulatif ke intake untuk konteks saran yang utuh
        merged_intake = self._merge_accumulated(state, intake)

        suggestion = self.engine.suggest(state.context, merged_intake)

        state.intakes.append(intake)
        state.suggestions.append(suggestion)
        self.store.record_intake(state.consultation_id, intake)
        self.store.record_suggestion(state.consultation_id, suggestion)

        return ConsultationResult(
            consultation_id=state.consultation_id,
            intake=merged_intake,
            suggestion=suggestion,
        )

    def _merge_accumulated(
        self, state: ConsultationState, latest: IntakeResult
    ) -> IntakeResult:
        from .schemas import ExtractedSymptom

        symptoms = [ExtractedSymptom(**v) for v in state.accumulated_symptoms.values()]
        symptoms.sort(key=lambda s: s.score, reverse=True)
        return IntakeResult(
            complaint_text=latest.complaint_text,
            observations=latest.observations,
            symptoms=symptoms,
            channel=latest.channel,
        )

    # ---- input dokter & feedback (bahan pembelajaran) ---------------------
    def record_doctor_input(self, doctor_input: DoctorInput) -> dict:
        return self.store.record_doctor_input(doctor_input)

    def record_feedback(self, feedback: SuggestionFeedback) -> dict:
        return self.store.record_feedback(feedback)

    # ---- util -------------------------------------------------------------
    def get_state(self, consultation_id: str) -> ConsultationState | None:
        state = self._sessions.get(consultation_id)
        if state:
            return state
        return self._hydrate_session(consultation_id)

    def _hydrate_session(self, consultation_id: str) -> ConsultationState | None:
        """Pulihkan sesi minimal dari registry + learning store (setelah restart)."""
        reg = get_identity_registry().get(consultation_id)
        if not reg:
            return None
        snap = reg.get("context_snapshot") or {}
        if not snap:
            for row in self.store._read("consultation"):
                if row.get("consultation_id") == consultation_id:
                    snap = row.get("context") or {}
                    break
        if not snap:
            return None
        ctx = ConsultationContext(**snap)
        state = ConsultationState(consultation_id=consultation_id, context=ctx)
        for row in self.store._read("intake"):
            if row.get("consultation_id") != consultation_id:
                continue
            for s in row.get("symptoms", []):
                nid = s.get("name_id")
                if nid:
                    state.accumulated_symptoms[nid] = s
        self._sessions[consultation_id] = state
        return state


if __name__ == "__main__":
    svc = ConsultationService()
    ctx = ConsultationContext(category_slug="cat", breed_slug="cat-persian", age_years=6)
    payload = IntakePayload(
        text="Kucing saya mengejan saat pipis, ada darah, lemas dan tidak mau makan",
        channel="chat",
    )
    res = svc.start(ctx, payload)
    print("Consultation:", res.consultation_id)
    print("Gejala:", res.intake.symptom_name_ids())
    print("Ringkasan:", res.suggestion.summary)
    for d in res.suggestion.suggested_diseases:
        print(f"  - {d.name_id or d.disease_slug}: {d.confidence} [{d.source}]")
    print("Darurat:", res.suggestion.is_emergency, "| Red flags:", res.suggestion.red_flags)
