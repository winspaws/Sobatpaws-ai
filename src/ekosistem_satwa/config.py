"""Konfigurasi path & environment untuk Ekosistem Satwa."""
from __future__ import annotations

import os
from pathlib import Path


def _env(primary: str, fallback: str = "", default: str = "") -> str:
    """Baca env dengan alias SOBATPAWS_* / EKOSISTEM_SATWA_*."""
    val = os.getenv(primary, "").strip()
    if val:
        return val
    if fallback:
        val = os.getenv(fallback, "").strip()
        if val:
            return val
    return default

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # dotenv opsional
    pass

# Root proyek = dua level di atas file ini (src/ekosistem_satwa/config.py -> root)
PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = PROJECT_ROOT / "data"
BREEDS_DIR = DATA_DIR / "breeds"
CLINICAL_DIR = DATA_DIR / "clinical"
GENERATED_DIR = DATA_DIR / "generated"
ML_VIEWS_DIR = DATA_DIR / "ml_views"
EXCEL_DIR = DATA_DIR / "excel"
DBML_DIR = PROJECT_ROOT / "dbml"
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"
SEED_DIR = PROJECT_ROOT / "seed"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
REGISTRY_PATH = ARTIFACTS_DIR / "platform_registry.json"

ARTIFACTS_DIR.mkdir(exist_ok=True)
SEED_DIR.mkdir(exist_ok=True)
GENERATED_DIR.mkdir(exist_ok=True)
ML_VIEWS_DIR.mkdir(exist_ok=True)


class AISettings:
    """Pengaturan provider AI dari environment (kunci API JANGAN di-commit)."""

    provider = _env("EKOSISTEM_SATWA_AI_PROVIDER", "SOBATPAWS_AI_PROVIDER", "local")
    openai_api_key = _env("OPENAI_API_KEY")
    openai_model = _env("OPENAI_MODEL", default="gpt-4o-mini")
    anthropic_api_key = _env("ANTHROPIC_API_KEY")
    anthropic_model = _env("ANTHROPIC_MODEL", default="claude-3-5-sonnet-latest")
    temperature = float(_env("EKOSISTEM_SATWA_AI_TEMPERATURE", "SOBATPAWS_AI_TEMPERATURE", "0.2"))
    max_tokens = int(_env("EKOSISTEM_SATWA_AI_MAX_TOKENS", "SOBATPAWS_AI_MAX_TOKENS", "400"))
    pawnia_max_tokens = int(_env("PAWNIA_MAX_TOKENS", default="220"))
    augmentation_mode = _env(
        "EKOSISTEM_SATWA_AI_AUGMENTATION_MODE", "SOBATPAWS_AI_AUGMENTATION_MODE", "smart"
    )
    daily_token_budget = int(
        _env("EKOSISTEM_SATWA_AI_DAILY_TOKEN_BUDGET", "SOBATPAWS_AI_DAILY_TOKEN_BUDGET", "250000")
    )
    cache_ttl_sec = int(_env("EKOSISTEM_SATWA_AI_CACHE_TTL_SEC", "SOBATPAWS_AI_CACHE_TTL_SEC", "7200"))
    skip_llm_confidence = float(
        _env("EKOSISTEM_SATWA_AI_SKIP_LLM_CONFIDENCE", "SOBATPAWS_AI_SKIP_LLM_CONFIDENCE", "0.75")
    )
    local_llm_base_url = _env(
        "LOCAL_LLM_BASE_URL", default="https://ai.sumopod.com/v1"
    )
    local_llm_api_key = _env("LOCAL_LLM_API_KEY", default="")
    local_llm_model = _env("LOCAL_LLM_MODEL", default="deepseek-v4-flash")
    fallback_providers = _env(
        "EKOSISTEM_SATWA_AI_FALLBACK_CHAIN", "SOBATPAWS_AI_FALLBACK_CHAIN", "local,openai,anthropic"
    )

    # Pawnia tier models (opsional)
    pawnia_default_model = _env("PAWNIA_DEFAULT_MODEL", default="deepseek-v4-flash")
    pawnia_emergency_model = _env("PAWNIA_EMERGENCY_MODEL", default="deepseek-v4-pro")
    pawnia_vision_model = _env("PAWNIA_VISION_MODEL", default="gemini/gemini-2.0-flash-lite")

    # Vision module
    vision_max_video_frames = int(_env("EKOSISTEM_SATWA_VISION_MAX_FRAMES", default="5"))
    vision_max_image_mb = int(_env("EKOSISTEM_SATWA_VISION_MAX_IMAGE_MB", default="10"))
    vision_max_video_mb = int(_env("EKOSISTEM_SATWA_VISION_MAX_VIDEO_MB", default="50"))


DATABASE_URL = _env("DATABASE_URL", default="postgresql://localhost:5432/ekosistemsatwa")

# Backend penyimpanan agent AI: jsonl | postgres | both
AI_STORE_BACKEND = _env("EKOSISTEM_SATWA_AI_STORE_BACKEND", "SOBATPAWS_AI_STORE_BACKEND", "jsonl")

# Backend penyimpanan bahan pembelajaran: jsonl | postgres | both
LEARNING_BACKEND = _env("EKOSISTEM_SATWA_LEARNING_BACKEND", "SOBATPAWS_LEARNING_BACKEND", "jsonl")

# Backend penyimpanan session konsultasi: jsonl | postgres | both
SESSION_STORE_BACKEND = _env("EKOSISTEM_SATWA_SESSION_BACKEND", "SOBATPAWS_SESSION_BACKEND", "jsonl")

VET_API_KEY = _env("EKOSISTEM_SATWA_VET_API_KEY", "SOBATPAWS_VET_API_KEY")
ADMIN_API_KEY = _env("EKOSISTEM_SATWA_ADMIN_API_KEY", "SOBATPAWS_ADMIN_API_KEY")

# Memory Service configuration
MEMORY_BACKEND = os.getenv("EKOSISTEM_SATWA_MEMORY_BACKEND", "jsonl")  # jsonl | postgres | both
SHORT_TERM_MEMORY_TTL_SECONDS = int(os.getenv("EKOSISTEM_SATWA_SHORT_TERM_TTL", str(24 * 60 * 60)))  # 24 hours default
MEMORY_DIR = ARTIFACTS_DIR / "memory"
