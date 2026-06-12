"""Dependency & status helpers (hindari circular import main ↔ admin)."""
from __future__ import annotations

from functools import lru_cache

from ..ai.agent_manager import AgentManager, get_agent_manager
from ..ai.consultation import ConsultationService
from ..ai.llm import LLMClient
from ..config import ARTIFACTS_DIR, DATABASE_URL, AISettings


@lru_cache(maxsize=1)
def get_service() -> ConsultationService:
    return get_agent_manager().svc


@lru_cache(maxsize=1)
def get_agent() -> AgentManager:
    return get_agent_manager()


def ml_status() -> dict:
    models_dir = ARTIFACTS_DIR / "models"
    trained: list[str] = []
    if models_dir.exists():
        for meta in sorted(models_dir.glob("symptom_disease_*.meta.json")):
            cat = meta.stem.replace("symptom_disease_", "").replace(".meta", "")
            trained.append(cat)
    return {
        "ok": bool(trained),
        "trained_categories": trained,
        "model_count": len(trained),
        "artifacts_dir": str(models_dir),
    }


def ai_status() -> dict:
    s = AISettings()
    llm = LLMClient()
    from ..ai.provider_connector import connection_status
    from ..ai.providers import get_provider_registry

    reg = get_provider_registry()
    primary = reg.get_primary()
    conn = connection_status(reg)
    return {
        "ok": True,
        "provider": primary.id if primary else s.provider,
        "llm_available": llm.available,
        "mode": "llm_augmented" if llm.available else "rule_based",
        "augmentation_mode": s.augmentation_mode,
        "model": llm.model,
        "providers": reg.list_providers(),
        "external_providers": {
            "anthropic_configured": conn["anthropic_configured"],
            "openai_configured": conn["openai_configured"],
            "primary_id": conn["primary_id"],
            "fallback_chain": conn["fallback_chain"],
        },
        "agent_store": get_agent_manager().store.backend_info(),
    }


def mask_url(url: str) -> str:
    if "@" in url:
        scheme_creds, _, host = url.partition("@")
        scheme = scheme_creds.split("//", 1)[0]
        return f"{scheme}//***@{host}"
    return url


def db_status() -> dict:
    info: dict = {"ok": False, "url": mask_url(DATABASE_URL), "tables": None, "detail": None}
    try:
        from sqlalchemy import create_engine, inspect, text

        engine = create_engine(
            DATABASE_URL, connect_args={"connect_timeout": 2}, pool_pre_ping=True
        )
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            info["tables"] = len(inspect(engine).get_table_names())
        info["ok"] = True
        info["detail"] = "Koneksi PostgreSQL berhasil."
        engine.dispose()
    except Exception as exc:  # noqa: BLE001
        info["detail"] = f"Tidak terhubung: {type(exc).__name__}"
    return info
