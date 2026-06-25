"""Endpoint integrasi untuk aplikasi vet (mobile/web klinik)."""
from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field

from ..config import AISettings, LEARNING_BACKEND
from ..ai.telemetry import get_telemetry
from ..integration.identity import (
    EkosistemSatwaEntityIds,
    entities_from_context,
    get_identity_registry,
    resolve_consultation_id,
)
from ..ai.agent_manager import get_agent_manager
from .auth import auth_status, optional_client, require_vet


class EntityLookupRequest(BaseModel):
    """Request body for bulk entity lookup."""

    external_consultation_ids: list[str] = Field(
        default_factory=list,
        description="List of external consultation IDs to look up",
    )
    consultation_ids: list[str] = Field(
        default_factory=list,
        description="List of internal consultation IDs to look up",
    )


class EntitySyncRequest(BaseModel):
    """Request body for syncing entity registration from external app."""

    consultation_id: str | None = Field(
        None,
        description="Internal AI session ID (optional; generated if missing)",
    )
    external_consultation_id: str | None = Field(
        None,
        description="ID from primary Ekosistem Satwa app",
    )
    org_id: int | None = None
    vet_id: int | None = None
    doctor_id: int | None = None
    user_id: int | None = None
    owner_id: int | None = None
    customer_id: int | None = None
    pet_id: int | None = None
    case_id: int | None = None
    external_refs: dict[str, str] = Field(default_factory=dict)
    context_snapshot: dict[str, Any] | None = Field(
        None,
        description="Optional snapshot of context for audit",
    )


class EntityRegistryFilter(BaseModel):
    """Query filter for entity registry listing."""

    vet_id: int | None = None
    owner_id: int | None = None
    customer_id: int | None = None
    pet_id: int | None = None
    org_id: int | None = None
    limit: int = Field(50, ge=1, le=500)
    offset: int = Field(0, ge=0)


router = APIRouter(prefix="/api/integration", tags=["Integrasi Vet App"])

ID_SCHEMA = {
    "description": "ID entitas Ekosistem Satwa — kirim di context saat POST /consultations",
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
            "note": "ID konsultasi dari app Ekosistem Satwa utama — untuk lookup & sync",
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
        "POST /api/integration/lookup — bulk lookup",
        "GET /api/integration/entity-registry — dump registry dengan filter",
    ],
}


@router.get("/id-schema")
def integration_id_schema() -> dict:
    """Kontrak ID entitas untuk tim developer Ekosistem Satwa."""
    return ID_SCHEMA


@router.get("/entities/{consultation_id}", dependencies=[Depends(require_vet)])
def get_entities(consultation_id: str) -> dict:
    """Ambil bundle ID entitas untuk satu sesi konsultasi."""
    cid = resolve_consultation_id(consultation_id) or consultation_id
    reg = get_identity_registry().get(cid)
    if reg:
        entities = EkosistemSatwaEntityIds(**{
            k: reg[k] for k in EkosistemSatwaEntityIds.model_fields if k in reg
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
    """Lookup sesi AI dari ID konsultasi app Ekosistem Satwa utama."""
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
    """Daftar sesi AI terfilter by ID entitas Ekosistem Satwa."""
    rows = get_agent_manager().find_sessions(
        vet_id=vet_id,
        owner_id=owner_id,
        customer_id=customer_id,
        pet_id=pet_id,
        org_id=org_id,
        limit=limit,
    )
    return {"count": len(rows), "consultations": rows}


@router.get("/entity-registry", dependencies=[Depends(require_vet)])
def entity_registry(
    vet_id: int | None = Query(None),
    owner_id: int | None = Query(None),
    customer_id: int | None = Query(None),
    pet_id: int | None = Query(None),
    org_id: int | None = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> dict:
    """
    Daftar semua entitas di identity registry dengan pagination dan filter.

    Endpoint ini mengembalikan raw data dari JSONL registry untuk sync ke
    database app Ekosistem Satwa utama.
    """
    reg = get_identity_registry()
    owner_id = owner_id or customer_id
    # Get a larger batch for pagination then slice
    all_rows = reg.list_by_filter(
        vet_id=vet_id,
        owner_id=owner_id,
        pet_id=pet_id,
        org_id=org_id,
        limit=limit + offset,  # Get enough for offset + limit
    )
    # Apply offset slicing
    if offset > 0 and offset < len(all_rows):
        rows = all_rows[offset:]
    else:
        rows = all_rows

    # Public-safe dict without internal fields
    public_rows: list[dict] = []
    for r in rows[:limit]:
        if "id" in r:
            r.pop("id", None)
        public_rows.append({
            k: v for k, v in r.items()
            if k in EkosistemSatwaEntityIds.model_fields or k in ("registered_at", "context_snapshot")
        })

    return {
        "count": len(public_rows),
        "offset": offset,
        "limit": limit,
        "registry": public_rows,
        "schema": ID_SCHEMA,
    }


@router.post("/lookup", dependencies=[Depends(require_vet)])
def bulk_lookup(req: EntityLookupRequest) -> dict:
    """
    Bulk lookup entities by external_consultation_id atau consultation_id.

    Mengembalikan map dari ID input ke entities (atau null jika tidak ditemukan).
    """
    reg = get_identity_registry()
    results: dict[str, dict | None] = {}
    not_found: list[str] = []

    # Lookup by external ID
    for ext_id in req.external_consultation_ids:
        cid = reg.resolve_external(ext_id)
        if cid:
            rec = reg.get(cid)
            if rec:
                entities = EkosistemSatwaEntityIds(**{
                    k: rec[k] for k in EkosistemSatwaEntityIds.model_fields if k in rec
                })
                results[ext_id] = {
                    "consultation_id": cid,
                    "external_consultation_id": ext_id,
                    "entities": entities.to_public_dict(),
                }
                continue
        # Check active sessions too
        cid2 = resolve_consultation_id(external_consultation_id=ext_id)
        if cid2:
            detail = get_agent_manager().get_session_detail(cid2)
            if detail:
                results[ext_id] = {
                    "consultation_id": cid2,
                    "external_consultation_id": ext_id,
                    "entities": detail.get("entities"),
                    "session_active": True,
                }
                continue
        results[ext_id] = None
        not_found.append(ext_id)

    # Lookup by internal consultation ID
    for cid in req.consultation_ids:
        rec = reg.get(cid)
        if rec:
            entities = EkosistemSatwaEntityIds(**{
                k: rec[k] for k in EkosistemSatwaEntityIds.model_fields if k in rec
            })
            results[cid] = {
                "consultation_id": cid,
                "entities": entities.to_public_dict(),
            }
            continue
        detail = get_agent_manager().get_session_detail(cid)
        if detail:
            results[cid] = {
                "consultation_id": cid,
                "entities": detail.get("entities"),
                "session_active": True,
            }
            continue
        results[cid] = None
        not_found.append(cid)

    return {
        "total": len(results),
        "found": sum(1 for v in results.values() if v is not None),
        "not_found_count": len(not_found),
        "not_found": not_found if len(not_found) < 20 else not_found[:20],
        "results": results,
    }


@router.post("/sync", dependencies=[Depends(require_vet)])
def sync_entity(req: EntitySyncRequest) -> dict:
    """
    Sync entity registration dari app Ekosistem Satwa utama.

    Endpoint ini memungkinkan app utama mendaftarkan entity ID mapping
    SEBELUM konsultasi dimulai, atau update mapping setelah konsultasi.

    Gunakan ini bila app utama ingin sinkronkan data di luar alur
    POST /consultations normal.
    """
    reg = get_identity_registry()

    # Generate consultation_id if not provided but we have external_consultation_id
    consultation_id = req.consultation_id
    if not consultation_id and req.external_consultation_id:
        # Check if this external_id already maps to something
        existing = reg.resolve_external(req.external_consultation_id)
        if existing:
            consultation_id = existing
        else:
            consultation_id = req.external_consultation_id

    if not consultation_id:
        consultation_id = uuid.uuid4().hex

    # Build entities from request
    entity_ids = EkosistemSatwaEntityIds(
        consultation_id=consultation_id,
        external_consultation_id=req.external_consultation_id,
        org_id=req.org_id,
        vet_id=req.vet_id or req.doctor_id or req.user_id,
        doctor_id=req.doctor_id or req.vet_id or req.user_id,
        user_id=req.user_id or req.vet_id,
        owner_id=req.owner_id or req.customer_id,
        customer_id=req.customer_id or req.owner_id,
        pet_id=req.pet_id,
        case_id=req.case_id,
        external_refs=dict(req.external_refs or {}),
    )

    # Register to registry
    payload = reg.register(
        consultation_id=consultation_id,
        entities=entity_ids,
        context_snapshot=req.context_snapshot,
    )

    # Check if there's an active session and sync there too
    try:
        mgr = get_agent_manager()
        session = mgr.get_session_detail(consultation_id)
        if session:
            # Session exists - we don't update it here, just note that
            session_exists = True
        else:
            session_exists = False
    except Exception:
        session_exists = False

    return {
        "status": "synced",
        "consultation_id": consultation_id,
        "external_consultation_id": entity_ids.external_consultation_id,
        "entities": entity_ids.to_public_dict(),
        "registered_at": payload.get("registered_at"),
        "session_active": session_exists,
    }


@router.get("/manifest")
def integration_manifest(request: Request) -> dict:
    """Kontrak integrasi — dipakai app vet saat onboarding."""
    client = optional_client(request)
    base = str(request.base_url).rstrip("/")
    auth = auth_status()
    return {
        "platform": "Ekosistem Satwa Veterinary ML & AI",
        "api_version": "0.3.0",
        "openapi_url": f"{base}/docs",
        "auth": auth,
        "client": client,
        "recommended_flow": [
            "1. GET /health — cek koneksi",
            "2. GET /api/integration/id-schema — kontrak ID entitas (vet, pelanggan, pet, ...)",
            "3. GET /api/integration/manifest — baca semua endpoint",
            "4. POST /api/integration/sync — (opsional) pre-register entity mapping",
            "5. GET /categories + /categories/{slug}/breeds — muat master data",
            "6. POST /consultations — mulai sesi (context: org_id, vet_id, owner_id, pet_id, external_consultation_id)",
            "7. POST /consultations/{id}/turns — kirim teks tambahan",
            "8. POST /consultations/{id}/media — unggah audio/gambar (multipart)",
            "9. Tampilkan suggestion + entities ke dokter (AISuggestion JSON)",
            "10. POST /api/agent/conversations/{id}/vet-record — input dokter lengkap",
            "11. POST /api/agent/conversations/{id}/chat — interaksi agent (hemat token)",
            "12. GET /api/integration/entities/{id} — ambil ID entitas untuk sync ke DB utama",
            "13. POST /api/integration/lookup — bulk lookup by external IDs",
            "14. GET /api/integration/entity-registry — dump semua mapping untuk sync",
            "15. POST /consultations/{id}/feedback — penilaian saran AI",
        ],
        "shortcuts": {
            "single_shot": "POST /api/consult — tanpa sesi, tanpa learning loop",
            "ml_only": "POST /ml/predict — prediksi cepat tanpa LLM",
            "entity_sync": "POST /api/integration/sync — pre-register entity mapping",
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
            "manifest": f"{base}/api/integration/manifest",
            "id_schema": f"{base}/api/integration/id-schema",
            "entities": f"{base}/api/integration/entities/{{consultation_id}}",
            "entity_registry": f"{base}/api/integration/entity-registry",
            "consultations": f"{base}/consultations",
            "consultations_by_external": f"{base}/api/integration/consultations/by-external/{{external_id}}",
            "bulk_lookup": f"{base}/api/integration/lookup",
            "sync": f"{base}/api/integration/sync",
            "categories": f"{base}/categories",
            "symptoms": f"{base}/api/symptoms",
        },
        "entity_ids": ID_SCHEMA,
        "headers_required": {
            "X-EkosistemSatwa-Key": auth["enabled"],
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
            "entity_sync": True,
            "bulk_lookup": True,
        },
        "agent_endpoints": {
            "providers": "/api/agent/providers",
            "provider_status": "/api/agent/providers/status",
            "provider_test": "POST /api/agent/providers/test?provider_id=anthropic",
            "agent_chat": "POST /api/agent/conversations/{id}/chat",
        },
        "integration_endpoints": {
            "sync": "POST /api/integration/sync",
            "bulk_lookup": "POST /api/integration/lookup",
            "entity_registry": "GET /api/integration/entity-registry",
        },
        "ai_efficiency": get_telemetry().summary(limit_recent=0),
    }
