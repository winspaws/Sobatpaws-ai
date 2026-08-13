"""Kontrak publik untuk app Sobatpaws (Android / iOS / Web / Vet)."""
from __future__ import annotations

from fastapi import APIRouter, Request

from .auth import auth_status
from ..config import AISettings, LEARNING_BACKEND, VET_API_KEY, ADMIN_API_KEY

router = APIRouter(tags=["Integrasi App Sobatpaws"])


@router.get("/api/integration/manifest")
@router.get("/api/v1/app/manifest")
def app_integration_manifest(request: Request) -> dict:
    """Onboarding kontrak untuk aplikasi Sobatpaws."""
    base = str(request.base_url).rstrip("/")
    auth = auth_status()
    s = AISettings()
    return {
        "platform": "Ekosistem Satwa / Sobatpaws",
        "api_version": "0.3.0",
        "status": "ready",
        "openapi_url": f"{base}/docs",
        "auth": {
            **auth,
            "vet_key_configured": bool(VET_API_KEY),
            "admin_key_configured": bool(ADMIN_API_KEY),
            "headers": ["X-EkosistemSatwa-Key", "X-Sobatpaws-Key", "Authorization: Bearer"],
        },
        "ai": {
            "provider": s.provider,
            "model": s.local_llm_model or s.pawnia_default_model,
            "emergency_model": s.pawnia_emergency_model,
            "vision_model": s.pawnia_vision_model,
            "augmentation_mode": s.augmentation_mode,
            "token_efficiency": {
                "max_tokens": s.max_tokens,
                "pawnia_max_tokens": s.pawnia_max_tokens,
                "skip_llm_confidence": s.skip_llm_confidence,
                "cache_ttl_sec": s.cache_ttl_sec,
                "daily_token_budget": s.daily_token_budget,
                "note": "Template-first: sapaan/darurat/reminder tanpa LLM. LLM hanya jika menambah nilai klinis.",
            },
        },
        "recommended_flow": [
            "1. GET /health — cek koneksi",
            "2. GET /api/integration/manifest — kontrak ini",
            "3. GET /categories + /categories/{slug}/breeds — master data",
            "4. POST /api/v1/ai/chat — Pawnia (pemilik hewan / companion)",
            "5. POST /consultations — sesi vet (kirim vet_id, owner_id, pet_id)",
            "6. POST /consultations/{id}/doctor-input — gold label (learning loop)",
            "7. POST /api/vision/analyze — foto gejala (opsional)",
            "8. GET /api/v1/ai/status — diagnostik Pawnia",
        ],
        "endpoints": {
            "health": f"{base}/health",
            "pawnia_chat": f"{base}/api/v1/ai/chat",
            "pawnia_status": f"{base}/api/v1/ai/status",
            "consultations": f"{base}/consultations",
            "ml_predict": f"{base}/ml/predict",
            "vision": f"{base}/api/vision/analyze",
            "categories": f"{base}/categories",
            "symptoms": f"{base}/api/symptoms",
            "admin_integration": f"{base}/api/v1/integration/health",
        },
        "entity_ids_required": ["vet_id", "owner_id", "pet_id"],
        "entity_ids_recommended": ["external_consultation_id", "org_id"],
        "learning_backend": LEARNING_BACKEND,
        "rate_limit": {
            "per_minute": int(__import__("os").getenv("RATE_LIMIT_PER_MINUTE", "120")),
            "note": "429 jika terlampaui; health & docs tidak dihitung.",
        },
    }
