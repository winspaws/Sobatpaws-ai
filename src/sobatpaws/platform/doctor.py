"""Platform doctor — diagnostik kesehatan sistem untuk dev & AI agent.

Menghasilkan laporan JSON terstruktur: komponen OK/gagal, file hilang,
model terlatih, gold rows, manifest synthetic, dll.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..config import (
    ARTIFACTS_DIR,
    DATA_DIR,
    DBML_DIR,
    EXCEL_DIR,
    GENERATED_DIR,
    ML_VIEWS_DIR,
    REGISTRY_PATH,
    SEED_DIR,
)
from ..data_loader import load_knowledge_base


def _check_path(path: Path, *, min_size: int = 0) -> dict[str, Any]:
    if not path.exists():
        return {"ok": False, "detail": "missing"}
    if path.is_file() and path.stat().st_size < min_size:
        return {"ok": False, "detail": "empty"}
    return {"ok": True, "detail": str(path)}


def run_doctor() -> dict[str, Any]:
    """Jalankan semua pemeriksaan; kembalikan laporan JSON."""
    checks: list[dict[str, Any]] = []

    # --- Curated knowledge base ---
    try:
        kb = load_knowledge_base()
        stats = kb.stats()
        checks.append({
            "id": "knowledge_base",
            "ok": stats["categories"] > 0 and stats["diseases"] > 0,
            "track": "curated",
            "stats": stats,
        })
    except Exception as exc:  # noqa: BLE001
        checks.append({"id": "knowledge_base", "ok": False, "error": str(exc)})

    # --- Seed SQL ---
    seed = _check_path(SEED_DIR / "seed.sql", min_size=100)
    checks.append({"id": "seed_sql", "track": "curated", **seed})

    # --- Synthetic generated ---
    gen_manifest = GENERATED_DIR / "manifest.json"
    if gen_manifest.exists():
        try:
            manifest = json.loads(gen_manifest.read_text(encoding="utf-8"))
            checks.append({
                "id": "synthetic_manifest",
                "ok": True,
                "track": "synthetic",
                "grand_total_rows": manifest.get("grand_total_rows"),
                "tables": len(manifest.get("tables", {})),
            })
        except Exception as exc:  # noqa: BLE001
            checks.append({"id": "synthetic_manifest", "ok": False, "error": str(exc)})
    else:
        checks.append({
            "id": "synthetic_manifest",
            "ok": False,
            "track": "synthetic",
            "detail": "Jalankan scripts/generate_all.py",
        })

    # --- ML views ---
    mlv_files = list(ML_VIEWS_DIR.glob("*")) if ML_VIEWS_DIR.exists() else []
    checks.append({
        "id": "ml_views",
        "ok": len(mlv_files) > 0,
        "track": "synthetic",
        "file_count": len(mlv_files),
        "detail": "Jalankan scripts/build_ml_views.py" if not mlv_files else "ok",
    })

    # --- ML models ---
    models_dir = ARTIFACTS_DIR / "models"
    metas = sorted(models_dir.glob("symptom_disease_*.meta.json")) if models_dir.exists() else []
    checks.append({
        "id": "ml_models",
        "ok": len(metas) > 0,
        "track": "ml",
        "model_count": len(metas),
        "categories": [
            m.stem.replace("symptom_disease_", "").replace(".meta", "") for m in metas
        ],
        "detail": "Jalankan python -m sobatpaws.ml.train" if not metas else "ok",
    })

    # --- Learning loop ---
    learning_dir = ARTIFACTS_DIR / "learning"
    gold = 0
    try:
        from ..ai.learning_store import get_store

        store = get_store()
        gold = len(store.export_clinical_rows())
        lstats = store.stats()
        checks.append({
            "id": "learning_store",
            "ok": True,
            "track": "learning",
            "stats": lstats,
            "gold_rows": gold,
            "backend": store.backend_info(),
        })
    except Exception as exc:  # noqa: BLE001
        checks.append({"id": "learning_store", "ok": False, "error": str(exc)})

    # --- Registry ---
    reg = _check_path(REGISTRY_PATH)
    checks.append({"id": "platform_registry", "track": "platform", **reg})

    # --- Excel exports ---
    xlsx = list(EXCEL_DIR.glob("Sobatpaws_*.xlsx")) if EXCEL_DIR.exists() else []
    checks.append({
        "id": "excel_exports",
        "ok": len(xlsx) > 0,
        "track": "export",
        "count": len(xlsx),
    })

    # --- DBML schema ---
    checks.append({
        "id": "dbml_schema",
        "track": "platform",
        **_check_path(DBML_DIR / "schema.dbml"),
    })

    all_ok = all(c.get("ok") for c in checks if c["id"] not in (
        "synthetic_manifest", "ml_views", "excel_exports", "platform_registry"
    ))
    optional_ok = sum(1 for c in checks if c.get("ok"))

    return {
        "status": "healthy" if all_ok else "degraded",
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "checks_total": len(checks),
            "checks_ok": optional_ok,
            "critical_ok": all_ok,
            "gold_rows_ready_for_retrain": gold,
        },
        "checks": checks,
        "recommended_next": _recommendations(checks),
    }


def _recommendations(checks: list[dict]) -> list[str]:
    rec: list[str] = []
    by_id = {c["id"]: c for c in checks}
    if not by_id.get("ml_models", {}).get("ok"):
        rec.append("python -m sobatpaws.platform.pipeline --step train_ml")
    if not by_id.get("synthetic_manifest", {}).get("ok"):
        rec.append("python scripts/generate_all.py --scale 0.05")
    if not by_id.get("ml_views", {}).get("ok") and by_id.get("synthetic_manifest", {}).get("ok"):
        rec.append("python scripts/build_ml_views.py")
    if not by_id.get("platform_registry", {}).get("ok"):
        rec.append("python -m sobatpaws.platform.registry --refresh")
    if by_id.get("learning_store", {}).get("gold_rows", 0) > 0:
        rec.append("python -m sobatpaws.ml.retrain")
    if not rec:
        rec.append("Sistem siap — jalankan ./run.sh untuk API")
    return rec


if __name__ == "__main__":
    report = run_doctor()
    print(json.dumps(report, ensure_ascii=False, indent=2))
