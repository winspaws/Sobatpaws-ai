"""API pengelolaan agent AI — provider, saran, chat, usage."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from ..ai.agent_manager import get_agent_manager
from ..ai.provider_connector import connection_status, test_all_providers, test_provider
from ..ai.schemas import (
    AgentChatRequest,
    AgentChatResponse,
    DoctorInput,
    ProviderUpsertRequest,
    SuggestionFeedback,
    SuggestionReviewRequest,
)
from .auth import require_admin, require_vet

router = APIRouter(prefix="/api/agent", tags=["AI Agent"])


@router.get("/providers/status")
def providers_status() -> dict:
    """Status konfigurasi provider eksternal (Anthropic, OpenAI, lokal) — tanpa live ping."""
    mgr = get_agent_manager()
    return connection_status(mgr.registry)


@router.post("/providers/test", dependencies=[Depends(require_admin)])
def test_providers(provider_id: str | None = Query(None)) -> dict:
    """Uji koneksi live ke provider AI eksternal (mis. Anthropic Claude).

    Query `provider_id=anthropic` untuk satu provider, atau kosong untuk semua.
    """
    mgr = get_agent_manager()
    ids = [provider_id] if provider_id else None
    return test_all_providers(mgr.registry, provider_ids=ids)


@router.post("/providers/{provider_id}/test", dependencies=[Depends(require_admin)])
def test_one_provider(provider_id: str) -> dict:
    """Uji koneksi live ke satu provider (contoh: anthropic → Claude API)."""
    mgr = get_agent_manager()
    cfg = mgr.registry.get(provider_id)
    if not cfg:
        raise HTTPException(404, f"Provider '{provider_id}' tidak ditemukan.")
    return test_provider(cfg)


@router.get("/providers")
def list_providers() -> dict:
    """Daftar provider LLM (OpenAI, Anthropic, lokal, custom)."""
    mgr = get_agent_manager()
    return {"providers": mgr.registry.list_providers(active_only=False)}


@router.post("/providers/{provider_id}/activate", dependencies=[Depends(require_admin)])
def activate_provider(provider_id: str) -> dict:
    mgr = get_agent_manager()
    p = mgr.registry.set_primary(provider_id)
    if not p:
        raise HTTPException(404, f"Provider '{provider_id}' tidak ditemukan.")
    return {"status": "ok", "primary": provider_id, "available": p.available()}


@router.post("/providers", dependencies=[Depends(require_admin)])
def upsert_provider(req: ProviderUpsertRequest) -> dict:
    mgr = get_agent_manager()
    p = mgr.registry.upsert(req.model_dump())
    return {"status": "ok", "provider": mgr.registry.list_providers()}


@router.get("/usage")
def agent_usage() -> dict:
    return get_agent_manager().usage_summary()


@router.get("/conversations", dependencies=[Depends(require_vet)])
def list_conversations(limit: int = 30) -> dict:
    rows = get_agent_manager().list_conversations(limit=limit)
    return {"count": len(rows), "conversations": rows}


@router.get("/conversations/{consultation_id}", dependencies=[Depends(require_vet)])
def get_conversation(consultation_id: str) -> dict:
    detail = get_agent_manager().get_session_detail(consultation_id)
    if not detail:
        raise HTTPException(404, "Konsultasi tidak ditemukan.")
    return detail


@router.get("/suggestions", dependencies=[Depends(require_vet)])
def list_suggestions(
    consultation_id: str | None = None,
    reviewed: bool | None = None,
    limit: int = 50,
) -> dict:
    rows = get_agent_manager().list_suggestions(consultation_id, reviewed, limit)
    return {"count": len(rows), "suggestions": rows}


@router.post("/suggestions/{suggestion_id}/review", dependencies=[Depends(require_vet)])
def review_suggestion(suggestion_id: str, req: SuggestionReviewRequest) -> dict:
    rec = get_agent_manager().review_suggestion(suggestion_id, req.note)
    if not rec:
        raise HTTPException(404, "Saran tidak ditemukan.")
    return {"status": "reviewed", "suggestion_id": suggestion_id}


@router.post(
    "/conversations/{consultation_id}/chat",
    response_model=AgentChatResponse,
    dependencies=[Depends(require_vet)],
)
def agent_chat(consultation_id: str, req: AgentChatRequest) -> AgentChatResponse:
    """Chat interaktif dengan agent (konteks klinis ringkas, hemat token)."""
    mgr = get_agent_manager()
    try:
        out = mgr.agent_chat(consultation_id, req.message, req.provider_id)
    except KeyError as exc:
        raise HTTPException(404, str(exc)) from exc
    return AgentChatResponse(**out)


class FullDoctorInputBody(DoctorInput):
    """DoctorInput dengan field lengkap untuk API."""


@router.post("/conversations/{consultation_id}/doctor-input", dependencies=[Depends(require_vet)])
def agent_doctor_input(consultation_id: str, payload: DoctorInput) -> dict:
    """Simpan input dokter lengkap (diagnosa, gejala, tindakan, produk, outcome)."""
    payload.consultation_id = consultation_id
    return get_agent_manager().record_doctor_input(payload)


@router.post("/conversations/{consultation_id}/feedback", dependencies=[Depends(require_vet)])
def agent_feedback(consultation_id: str, payload: SuggestionFeedback) -> dict:
    payload.consultation_id = consultation_id
    return get_agent_manager().record_feedback(payload)


class VetInputForm(BaseModel):
    """Form input dokter dari UI (field lengkap)."""

    vet_id: int | None = None
    confirmed_disease_slug: str | None = None
    differential_disease_slugs: list[str] = Field(default_factory=list)
    confirmed_symptoms: list[str] = Field(default_factory=list)
    diagnostics_ordered: list[str] = Field(default_factory=list)
    treatments_given: list[str] = Field(default_factory=list)
    products_prescribed: list[str] = Field(default_factory=list)
    clinical_notes: str | None = None
    outcome: str | None = None
    confidence: float | None = Field(None, ge=0, le=100)
    suggestion_ref: str | None = None
    verdict: str | None = Field(None, description="opsional: feedback sekaligus")
    corrected_disease_slug: str | None = None
    comment: str | None = None


@router.post("/conversations/{consultation_id}/vet-record", dependencies=[Depends(require_vet)])
def vet_full_record(consultation_id: str, form: VetInputForm) -> dict:
    """Satu endpoint: input klinis dokter + feedback opsional."""
    mgr = get_agent_manager()
    doc = DoctorInput(
        consultation_id=consultation_id,
        vet_id=form.vet_id,
        confirmed_disease_slug=form.confirmed_disease_slug,
        differential_disease_slugs=form.differential_disease_slugs,
        confirmed_symptoms=form.confirmed_symptoms,
        diagnostics_ordered=form.diagnostics_ordered,
        treatments_given=form.treatments_given,
        products_prescribed=form.products_prescribed,
        clinical_notes=form.clinical_notes,
        outcome=form.outcome,
        confidence=form.confidence,
    )
    out = mgr.record_doctor_input(doc)
    if form.verdict:
        fb = SuggestionFeedback(
            consultation_id=consultation_id,
            suggestion_ref=form.suggestion_ref,
            verdict=form.verdict,
            corrected_disease_slug=form.corrected_disease_slug,
            comment=form.comment,
            reviewer_id=form.vet_id,
        )
        out["feedback"] = mgr.record_feedback(fb)
    return out
