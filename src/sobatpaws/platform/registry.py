"""Platform registry — lineage data + model ML terpusat untuk agent & admin."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..config import (
    ARTIFACTS_DIR,
    EXCEL_DIR,
    GENERATED_DIR,
    ML_VIEWS_DIR,
    REGISTRY_PATH,
)
from ..data_loader import load_knowledge_base


def load_registry() -> dict[str, Any]:
    if REGISTRY_PATH.exists():
        try:
            return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return {}


def _scan_models() -> list[dict[str, Any]]:
    models_dir = ARTIFACTS_DIR / "models"
    out: list[dict[str, Any]] = []
    if not models_dir.exists():
        return out
    for meta_path in sorted(models_dir.glob("symptom_disease_*.meta.json")):
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            out.append({
                "id": meta_path.stem.replace(".meta", ""),
                "category_slug": meta.get("category_slug"),
                "task_type": meta.get("task_type", "symptom_to_disease"),
                "algorithm": meta.get("algorithm"),
                "metrics": meta.get("metrics", {}),
                "real_case_rows": meta.get("real_case_rows", 0),
                "artifact_path": meta.get("model_path"),
                "meta_path": str(meta_path),
                "mtime": datetime.fromtimestamp(
                    meta_path.stat().st_mtime, tz=timezone.utc
                ).isoformat(),
            })
        except (json.JSONDecodeError, OSError):
            continue
    return out


def _scan_generated() -> dict[str, Any]:
    manifest_path = GENERATED_DIR / "manifest.json"
    if not manifest_path.exists():
        return {"exists": False}
    try:
        m = json.loads(manifest_path.read_text(encoding="utf-8"))
        return {
            "exists": True,
            "grand_total_rows": m.get("grand_total_rows"),
            "table_count": len(m.get("tables", {})),
            "generated_at": m.get("generated_at"),
        }
    except json.JSONDecodeError:
        return {"exists": False, "error": "invalid manifest"}


def _scan_ml_views() -> dict[str, Any]:
    if not ML_VIEWS_DIR.exists():
        return {"exists": False, "views": []}
    views = [p.name for p in ML_VIEWS_DIR.iterdir() if p.is_file()]
    return {"exists": bool(views), "views": views}


def _scan_learning() -> dict[str, Any]:
    try:
        from ..ai.learning_store import get_store

        store = get_store()
        return {
            "stats": store.stats(),
            "gold_rows": len(store.export_clinical_rows()),
            "backend": store.backend_info(),
        }
    except Exception as exc:  # noqa: BLE001
        return {"error": str(exc)}


def refresh_registry() -> dict[str, Any]:
    """Bangun ulang registry dari state filesystem saat ini."""
    kb = load_knowledge_base()
    registry: dict[str, Any] = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "platform_version": "0.3.0",
        "data_tracks": {
            "curated_json": {
                "stats": kb.stats(),
                "source": "data/categories.json + data/breeds + data/clinical",
            },
            "synthetic_csv": _scan_generated(),
            "ml_views": _scan_ml_views(),
            "learning": _scan_learning(),
        },
        "models": _scan_models(),
        "exports": {
            "excel_count": len(list(EXCEL_DIR.glob("Sobatpaws_*.xlsx")))
            if EXCEL_DIR.exists() else 0,
            "excel_dir": str(EXCEL_DIR),
        },
        "lineage": {
            "runtime_training_source": "curated_json (KnowledgeBase synthetic samples)",
            "synthetic_ml_views_source": "data/generated/*.csv + data/ml_views/",
            "retrain_source": "artifacts/learning/doctor_inputs.jsonl (gold labels)",
            "training_sources": ["kb", "views", "hybrid"],
        },
    }
    try:
        from .model_registry_pg import sync_models_to_postgres
        registry["postgres_ml_models"] = sync_models_to_postgres()
    except Exception as exc:  # noqa: BLE001
        registry["postgres_ml_models"] = {"status": "skipped", "error": str(exc)}
    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    REGISTRY_PATH.write_text(
        json.dumps(registry, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return registry


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--print", action="store_true", help="print current registry")
    args = ap.parse_args()
    if args.refresh:
        reg = refresh_registry()
        print(json.dumps(reg, ensure_ascii=False, indent=2))
    elif args.print or True:
        print(json.dumps(load_registry() or refresh_registry(), ensure_ascii=False, indent=2))
