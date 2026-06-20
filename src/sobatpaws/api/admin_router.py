"""Dashboard admin Sobatpaws — monitoring data, integrasi, & penggunaan AI."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from ..ai.cache import get_llm_cache
from ..ai.llm import LLMClient
from ..ai.provider_connector import connection_status
from ..ai.telemetry import get_telemetry
from ..config import AISettings, LEARNING_BACKEND
from .auth import auth_status, require_admin
from .deps import ai_status, db_status, get_service, ml_status

router = APIRouter(prefix="/admin", tags=["Admin Dashboard"], dependencies=[Depends(require_admin)])


@router.get("/overview")
def admin_overview() -> dict:
    """Ringkasan sistem untuk dashboard admin."""
    svc = get_service()
    telemetry = get_telemetry().summary(limit_recent=10)
    return {
        "auth": auth_status(),
        "knowledge_base": svc.kb.stats(),
        "learning": {
            "stats": svc.store.stats(),
            "backend": svc.store.backend_info(),
            "gold_rows": len(svc.store.export_clinical_rows()),
        },
        "ai": ai_status(),
        "ai_usage": telemetry,
        "ml": ml_status(),
        "database": db_status(),
        "cache": get_llm_cache().stats(),
        "settings": {
            "learning_backend": LEARNING_BACKEND,
            "augmentation_mode": AISettings().augmentation_mode,
            "daily_token_budget": AISettings().daily_token_budget,
            "max_tokens": AISettings().max_tokens,
            "skip_llm_confidence": AISettings().skip_llm_confidence,
        },
    }


@router.get("/ai/usage")
def admin_ai_usage(limit: int = 100) -> dict:
    """Detail penggunaan token & biaya LLM."""
    return get_telemetry().summary(limit_recent=limit)


@router.get("/learning/events")
def admin_learning_events(kind: str | None = None, limit: int = 50) -> dict:
    """Event pembelajaran terbaru (audit trail)."""
    svc = get_service()
    store = svc.store
    kinds = [kind] if kind else list(getattr(store, "FILES", {}).keys())
    if not kinds:
        kinds = ["consultation", "intake", "suggestion", "doctor_input", "feedback"]
    events: list[dict] = []
    for k in kinds:
        reader = getattr(store, "_read", None)
        if not reader:
            break
        for row in reader(k):
            row["_kind"] = k
            events.append(row)
    events.sort(key=lambda r: r.get("recorded_at", ""), reverse=True)
    return {"count": len(events[:limit]), "events": events[:limit]}


@router.get("/integration/status")
def admin_integration_status() -> dict:
    """Status integrasi untuk app vet & layanan eksternal."""
    svc = get_service()
    telemetry = get_telemetry().summary(limit_recent=5)
    auth = auth_status()
    return {
        "api_ready": True,
        "auth_configured": auth["enabled"],
        "vet_app": {
            "auth_required": auth["vet_key_configured"],
            "endpoints": ["/consultations", "/api/consult", "/ml/predict", "/categories"],
            "learning_backend": svc.store.backend_info(),
        },
        "ai_agent": {
            "mode": AISettings().augmentation_mode,
            "llm_available": LLMClient().available,
            "providers": connection_status(),
            "efficiency": {
                "cache_hit_rate": telemetry.get("cache_hit_rate"),
                "skipped_llm_calls": telemetry.get("skipped"),
                "today_tokens": telemetry.get("today_tokens"),
                "today_cost_usd": telemetry.get("today_cost_usd"),
                "budget_remaining": telemetry.get("daily_budget_remaining"),
            },
        },
        "data_pipeline": {
            "knowledge_base": svc.kb.stats(),
            "excel_exports": _excel_count(),
            "platform_registry": _registry_summary(),
        },
    }


def _registry_summary() -> dict:
    try:
        from ..platform.registry import load_registry
        reg = load_registry()
        if not reg:
            return {"exists": False}
        return {
            "exists": True,
            "updated_at": reg.get("updated_at"),
            "model_count": len(reg.get("models", [])),
            "gold_rows": reg.get("data_tracks", {}).get("learning", {}).get("gold_rows"),
        }
    except Exception:  # noqa: BLE001
        return {"exists": False}


def _excel_count() -> int:
    from ..config import EXCEL_DIR
    if not EXCEL_DIR.exists():
        return 0
    return len(list(EXCEL_DIR.glob("Sobatpaws_*.xlsx")))


@router.post("/ai/budget/reset")
def reset_daily_budget() -> dict:
    """Reset counter budget harian (admin only, in-memory)."""
    t = get_telemetry()
    with t._lock:  # noqa: SLF001 — admin maintenance
        t._daily_tokens = 0
        t._today = __import__("datetime").date.today()
    return {"status": "reset", "daily_tokens": 0}
