"""Kebijakan hemat token — tentukan kapan LLM dipanggil, berapa token, dan kapan skip.

Prinsip:
1. Rule/KB/ML dulu. LLM hanya jika menambah nilai.
2. Prompt pendek. Output dibatasi ketat.
3. Cache agresif (normalisasi teks).
4. Darurat = template (lebih aman + 0 token).
5. Sapaan / thanks / vision placeholder = template.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from ..config import AISettings

# Agent yang cukup template (aman + hemat)
TEMPLATE_ONLY_AGENTS = frozenset({
    "triage_emergency",
    "vision_screening",
    "meal_planner",
    "medication_adherence",
    "behavior_fun",
})

GREETING_RE = re.compile(
    r"^\s*(halo|hai|hi|hey|selamat\s+(pagi|siang|sore|malam)|assalamualaikum|"
    r"pagi|siang|sore|malam|helo)\b",
    re.I,
)
THANKS_RE = re.compile(r"\b(terima\s*kasih|makasih|thanks|thank you|thx)\b", re.I)
SHORT_CHAT_RE = re.compile(r"^[\w\s,.!?]{0,24}$")
PLACEHOLDER_KEYS = frozenset({
    "", "sk-xxxx", "xxxx", "changeme", "your-key", "dummy", "ollama", "test", "none",
})

# Token budget per jenis operasi (completion)
TOKEN_BUDGET = {
    "intent": 16,
    "pawnia_chat": 220,
    "augmentation": 280,
    "vision": 280,
    "default": 400,
}


@dataclass(frozen=True)
class TokenDecision:
    use_llm: bool
    reason: str
    max_tokens: int
    operation: str


def _norm_text(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def normalize_cache_text(text: str, *, max_chars: int = 400) -> str:
    """Kunci cache: lowercase, spasi normal, potong."""
    return _norm_text(text)[:max_chars]


def token_budget_for(operation: str) -> int:
    s = AISettings()
    cap = int(getattr(s, "pawnia_max_tokens", 0) or 0) or TOKEN_BUDGET.get(
        operation if operation in TOKEN_BUDGET else "default",
        TOKEN_BUDGET["default"],
    )
    if operation == "pawnia_chat":
        cap = min(cap, int(getattr(s, "pawnia_max_tokens", 220) or 220))
    return min(cap, max(32, s.max_tokens))


def should_use_llm_pawnia(
    *,
    agent_type: str,
    user_text: str,
    intent_confidence: float = 0.0,
    risk_score: int = 0,
) -> TokenDecision:
    """Keputusan LLM untuk respons Pawnia."""
    s = AISettings()
    mode = (s.augmentation_mode or "smart").lower()
    op = "pawnia_chat"
    max_tok = token_budget_for(op)

    if mode == "never":
        return TokenDecision(False, "mode_never", max_tok, op)

    ready, cred_reason = llm_credentials_ready(s)
    if not ready:
        return TokenDecision(False, cred_reason, max_tok, op)

    text = _norm_text(user_text)
    agent = (agent_type or "").strip()

    if agent in TEMPLATE_ONLY_AGENTS:
        return TokenDecision(False, f"template_agent_{agent}", max_tok, op)

    if not text:
        return TokenDecision(False, "empty_text", max_tok, op)

    if GREETING_RE.search(text) and len(text) < 80:
        return TokenDecision(False, "greeting", max_tok, op)

    if THANKS_RE.search(text) and len(text) < 120:
        return TokenDecision(False, "thanks", max_tok, op)

    if agent == "pet_companion" and intent_confidence >= 0.45 and len(text) < 40:
        return TokenDecision(False, "short_companion", max_tok, op)

    if agent == "pet_companion" and SHORT_CHAT_RE.match(text) and intent_confidence >= 0.3:
        return TokenDecision(False, "generic_chat", max_tok, op)

    # Darurat sudah di TEMPLATE_ONLY; jaga-jaga jika agent lain + risk tinggi
    if risk_score >= 81:
        return TokenDecision(False, "critical_template", max_tok, op)

    if mode == "always":
        return TokenDecision(True, "mode_always", max_tok, op)

    # smart: LLM hanya untuk kasus yang butuh bahasa kontekstual
    if agent in ("nutrition_advisor", "behavior_insight", "vet_escalation") and len(text) >= 18:
        return TokenDecision(True, "contextual_value", max_tok, op)

    if agent == "pet_companion" and len(text) >= 40:
        return TokenDecision(True, "long_companion", min(max_tok, 180), op)

    return TokenDecision(False, "smart_skip", max_tok, op)


def should_detect_intent_llm(text: str, keyword_confidence: float) -> TokenDecision:
    """LLM intent hanya jika keyword sangat ambigu."""
    max_tok = TOKEN_BUDGET["intent"]
    s = AISettings()
    if (s.augmentation_mode or "smart").lower() == "never":
        return TokenDecision(False, "mode_never", max_tok, "intent")
    if keyword_confidence >= 0.30:
        return TokenDecision(False, "keyword_enough", max_tok, "intent")
    if len(_norm_text(text)) < 12:
        return TokenDecision(False, "too_short", max_tok, "intent")
    return TokenDecision(True, "ambiguous_intent", max_tok, "intent")


def is_placeholder_key(api_key: str | None) -> bool:
    key = (api_key or "").strip().lower()
    if key in PLACEHOLDER_KEYS:
        return True
    if key.startswith("sk-xxxx") or key.endswith("xxxx"):
        return True
    return len(key) < 12


def llm_credentials_ready(settings: AISettings | None = None) -> tuple[bool, str]:
    """True hanya jika kunci API nyata (bukan placeholder)."""
    s = settings or AISettings()
    provider = (s.provider or "local").lower()
    if provider in ("local", "local_llm"):
        if not (s.local_llm_base_url or "").strip():
            return False, "no_base_url"
        if "sumopod" in (s.local_llm_base_url or "").lower() and is_placeholder_key(s.local_llm_api_key):
            return False, "placeholder_sumopod_key"
        if is_placeholder_key(s.local_llm_api_key) and "11434" not in (s.local_llm_base_url or ""):
            return False, "placeholder_local_key"
        return True, "local_ready"
    if provider == "openai":
        if is_placeholder_key(s.openai_api_key):
            return False, "placeholder_openai_key"
        return True, "openai_ready"
    if provider == "anthropic":
        if is_placeholder_key(s.anthropic_api_key):
            return False, "placeholder_anthropic_key"
        return True, "anthropic_ready"
    return False, "unknown_provider"


def skip_reasons_summary(rows: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for r in rows:
        if not r.get("skipped"):
            continue
        reason = r.get("skip_reason") or "unknown"
        counts[reason] = counts.get(reason, 0) + 1
    return dict(sorted(counts.items(), key=lambda x: -x[1]))


def compact_pet_context(context: dict | None) -> str:
    """Satu baris konteks hewan — hemat prompt."""
    ctx = context or {}
    src = ctx.get("proprietary") or ctx.get("pet_context") or {}
    parts = []
    for key, label in (
        ("name", "nama"),
        ("species", "spesies"),
        ("breed", "ras"),
        ("age_years", "usia"),
        ("weight_kg", "bb"),
    ):
        val = src.get(key) or src.get("age")
        if key == "age_years":
            val = src.get("age_years") or src.get("age")
        if val not in (None, ""):
            parts.append(f"{label}:{val}")
    return ",".join(parts) if parts else "-"
