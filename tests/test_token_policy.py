"""Unit tests kebijakan hemat token Pawnia."""
from __future__ import annotations

from ekosistem_satwa.ai.token_policy import (
    is_placeholder_key,
    llm_credentials_ready,
    should_detect_intent_llm,
    should_use_llm_pawnia,
)
from ekosistem_satwa.config import AISettings


def test_placeholder_keys():
    assert is_placeholder_key("sk-xxxx")
    assert is_placeholder_key("")
    assert is_placeholder_key("ollama")
    assert not is_placeholder_key("sk-ant-api03-realkeyvalue123456")


def test_greeting_skips_llm():
    d = should_use_llm_pawnia(
        agent_type="pet_companion", user_text="Halo", intent_confidence=0.9,
    )
    assert d.use_llm is False
    assert d.reason in ("greeting", "placeholder_sumopod_key", "placeholder_local_key", "mode_never")


def test_emergency_always_template():
    d = should_use_llm_pawnia(
        agent_type="triage_emergency",
        user_text="Anjing kejang tidak sadar",
        risk_score=90,
    )
    assert d.use_llm is False


def test_intent_keyword_enough():
    d = should_detect_intent_llm("halo pawnia", 0.45)
    assert d.use_llm is False
    assert d.reason == "keyword_enough"


def test_nutrition_wants_llm_only_if_credentials():
    d = should_use_llm_pawnia(
        agent_type="nutrition_advisor",
        user_text="Rekomendasi makanan kucing Persia alergi ayam",
        intent_confidence=0.8,
    )
    ready, _ = llm_credentials_ready()
    if not ready:
        assert d.use_llm is False
    else:
        assert d.use_llm is True
        assert d.max_tokens <= AISettings().max_tokens
