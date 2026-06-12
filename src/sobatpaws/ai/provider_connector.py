"""Uji koneksi ke provider AI eksternal (Anthropic/Claude, OpenAI, lokal)."""
from __future__ import annotations

import logging
import time
from typing import Any

from ..config import AISettings
from .llm import LLMClient
from .providers import (
    KIND_ANTHROPIC,
    KIND_LOCAL,
    KIND_OPENAI,
    ProviderConfig,
    ProviderRegistry,
    get_provider_registry,
)

logger = logging.getLogger("sobatpaws.ai.connector")

PING_SYSTEM = "Anda asisten tes koneksi. Jawab JSON: {\"status\":\"ok\",\"provider\":\"nama\"}"
PING_USER = "ping"


def test_provider(cfg: ProviderConfig, *, timeout_hint_ms: int = 15000) -> dict[str, Any]:
    """Uji koneksi live ke satu provider. Tidak memakai cache."""
    base: dict[str, Any] = {
        "id": cfg.id,
        "name": cfg.name,
        "kind": cfg.kind,
        "model": cfg.default_model,
        "configured": cfg.available(),
        "connected": False,
        "latency_ms": None,
        "error": None,
        "response_preview": None,
    }
    if not cfg.available():
        base["error"] = "API key atau base_url belum dikonfigurasi"
        return base

    t0 = time.perf_counter()
    try:
        if cfg.kind == KIND_ANTHROPIC:
            result = _test_anthropic(cfg)
        elif cfg.kind == KIND_OPENAI:
            result = _test_openai(cfg)
        elif cfg.kind in (KIND_LOCAL, "custom"):
            result = _test_openai_compatible(cfg)
        else:
            client = LLMClient.for_provider(cfg)
            data = client.chat_json(PING_SYSTEM, PING_USER, max_tokens=60, operation="connect_test")
            result = {"preview": str(data)[:120] if data else None, "ok": bool(data)}
    except Exception as exc:  # noqa: BLE001
        base["latency_ms"] = int((time.perf_counter() - t0) * 1000)
        base["error"] = f"{type(exc).__name__}: {exc}"
        logger.warning("Test koneksi %s gagal: %s", cfg.id, exc)
        return base

    base["latency_ms"] = int((time.perf_counter() - t0) * 1000)
    base["connected"] = bool(result.get("ok"))
    base["response_preview"] = result.get("preview")
    if not base["connected"]:
        base["error"] = result.get("error") or "Tidak ada respons valid"
    return base


def _test_anthropic(cfg: ProviderConfig) -> dict[str, Any]:
    import anthropic

    s = AISettings()
    api_key = cfg.api_key or s.anthropic_api_key
    model = cfg.default_model or s.anthropic_model
    client = anthropic.Anthropic(api_key=api_key)
    msg = client.messages.create(
        model=model,
        max_tokens=32,
        temperature=0,
        system=PING_SYSTEM,
        messages=[{"role": "user", "content": PING_USER}],
    )
    text = "".join(
        b.text for b in msg.content if getattr(b, "type", "") == "text"
    )
    return {"ok": bool(text.strip()), "preview": text[:120]}


def _test_openai(cfg: ProviderConfig) -> dict[str, Any]:
    from openai import OpenAI

    s = AISettings()
    api_key = cfg.api_key or s.openai_api_key
    model = cfg.default_model or s.openai_model
    client = OpenAI(api_key=api_key)
    resp = client.chat.completions.create(
        model=model,
        max_tokens=32,
        temperature=0,
        messages=[
            {"role": "system", "content": PING_SYSTEM},
            {"role": "user", "content": PING_USER},
        ],
    )
    text = resp.choices[0].message.content or ""
    return {"ok": bool(text.strip()), "preview": text[:120]}


def _test_openai_compatible(cfg: ProviderConfig) -> dict[str, Any]:
    from openai import OpenAI

    s = AISettings()
    base_url = (cfg.base_url or s.local_llm_base_url or "").rstrip("/")
    api_key = cfg.api_key or s.local_llm_api_key or "ollama"
    model = cfg.default_model or s.local_llm_model
    if not base_url:
        return {"ok": False, "error": "base_url kosong"}
    client = OpenAI(api_key=api_key, base_url=base_url)
    resp = client.chat.completions.create(
        model=model,
        max_tokens=32,
        temperature=0,
        messages=[
            {"role": "system", "content": PING_SYSTEM + " JSON valid."},
            {"role": "user", "content": PING_USER},
        ],
    )
    text = resp.choices[0].message.content or ""
    return {"ok": bool(text.strip()), "preview": text[:120]}


def test_all_providers(
    registry: ProviderRegistry | None = None,
    provider_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Uji semua provider aktif atau subset."""
    reg = registry or get_provider_registry()
    targets = reg.list_providers(active_only=False)
    if provider_ids:
        targets = [p for p in targets if p["id"] in provider_ids]

    results = []
    for meta in targets:
        cfg = reg.get(meta["id"])
        if not cfg:
            continue
        results.append(test_provider(cfg))

    primary = reg.get_primary()
    connected = [r for r in results if r.get("connected")]
    return {
        "primary_id": primary.id if primary else None,
        "primary_connected": any(r["id"] == primary.id and r["connected"] for r in results) if primary else False,
        "total": len(results),
        "connected_count": len(connected),
        "results": results,
    }


def connection_status(registry: ProviderRegistry | None = None) -> dict[str, Any]:
    """Status konfigurasi tanpa panggilan live (cepat)."""
    reg = registry or get_provider_registry()
    primary = reg.get_primary()
    providers = reg.list_providers(active_only=False)
    return {
        "primary_id": primary.id if primary else None,
        "primary_available": primary.available() if primary else False,
        "fallback_chain": [p.id for p in reg.get_chain()],
        "providers": providers,
        "anthropic_configured": any(
            p["kind"] == KIND_ANTHROPIC and p.get("has_api_key") for p in providers
        ),
        "openai_configured": any(
            p["kind"] == KIND_OPENAI and p.get("has_api_key") for p in providers
        ),
    }
