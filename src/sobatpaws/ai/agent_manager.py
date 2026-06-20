"""Orkestrator agent AI — interaksi, saran, input dokter, hemat token, multi-provider."""
from __future__ import annotations

import logging
from typing import Any

from ..config import AISettings
from ..integration.identity import entities_from_context, get_identity_registry, normalize_context
from .agent_store import AgentStore, get_agent_store
from .consultation import ConsultationService, ConsultationResult
from .llm import LLMClient
from .providers import get_provider_registry
from .schemas import (
    AISuggestion,
    ConsultationContext,
    DoctorInput,
    IntakePayload,
    SuggestionFeedback,
)

logger = logging.getLogger("sobatpaws.ai.agent")


class AgentManager:
    """Lapisan manajemen agent di atas ConsultationService + AgentStore."""

    def __init__(
        self,
        consultation_service: ConsultationService | None = None,
        store: AgentStore | None = None,
        llm: LLMClient | None = None,
    ):
        self.svc = consultation_service or ConsultationService()
        self.store = store or get_agent_store()
        self.llm = llm or LLMClient()
        self.registry = get_provider_registry()

    # ---- konsultasi klinis (ML + KB + LLM opsional) -----------------------
    def start(
        self,
        context: ConsultationContext,
        payload: IntakePayload,
        consultation_id: str | None = None,
    ) -> dict[str, Any]:
        context = normalize_context(context)
        result = self.svc.start(context, payload, consultation_id=consultation_id)
        self.store.create_conversation(result.consultation_id, context)
        sug_rec = self._persist_turn(result, context)
        return self._wrap_result(result, sug_rec, context)

    def add_turn(
        self, consultation_id: str, payload: IntakePayload,
    ) -> dict[str, Any]:
        result = self.svc.add_turn(consultation_id, payload)
        state = self.svc.get_state(consultation_id)
        ctx = state.context if state else ConsultationContext()
        sug_rec = self._persist_turn(result, ctx)
        return self._wrap_result(result, sug_rec, ctx)

    def _persist_turn(
        self, result: ConsultationResult, context: ConsultationContext,
    ) -> dict[str, Any]:
        sug_rec = self.store.save_suggestion(
            result.consultation_id,
            result.suggestion,
            case_id=context.case_id,
            pet_id=context.pet_id,
        )
        if result.intake.complaint_text:
            self.store.add_message(
                result.consultation_id, "user", result.intake.complaint_text,
                {"channel": result.intake.channel.value},
            )
        self.store.add_message(
            result.consultation_id, "assistant",
            result.suggestion.summary or "Saran klinis diperbarui.",
            {"type": "suggestion", "suggestion_id": sug_rec["id"]},
        )
        return sug_rec

    def _wrap_result(
        self,
        result: ConsultationResult,
        sug_rec: dict,
        context: ConsultationContext | None = None,
    ) -> dict[str, Any]:
        ctx = context
        if ctx is None:
            state = self.svc.get_state(result.consultation_id)
            ctx = state.context if state else ConsultationContext()
        entities = entities_from_context(ctx, consultation_id=result.consultation_id)
        return {
            "consultation_id": result.consultation_id,
            "intake": result.intake,
            "suggestion": result.suggestion,
            "suggestion_id": sug_rec["id"],
            "suggestion_ref": sug_rec["id"],
            "entities": entities.to_public_dict(),
        }

    # ---- chat agent interaktif (hemat token) --------------------------------
    def agent_chat(
        self,
        consultation_id: str,
        message: str,
        provider_id: str | None = None,
    ) -> dict[str, Any]:
        state = self.svc.get_state(consultation_id)
        if state is None:
            raise KeyError(f"Konsultasi '{consultation_id}' tidak ditemukan.")

        self.store.add_message(consultation_id, "user", message)

        # Konteks ringkas: gejala + top penyakit + 4 pesan terakhir
        symptoms = list(state.accumulated_symptoms.keys())[:12]
        last_sug = state.suggestions[-1] if state.suggestions else None
        top_diseases = []
        if last_sug:
            for d in last_sug.suggested_diseases[:3]:
                top_diseases.append(
                    f"{d.name_id or d.disease_slug} ({round(d.confidence * 100)}%)"
                )

        history = self.store.list_messages(consultation_id, limit=6)
        history_txt = "\n".join(
            f"{m['role']}: {m['content'][:200]}"
            for m in history[-4:]
        )

        system = (
            "Asisten klinis vet Sobatpaws. Jawab singkat Bahasa Indonesia, "
            "maks 4 kalimat. Berikan saran tindak lanjut & pertanyaan klinis. "
            "Tidak menggantikan pemeriksaan dokter. JSON: "
            "{\"reply\": str, \"follow_up_questions\": [str max 3], "
            "\"action_hint\": str|null}"
        )
        user = (
            f"Spesies:{state.context.category_slug}|Ras:{state.context.breed_slug}\n"
            f"Gejala:{symptoms}\nTop dx:{top_diseases}\n"
            f"Riwayat singkat:\n{history_txt}\n\nPesan dokter: {message[:500]}"
        )

        data, req_rec = self._llm_with_fallback(
            system, user, operation="agent_chat",
            consultation_id=consultation_id,
            org_id=state.context.org_id,
            provider_id=provider_id,
            max_tokens=min(AISettings().max_tokens, 500),
        )

        reply = "Maaf, agent tidak tersedia. Gunakan saran ML/KB di panel."
        follow_ups: list[str] = []
        action_hint = None
        if data:
            reply = str(data.get("reply", reply))
            fu = data.get("follow_up_questions")
            if isinstance(fu, list):
                follow_ups = [str(q) for q in fu][:3]
            action_hint = data.get("action_hint")

        self.store.add_message(
            consultation_id, "assistant", reply,
            {"type": "agent_chat", "follow_ups": follow_ups},
        )

        return {
            "consultation_id": consultation_id,
            "reply": reply,
            "follow_up_questions": follow_ups,
            "action_hint": action_hint,
            "request_id": req_rec.get("id") if req_rec else None,
            "provider_used": req_rec.get("provider_id") if req_rec else None,
        }

    def _llm_with_fallback(
        self,
        system: str,
        user: str,
        operation: str,
        consultation_id: str,
        org_id: int | None = None,
        provider_id: str | None = None,
        max_tokens: int | None = None,
    ) -> tuple[dict | None, dict | None]:
        chain = self.registry.get_chain()
        if provider_id:
            p = self.registry.get(provider_id)
            chain = [p] if p and p.available() else chain

        for prov in chain:
            client = LLMClient.for_provider(prov)
            if not client.available:
                continue
            data = client.chat_json(
                system, user, max_tokens=max_tokens,
                operation=operation, consultation_id=consultation_id,
                org_id=org_id,
            )
            req_rec = self.store.log_request(
                consultation_id,
                provider_id=prov.id,
                model=client.model,
                operation=operation,
                status="completed" if data else "failed",
                prompt_tokens=0,
                completion_tokens=0,
            )
            if data:
                return data, req_rec
        return None, None

    # ---- input dokter & feedback --------------------------------------------
    def record_doctor_input(self, doctor_input: DoctorInput) -> dict:
        state = self.svc.get_state(doctor_input.consultation_id)
        if state:
            ctx = state.context
            doctor_input.vet_id = doctor_input.vet_id or ctx.vet_id
            doctor_input.org_id = doctor_input.org_id or ctx.org_id
            doctor_input.owner_id = doctor_input.owner_id or ctx.owner_id
            doctor_input.customer_id = doctor_input.customer_id or ctx.customer_id
            doctor_input.pet_id = doctor_input.pet_id or ctx.pet_id
            doctor_input.case_id = doctor_input.case_id or ctx.case_id
            doctor_input.external_consultation_id = (
                doctor_input.external_consultation_id or ctx.external_consultation_id
            )
        rec = self.svc.record_doctor_input(doctor_input)
        agent_rec = self.store.save_doctor_input(doctor_input)
        state = self.svc.get_state(doctor_input.consultation_id)
        if state and doctor_input.clinical_notes:
            self.store.add_message(
                doctor_input.consultation_id, "vet",
                doctor_input.clinical_notes,
                {
                    "confirmed_disease": doctor_input.confirmed_disease_slug,
                    "vet_id": doctor_input.vet_id,
                },
            )
        return {"learning_id": rec.get("id"), "agent_id": agent_rec["id"]}

    def record_feedback(self, feedback: SuggestionFeedback) -> dict:
        state = self.svc.get_state(feedback.consultation_id)
        sug_id = feedback.suggestion_ref
        if not sug_id and state and state.suggestions:
            latest = self.store.list_suggestions(feedback.consultation_id, limit=1)
            if latest:
                sug_id = latest[0]["id"]
        rec = self.svc.record_feedback(feedback)
        agent_rec = self.store.save_feedback(feedback, ai_suggestion_id=sug_id)
        if sug_id and feedback.verdict:
            self.store.review_suggestion(sug_id, reviewed=True, note=feedback.comment)
        return {"learning_id": rec.get("id"), "agent_id": agent_rec["id"]}

    # ---- pengelolaan saran --------------------------------------------------
    def list_suggestions(
        self, consultation_id: str | None = None, reviewed: bool | None = None,
        limit: int = 50,
    ) -> list[dict]:
        return self.store.list_suggestions(consultation_id, reviewed, limit)

    def review_suggestion(
        self, suggestion_id: str, note: str | None = None,
    ) -> dict | None:
        return self.store.review_suggestion(suggestion_id, reviewed=True, note=note)

    def get_session_detail(self, consultation_id: str) -> dict | None:
        state = self.svc.get_state(consultation_id)
        conv = self.store.get_conversation(consultation_id)
        reg = get_identity_registry().get(consultation_id)
        if not state and not conv and not reg:
            return None
        ctx_data = (
            state.context.model_dump(mode="json") if state
            else (conv or {}).get("context") or (reg or {}).get("context_snapshot")
        )
        ctx = ConsultationContext(**ctx_data) if ctx_data else ConsultationContext()
        entities = entities_from_context(ctx, consultation_id=consultation_id)
        suggestions = self.store.list_suggestions(consultation_id, limit=20)
        messages = self.store.list_messages(consultation_id)
        return {
            "consultation_id": consultation_id,
            "entities": entities.to_public_dict(),
            "conversation": conv,
            "context": ctx_data,
            "suggestion_count": len(state.suggestions) if state else len(suggestions),
            "symptoms": list(state.accumulated_symptoms.values()) if state else [],
            "suggestions": suggestions,
            "messages": messages,
            "latest_suggestion": (
                state.suggestions[-1].model_dump(mode="json")
                if state and state.suggestions else None
            ),
        }

    def find_sessions(
        self,
        *,
        vet_id: int | None = None,
        owner_id: int | None = None,
        customer_id: int | None = None,
        pet_id: int | None = None,
        org_id: int | None = None,
        limit: int = 50,
    ) -> list[dict]:
        return get_identity_registry().list_by_filter(
            vet_id=vet_id,
            owner_id=owner_id,
            customer_id=customer_id,
            pet_id=pet_id,
            org_id=org_id,
            limit=limit,
        )

    def list_conversations(self, limit: int = 30) -> list[dict]:
        return self.store.list_conversations(limit)

    def usage_summary(self) -> dict:
        from .telemetry import get_telemetry

        return {
            "store": self.store.stats(),
            "telemetry": get_telemetry().summary(limit_recent=20),
            "providers": self.registry.list_providers(),
            "backend": self.store.backend_info(),
        }


_agent: AgentManager | None = None


def get_agent_manager() -> AgentManager:
    global _agent
    if _agent is None:
        _agent = AgentManager()
    return _agent
