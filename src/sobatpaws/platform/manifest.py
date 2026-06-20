"""Manifest platform Sobatpaws — kontrak machine-readable untuk AI agent & CI.

Mendefinisikan:
- tiga jalur data (curated JSON, synthetic CSV, learning loop)
- langkah pipeline terurut dengan I/O dan dependensi
- zona aman edit untuk agent
"""
from __future__ import annotations

from typing import Any

from ..config import (
    ARTIFACTS_DIR,
    CLINICAL_DIR,
    DATA_DIR,
    DBML_DIR,
    EXCEL_DIR,
    GENERATED_DIR,
    ML_VIEWS_DIR,
    PROJECT_ROOT,
    REGISTRY_PATH,
    SCRIPTS_DIR,
    SEED_DIR,
)

# Langkah pipeline: id, deskripsi, perintah, track, depends_on
PIPELINE_STEPS: list[dict[str, Any]] = [
    {
        "id": "validate_kb",
        "track": "curated",
        "description": "Muat & validasi knowledge base JSON (sumber kebenaran runtime)",
        "command": ["python", "-m", "sobatpaws.data_loader"],
        "depends_on": [],
        "outputs": [str(DATA_DIR / "categories.json"), str(CLINICAL_DIR)],
    },
    {
        "id": "sync_catalogs",
        "track": "curated",
        "description": "Sinkron vocabulary synthetic catalogs.py dari KB JSON",
        "command": ["python", str(SCRIPTS_DIR / "sync_catalogs_from_kb.py")],
        "depends_on": ["validate_kb"],
        "outputs": [str(SCRIPTS_DIR / "_kb_clinical_overlay.py")],
    },
    {
        "id": "seed_sql",
        "track": "curated",
        "description": "Generate seed SQL PostgreSQL dari knowledge base",
        "command": ["python", "-m", "sobatpaws.seed_generator"],
        "depends_on": ["validate_kb"],
        "outputs": [str(SEED_DIR / "seed.sql")],
    },
    {
        "id": "generate_dataset",
        "track": "synthetic",
        "description": "Stage 1: taxonomy + clinical matrix CSV",
        "command": ["python", str(SCRIPTS_DIR / "generate_dataset.py")],
        "depends_on": [],
        "outputs": [str(GENERATED_DIR / "breeds.csv")],
    },
    {
        "id": "generate_operational",
        "track": "synthetic",
        "description": "Stage 2: operational + ML + AI tables CSV",
        "command": ["python", str(SCRIPTS_DIR / "generate_operational.py")],
        "depends_on": ["generate_dataset"],
        "outputs": [str(GENERATED_DIR / "clinical_cases.csv")],
    },
    {
        "id": "validate_csv",
        "track": "synthetic",
        "description": "Validasi FK/PK/enum synthetic dataset",
        "command": ["python", str(SCRIPTS_DIR / "validate_dataset.py")],
        "depends_on": ["generate_operational"],
        "outputs": [str(GENERATED_DIR / "manifest.json")],
    },
    {
        "id": "build_ml_views",
        "track": "synthetic",
        "description": "Bangun tabel fitur ML denormalized (Parquet/CSV gzip)",
        "command": ["python", str(SCRIPTS_DIR / "build_ml_views.py")],
        "depends_on": ["validate_csv"],
        "outputs": [str(ML_VIEWS_DIR)],
    },
    {
        "id": "train_ml",
        "track": "ml",
        "description": "Latih model symptom→disease per kategori (KB / views / hybrid)",
        "command": ["python", "-m", "sobatpaws.ml.train", "--source", "hybrid"],
        "depends_on": ["validate_kb"],
        "outputs": [str(ARTIFACTS_DIR / "models")],
    },
    {
        "id": "retrain_ml",
        "track": "learning",
        "description": "Retrain dari gold rows input dokter (human-in-the-loop)",
        "command": ["python", "-m", "sobatpaws.ml.retrain"],
        "depends_on": ["train_ml"],
        "outputs": [str(ARTIFACTS_DIR / "models")],
    },
    {
        "id": "export_excel",
        "track": "export",
        "description": "Export dataset synthetic ke Excel",
        "command": ["python", str(SCRIPTS_DIR / "export_excel.py"), "--sample-only"],
        "depends_on": ["validate_csv"],
        "outputs": [str(EXCEL_DIR)],
    },
    {
        "id": "export_learning",
        "track": "learning",
        "description": "Export jejak konsultasi + gold rows ke Excel",
        "command": ["python", str(SCRIPTS_DIR / "export_excel.py"), "--learning-only"],
        "depends_on": [],
        "outputs": [str(EXCEL_DIR / "Sobatpaws_08_Learning.xlsx")],
    },
    {
        "id": "refresh_registry",
        "track": "platform",
        "description": "Perbarui platform registry (lineage model + data)",
        "command": ["python", "-m", "sobatpaws.platform.registry", "--refresh"],
        "depends_on": [],
        "outputs": [str(REGISTRY_PATH)],
    },
]

# Pipeline presets untuk agent
PIPELINE_PRESETS: dict[str, list[str]] = {
    "full_synthetic": [
        "generate_dataset", "generate_operational", "validate_csv",
        "build_ml_views", "refresh_registry",
    ],
    "ml_ready": ["validate_kb", "train_ml", "refresh_registry"],
    "learning_loop": ["retrain_ml", "export_learning", "refresh_registry"],
    "agent_bootstrap": ["validate_kb", "train_ml", "refresh_registry"],
    "ci_sample": [
        "generate_dataset", "generate_operational", "validate_csv", "build_ml_views",
    ],
}

PLATFORM_MANIFEST: dict[str, Any] = {
    "name": "Sobatpaws Smart Data Platform",
    "version": "0.3.0",
    "project_root": str(PROJECT_ROOT),
    "data_tracks": {
        "curated_json": {
            "role": "runtime_truth",
            "description": "Knowledge base untuk AI grounding, seed SQL, dan training ML",
            "paths": {
                "categories": str(DATA_DIR / "categories.json"),
                "breeds": str(DATA_DIR / "breeds"),
                "clinical": str(CLINICAL_DIR),
            },
            "loader": "sobatpaws.data_loader.load_knowledge_base",
            "safe_for_agent_edit": True,
        },
        "synthetic_csv": {
            "role": "bulk_analytics_ml_views",
            "description": "Dataset skala besar untuk validasi skema, Excel, ML views",
            "paths": {"generated": str(GENERATED_DIR), "ml_views": str(ML_VIEWS_DIR)},
            "generator": "scripts/generate_all.py",
            "safe_for_agent_edit": False,
        },
        "learning_loop": {
            "role": "human_in_the_loop",
            "description": "Konsultasi + input dokter → gold labels → retrain",
            "paths": {
                "events": str(ARTIFACTS_DIR / "learning"),
                "models": str(ARTIFACTS_DIR / "models"),
            },
            "retrain": "sobatpaws.ml.retrain",
            "safe_for_agent_edit": False,
        },
    },
    "schema": {
        "dbml": str(DBML_DIR / "schema.dbml"),
        "postgres_schema": str(SEED_DIR / "schema.sql"),
        "learning_table": str(SEED_DIR / "learning.sql"),
    },
    "runtime": {
        "api_entry": "sobatpaws.api.main:app",
        "consultation": "sobatpaws.ai.consultation.ConsultationService",
        "suggestion_engine": "sobatpaws.ai.suggestion_engine.SuggestionEngine",
    },
    "agent_guidelines": {
        "canonical_data": "Edit data/*.json untuk perubahan klinis; regenerate seed & retrain ML",
        "do_not": [
            "Edit data/generated/*.csv manual (regenerate via pipeline)",
            "Commit .env atau API keys",
            "Ubah skema DBML tanpa update validate_dataset.py",
        ],
        "preferred_commands": [
            "python -m sobatpaws.platform.doctor",
            "python -m sobatpaws.platform.pipeline --preset ml_ready",
            "python -m sobatpaws.ml.retrain",
        ],
    },
    "presets": PIPELINE_PRESETS,
}


def get_pipeline_steps() -> list[dict[str, Any]]:
    return list(PIPELINE_STEPS)


def get_step(step_id: str) -> dict[str, Any] | None:
    return next((s for s in PIPELINE_STEPS if s["id"] == step_id), None)


def get_preset(name: str) -> list[str] | None:
    return PIPELINE_PRESETS.get(name)
