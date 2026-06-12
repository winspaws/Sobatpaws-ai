"""Konfigurasi path & environment untuk Sobatpaws."""
from __future__ import annotations

import os
from pathlib import Path

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # dotenv opsional
    pass

# Root proyek = dua level di atas file ini (src/sobatpaws/config.py -> root)
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

    provider = os.getenv("SOBATPAWS_AI_PROVIDER", "openai")  # openai | anthropic | local
    openai_api_key = os.getenv("OPENAI_API_KEY", "")
    openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY", "")
    anthropic_model = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-latest")
    temperature = float(os.getenv("SOBATPAWS_AI_TEMPERATURE", "0.2"))
    max_tokens = int(os.getenv("SOBATPAWS_AI_MAX_TOKENS", "800"))
    augmentation_mode = os.getenv("SOBATPAWS_AI_AUGMENTATION_MODE", "smart")
    daily_token_budget = int(os.getenv("SOBATPAWS_AI_DAILY_TOKEN_BUDGET", "0"))
    cache_ttl_sec = int(os.getenv("SOBATPAWS_AI_CACHE_TTL_SEC", "3600"))
    skip_llm_confidence = float(os.getenv("SOBATPAWS_AI_SKIP_LLM_CONFIDENCE", "0.82"))
    local_llm_base_url = os.getenv("LOCAL_LLM_BASE_URL", "http://localhost:11434/v1")
    local_llm_api_key = os.getenv("LOCAL_LLM_API_KEY", "ollama")
    local_llm_model = os.getenv("LOCAL_LLM_MODEL", "llama3.2")
    fallback_providers = os.getenv("SOBATPAWS_AI_FALLBACK_CHAIN", "local,openai,anthropic")


DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost:5432/sobatpaws")

# Backend penyimpanan agent AI: jsonl | postgres | both
AI_STORE_BACKEND = os.getenv("SOBATPAWS_AI_STORE_BACKEND", "jsonl")

# Backend penyimpanan bahan pembelajaran: jsonl | postgres | both
LEARNING_BACKEND = os.getenv("SOBATPAWS_LEARNING_BACKEND", "jsonl")

VET_API_KEY = os.getenv("SOBATPAWS_VET_API_KEY", "")
ADMIN_API_KEY = os.getenv("SOBATPAWS_ADMIN_API_KEY", "")
