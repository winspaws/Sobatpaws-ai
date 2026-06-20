"""Registry provider LLM — OpenAI, Anthropic, lokal (Ollama/vLLM), custom base_url."""
from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..config import ARTIFACTS_DIR, AISettings

logger = logging.getLogger("sobatpaws.ai.providers")

PROVIDERS_FILE = ARTIFACTS_DIR / "ai" / "providers.json"

# Urutan fallback bila provider utama gagal (hemat token: lokal dulu bila diset)
KIND_OPENAI = "openai"
KIND_ANTHROPIC = "anthropic"
KIND_LOCAL = "local_llm"
KIND_AZURE = "azure_openai"
KIND_CUSTOM = "custom"


@dataclass
class ProviderConfig:
    """Konfigurasi satu provider (selaras ai_providers DBML)."""

    id: str
    name: str
    kind: str
    base_url: str | None = None
    default_model: str = ""
    api_key: str = ""
    is_active: bool = True
    is_primary: bool = False
    config_json: dict[str, Any] = field(default_factory=dict)

    def available(self) -> bool:
        if self.kind in (KIND_OPENAI, KIND_ANTHROPIC):
            return bool(self.api_key)
        if self.kind in (KIND_LOCAL, KIND_CUSTOM, KIND_AZURE):
            return bool(self.base_url or self.api_key)
        return False


class ProviderRegistry:
    """Kelola provider aktif + fallback chain + override file."""

    def __init__(self, settings: AISettings | None = None):
        self.s = settings or AISettings()
        self._providers: list[ProviderConfig] = []
        self._load_builtin()
        self._load_file_overrides()
        self._apply_env_primary()

    def _load_builtin(self) -> None:
        s = self.s
        primary_kind = (s.provider or "openai").lower()
        if primary_kind == "local":
            primary_kind = KIND_LOCAL

        if s.openai_api_key:
            self._providers.append(ProviderConfig(
                id="openai", name="OpenAI", kind=KIND_OPENAI,
                default_model=s.openai_model, api_key=s.openai_api_key,
                is_primary=primary_kind == KIND_OPENAI,
            ))
        else:
            self._providers.append(ProviderConfig(
                id="openai", name="OpenAI", kind=KIND_OPENAI,
                default_model=s.openai_model, api_key="",
                is_active=True, is_primary=primary_kind == KIND_OPENAI,
            ))
        if s.anthropic_api_key:
            self._providers.append(ProviderConfig(
                id="anthropic", name="Anthropic Claude", kind=KIND_ANTHROPIC,
                default_model=s.anthropic_model, api_key=s.anthropic_api_key,
                is_primary=primary_kind == KIND_ANTHROPIC,
            ))
        else:
            self._providers.append(ProviderConfig(
                id="anthropic", name="Anthropic Claude", kind=KIND_ANTHROPIC,
                default_model=s.anthropic_model, api_key="",
                is_active=True, is_primary=primary_kind == KIND_ANTHROPIC,
            ))
        local_url = getattr(s, "local_llm_base_url", None) or os.getenv(
            "LOCAL_LLM_BASE_URL", "http://localhost:11434/v1"
        )
        local_model = getattr(s, "local_llm_model", None) or os.getenv(
            "LOCAL_LLM_MODEL", "llama3.2"
        )
        local_key = getattr(s, "local_llm_api_key", None) or os.getenv(
            "LOCAL_LLM_API_KEY", "ollama"
        )
        self._providers.append(ProviderConfig(
            id="local", name="Local LLM (Ollama-compatible)", kind=KIND_LOCAL,
            base_url=local_url.rstrip("/"),
            default_model=local_model, api_key=local_key,
            is_primary=primary_kind in (KIND_LOCAL, "local"),
            config_json={"openai_compatible": True},
        ))

    def _load_file_overrides(self) -> None:
        if not PROVIDERS_FILE.exists():
            return
        try:
            data = json.loads(PROVIDERS_FILE.read_text(encoding="utf-8"))
            for item in data.get("providers", []):
                pid = item.get("id", "custom")
                existing = next((p for p in self._providers if p.id == pid), None)
                if existing:
                    for k, v in item.items():
                        if k == "api_key" and v:
                            existing.api_key = v
                        elif k == "base_url" and v:
                            existing.base_url = v
                        elif k == "default_model" and v:
                            existing.default_model = v
                        elif k == "is_active":
                            existing.is_active = bool(v)
                        elif k == "is_primary":
                            existing.is_primary = bool(v)
                else:
                    self._providers.append(ProviderConfig(
                        id=pid,
                        name=item.get("name", pid),
                        kind=item.get("kind", KIND_CUSTOM),
                        base_url=item.get("base_url"),
                        default_model=item.get("default_model", ""),
                        api_key=item.get("api_key", ""),
                        is_active=item.get("is_active", True),
                        is_primary=item.get("is_primary", False),
                        config_json=item.get("config_json") or {},
                    ))
        except Exception as exc:  # noqa: BLE001
            logger.warning("Gagal baca providers.json: %s", exc)

    def _apply_env_primary(self) -> None:
        forced = os.getenv("SOBATPAWS_AI_PROVIDER", "").strip().lower()
        if not forced:
            return
        kind = KIND_LOCAL if forced == "local" else forced
        for p in self._providers:
            p.is_primary = p.kind == kind or p.id == forced

    def list_providers(self, active_only: bool = True) -> list[dict[str, Any]]:
        out = []
        for p in self._providers:
            if active_only and not p.is_active:
                continue
            out.append({
                "id": p.id,
                "name": p.name,
                "kind": p.kind,
                "default_model": p.default_model,
                "base_url": p.base_url,
                "is_active": p.is_active,
                "is_primary": p.is_primary,
                "available": p.available(),
                "has_api_key": bool(p.api_key),
            })
        return out

    def get_primary(self) -> ProviderConfig | None:
        for p in self._providers:
            if p.is_primary and p.is_active and p.available():
                return p
        for p in self._providers:
            if p.is_active and p.available():
                return p
        return None

    def get_chain(self) -> list[ProviderConfig]:
        primary = self.get_primary()
        chain: list[ProviderConfig] = []
        if primary:
            chain.append(primary)
        for p in self._providers:
            if p.is_active and p.available() and p not in chain:
                chain.append(p)
        return chain

    def get(self, provider_id: str) -> ProviderConfig | None:
        return next((p for p in self._providers if p.id == provider_id), None)

    def set_primary(self, provider_id: str) -> ProviderConfig | None:
        p = self.get(provider_id)
        if not p:
            return None
        for x in self._providers:
            x.is_primary = x.id == provider_id
        self._persist()
        return p

    def upsert(self, cfg: dict[str, Any]) -> ProviderConfig:
        pid = cfg.get("id", "custom")
        p = self.get(pid)
        if p:
            p.name = cfg.get("name", p.name)
            p.kind = cfg.get("kind", p.kind)
            p.base_url = cfg.get("base_url", p.base_url)
            p.default_model = cfg.get("default_model", p.default_model)
            if cfg.get("api_key"):
                p.api_key = cfg["api_key"]
            p.is_active = cfg.get("is_active", p.is_active)
        else:
            p = ProviderConfig(
                id=pid,
                name=cfg.get("name", pid),
                kind=cfg.get("kind", KIND_CUSTOM),
                base_url=cfg.get("base_url"),
                default_model=cfg.get("default_model", ""),
                api_key=cfg.get("api_key", ""),
                is_active=cfg.get("is_active", True),
            )
            self._providers.append(p)
        self._persist()
        return p

    def _persist(self) -> None:
        PROVIDERS_FILE.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "providers": [
                {
                    "id": p.id, "name": p.name, "kind": p.kind,
                    "base_url": p.base_url, "default_model": p.default_model,
                    "is_active": p.is_active, "is_primary": p.is_primary,
                    # api_key tidak disimpan ke file demi keamanan
                }
                for p in self._providers
                if p.id not in ("openai", "anthropic") or p.base_url
            ],
        }
        PROVIDERS_FILE.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )


_registry: ProviderRegistry | None = None


def get_provider_registry() -> ProviderRegistry:
    global _registry
    if _registry is None:
        _registry = ProviderRegistry()
    return _registry
