"""Sinkronisasi artefak ML lokal ke tabel PostgreSQL ml_models.

Dipanggil setelah train/retrain dan refresh_registry. Degradasi anggun bila
DATABASE_URL tidak tersedia atau skema belum dimuat.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

from ..config import ARTIFACTS_DIR, DATABASE_URL, REGISTRY_PATH

logger = logging.getLogger("sobatpaws.platform.model_registry_pg")

_UPSERT_SQL = """
INSERT INTO ml_models (
    name, task_type, algorithm, version, status, artifact_uri, metrics, trained_at
)
VALUES (
    :name,
    CAST(:task_type AS ml_task_type),
    :algorithm,
    :version,
    CAST(:status AS ml_model_status),
    :artifact_uri,
    CAST(:metrics AS json),
    :trained_at
)
ON CONFLICT (name, version) DO UPDATE SET
    task_type = EXCLUDED.task_type,
    algorithm = EXCLUDED.algorithm,
    status = EXCLUDED.status,
    artifact_uri = EXCLUDED.artifact_uri,
    metrics = EXCLUDED.metrics,
    trained_at = EXCLUDED.trained_at,
    updated_at = now()
"""


def _meta_records(category_slug: str | None = None) -> list[dict[str, Any]]:
    models_dir = ARTIFACTS_DIR / "models"
    if not models_dir.exists():
        return []
    paths = sorted(models_dir.glob("symptom_disease_*.meta.json"))
    if category_slug:
        target = models_dir / f"symptom_disease_{category_slug}.meta.json"
        paths = [target] if target.exists() else []
    out: list[dict[str, Any]] = []
    for meta_path in paths:
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            cat = meta.get("category_slug") or meta_path.stem.replace(
                "symptom_disease_", ""
            ).replace(".meta", "")
            out.append({
                "name": f"symptom_disease_{cat}",
                "task_type": meta.get("task_type", "symptom_to_disease"),
                "algorithm": meta.get("algorithm", "random_forest"),
                "version": meta.get("version", "v1"),
                "status": "trained",
                "artifact_uri": meta.get("model_path") or str(
                    models_dir / f"symptom_disease_{cat}.joblib"
                ),
                "metrics": meta.get("metrics", {}),
                "trained_at": datetime.fromtimestamp(
                    meta_path.stat().st_mtime, tz=timezone.utc,
                ),
                "category_slug": cat,
                "meta_path": str(meta_path),
            })
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Skip meta %s: %s", meta_path, exc)
    return out


def sync_models_to_postgres(
    *,
    category_slug: str | None = None,
    database_url: str | None = None,
) -> dict[str, Any]:
    """Upsert semua (atau satu) model symptom→disease ke ml_models."""
    url = database_url or DATABASE_URL
    records = _meta_records(category_slug)
    if not records:
        return {"status": "skipped", "reason": "no model meta files", "synced": 0}

    try:
        from sqlalchemy import create_engine, text

        engine = create_engine(
            url, pool_pre_ping=True, connect_args={"connect_timeout": 3},
        )
        with engine.connect() as conn:
            exists = conn.execute(
                text("""
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.tables
                        WHERE table_schema = 'public' AND table_name = 'ml_models'
                    )
                """)
            ).scalar()
        if not exists:
            return {
                "status": "skipped",
                "reason": "ml_models table missing",
                "synced": 0,
            }
    except Exception as exc:  # noqa: BLE001
        return {"status": "unavailable", "error": str(exc), "synced": 0}

    synced = 0
    from sqlalchemy import text

    with engine.begin() as conn:
        for rec in records:
            conn.execute(
                text(_UPSERT_SQL),
                {
                    "name": rec["name"],
                    "task_type": rec["task_type"],
                    "algorithm": rec["algorithm"],
                    "version": rec["version"],
                    "status": rec["status"],
                    "artifact_uri": rec["artifact_uri"],
                    "metrics": json.dumps(rec["metrics"], ensure_ascii=False),
                    "trained_at": rec["trained_at"],
                },
            )
            synced += 1

    logger.info("Synced %d model(s) to ml_models", synced)
    return {"status": "synced", "synced": synced, "models": [r["name"] for r in records]}


def registry_lineage_snapshot() -> dict[str, Any]:
    """Ringkasan registry + model meta untuk admin/agent."""
    reg: dict[str, Any] = {}
    if REGISTRY_PATH.exists():
        try:
            reg = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            reg = {}
    return {
        "registry_updated_at": reg.get("updated_at"),
        "models_on_disk": len(_meta_records()),
        "models": _meta_records(),
    }
