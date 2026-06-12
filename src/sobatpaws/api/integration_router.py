"""Endpoint integrasi untuk aplikasi vet (mobile/web klinik)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from ..config import AISettings, LEARNING_BACKEND
from ..ai.telemetry import get_telemetry
from ..integration.identity import (
    SobatpawsEntityIds,
    get_identity_registry,
    resolve_consultation_id,
)
from ..ai.agent_manager import get_agent_manager
from .auth import auth_status, optional_client, require_vet

router = APIRouter(prefix="/api/integration", tags=["Integrasi Vet App"])

ID_SCHEMA = {
    "description": "ID entitas Sobatpaws — kirim di context saat POST /consultations",
    "fields": {
        "org_id": {"type": "int", "db": "organizations.id", "required": False},
        "vet_id": {
            "type": "int",
            "db": "users.id",
            "aliases": ["user_id", "doctor_id"],
            "required": True,
            "note": "Dokter yang menangani konsultasi",
        },
        "owner_id": {
            "type": "int",
            "db": "pet_owners.id",
            "aliases": ["customer_id"],
            "required": True,
            "note": "Pelanggan/pemilik hewan",
        },
        "pet_id": {"type": "int", "db": "pets.id", "required": True},
        "case_id": {"type": "int", "db": "clinical_cases.id", "required": False},
        "external_consultation_id": {
            "type": "string",
            "note": "ID konsultasi dari app Sobatpaws utama — untuk lookup & sync",
        },
        "consultation_id": {
            "type": "string",
            "note": "ID sesi AI — bisa dikirim saat start atau di-generate server",
        },
        "external_refs": {
            "type": "object",
            "note": "Map ID tambahan: appointment_id, invoice_id, dll.",
        },
    },
    "response_field": "entities",
    "lookup_endpoints": [
        "GET /api/integration/entities/{consultation_id}",
        "GET /api/integration/consultations/by-external/{external_id}",
        "GET /api/integration/consultations?vet_id=&pet_id=&owner_id=",
    ],
}


@router.get("/id-schema")
def integration_id_schema() -> dict:
    """Kontrak ID entitas untuk tim developer Sobatpaws."""
    return ID_SCHEMA


@router.get("/entities/{consultation_id}", dependencies=[Depends(require_vet)])
def get_entities(consultation_id: str) -> dict:
    """Ambil bundle ID entitas untuk satu sesi konsultasi."""
    cid = resolve_consultation_id(consultation_id) or consultation_id
    reg = get_identity_registry().get(cid)
    if reg:
        entities = SobatpawsEntityIds(**{
            k: reg[k] for k in SobatpawsEntityIds.model_fields if k in reg
        })
        return {"consultation_id": cid, "entities": entities.to_public_dict(), "source": "registry"}
    detail = get_agent_manager().get_session_detail(cid)
    if not detail:
        raise HTTPException(404, "Konsultasi tidak ditemukan.")
    return {
        "consultation_id": cid,
        "entities": detail.get("entities"),
        "source": "session",
    }


@router.get("/consultations/by-external/{external_id}", dependencies=[Depends(require_vet)])
def get_by_external(external_id: str) -> dict:
    """Lookup sesi AI dari ID konsultasi app Sobatpaws utama."""
    cid = resolve_consultation_id(external_consultation_id=external_id)
    if not cid:
        raise HTTPException(404, f"Tidak ada sesi untuk external_id '{external_id}'.")
    detail = get_agent_manager().get_session_detail(cid)
    if not detail:
        reg = get_identity_registry().get(cid)
        return {
            "consultation_id": cid,
            "external_consultation_id": external_id,
            "entities": reg,
            "session_active": False,
        }
    return {**detail, "session_active": True}


@router.get("/consultations", dependencies=[Depends(require_vet)])
def list_consultations(
    vet_id: int | None = Query(None),
    owner_id: int | None = Query(None),
    customer_id: int | None = Query(None),
    pet_id: int | None = Query(None),
    org_id: int | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
) -> dict:
    """Daftar sesi AI terfilter by ID entitas Sobatpaws."""
    rows = get_agent_manager().find_sessions(
        vet_id=vet_id,
        owner_id=owner_id,
        customer_id=customer_id,
        pet_id=pet_id,
        org_id=org_id,
        limit=limit,
    )
    return {"count": len(rows), "consultations": rows}


@router.get("/manifest")
def integration_manifest(request: Request) -> dict:
    """Kontrak integrasi — dipakai app vet saat onboarding."""
    client = optional_client(request)
    base = str(request.base_url).rstrip("/")
    auth = auth_status()
    return {
        "platform": "Sobatpaws Veterinary ML & AI",
        "api_version": "0.3.0",
        "openapi_url": f"{base}/docs",
        "auth": auth,
        "client": client,
        "recommended_flow": [
            "1. GET /health — cek koneksi",
            "2. GET /api/integration/id-schema — kontrak ID entitas (vet, pelanggan, pet, ...)",
            "3. GET /categories + /categories/{slug}/breeds — muat master data",
            "4. POST /consultations — mulai sesi (context: org_id, vet_id, owner_id, pet_id, external_consultation_id)",
            "5. POST /consultations/{id}/turns — kirim teks tambahan",
            "6. POST /consultations/{id}/media — unggah audio/gambar (multipart)",
            "7. Tampilkan suggestion + entities ke dokter (AISuggestion JSON)",
            "8. POST /api/agent/conversations/{id}/vet-record — input dokter lengkap",
            "9. POST /api/agent/conversations/{id}/chat — interaksi agent (hemat token)",
            "10. GET /api/integration/entities/{id} — ambil ID entitas untuk sync ke DB utama",
            "11. POST /consultations/{id}/feedback — penilaian saran AI",
        ],
        "shortcuts": {
            "single_shot": "POST /api/consult — tanpa sesi, tanpa learning loop",
            "ml_only": "POST /ml/predict — prediksi cepat tanpa LLM",
        },
        "token_efficiency": {
            "augmentation_mode": AISettings().augmentation_mode,
            "note": (
                "Mode 'smart' melewati LLM bila ML+KB sudah yakin (hemat token). "
                "Kirim pretranscribed_text / gejala terstruktur untuk minim panggilan vision/STT."
            ),
        },
        "endpoints": {
            "health": f"{base}/health",
            "status": f"{base}/api/status",
            "id_schema": f"{base}/api/integration/id-schema",
            "entities": f"{base}/api/integration/entities/{{consultation_id}}",
            "consultations": f"{base}/consultations",
            "consultations_by_external": f"{base}/api/integration/consultations/by-external/{{external_id}}",
            "categories": f"{base}/categories",
            "symptoms": f"{base}/api/symptoms",
        },
        "entity_ids": ID_SCHEMA,
        "headers_required": {
            "X-Sobatpaws-Key": auth["enabled"],
            "Content-Type": "application/json",
        },
        "media_upload": {
            "endpoint": "POST /consultations/{id}/media",
            "fields": ["file", "modality (audio|image|video_frame)", "channel"],
            "tip": "Gunakan pretranscribed_text di JSON bila STT sudah di device — hemat token Whisper.",
        },
        "learning_backend": LEARNING_BACKEND,
        "platform": {
            "manifest_url": f"{base}/api/platform/manifest",
            "doctor_url": f"{base}/api/platform/doctor",
            "registry_url": f"{base}/api/platform/registry",
            "pipeline_url": f"{base}/api/platform/pipeline",
            "agent_api": f"{base}/api/agent",
        },
    }


@router.get("/health", dependencies=[Depends(require_vet)])
def integration_health() -> dict:
    """Health check autentikasi vet app."""
    return {"status": "ok", "authenticated": True, "role": "vet"}


@router.get("/capabilities")
def capabilities() -> dict:
    """Kemampuan AI yang tersedia untuk app vet."""
    from ..ai.llm import LLMClient
    from ..ai.provider_connector import connection_status

    llm = LLMClient()
    prov = connection_status()
    return {
        "llm_available": llm.available or prov.get("primary_available"),
        "provider": AISettings().provider,
        "model": llm.model,
        "external_agents": prov,
        "features": {
            "multimodal_intake": True,
            "session_consultation": True,
            "single_shot_consult": True,
            "ml_predict": True,
            "doctor_learning_loop": True,
            "offline_rule_based": True,
            "llm_augmentation": (llm.available or prov.get("anthropic_configured")
                                 or prov.get("openai_configured"))
            and AISettings().augmentation_mode != "never",
            "anthropic_claude": prov.get("anthropic_configured", False),
            "openai": prov.get("openai_configured", False),
            "provider_fallback_chain": True,
            "agent_chat_api": True,
        },
        "agent_endpoints": {
            "providers": "/api/agent/providers",
            "provider_status": "/api/agent/providers/status",
            "provider_test": "POST /api/agent/providers/test?provider_id=anthropic",
            "agent_chat": "POST /api/agent/conversations/{id}/chat",
        },
        "ai_efficiency": get_telemetry().summary(limit_recent=0),
    }
