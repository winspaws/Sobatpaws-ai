"""Klien LLM multi-provider: OpenAI, Anthropic, lokal (Ollama-compatible), custom."""
from __future__ import annotations

import base64
import json
import logging
from typing import Any

from ..config import AISettings
from .cache import get_llm_cache
from .providers import KIND_ANTHROPIC, KIND_LOCAL, KIND_OPENAI, ProviderConfig, get_provider_registry
from .telemetry import AITelemetry, LLMUsageRecord, estimate_cost, get_telemetry, timed_call

logger = logging.getLogger("ekosistem_satwa.ai.llm")


class LLMClient:
    """Wrapper provider-agnostic dengan fallback registry & telemetry."""

    def __init__(
        self,
        settings: AISettings | None = None,
        telemetry: AITelemetry | None = None,
        provider: ProviderConfig | None = None,
    ):
        self.s = settings or AISettings()
        self.telemetry = telemetry or get_telemetry()
        self.cache = get_llm_cache()
        self._provider_cfg = provider or get_provider_registry().get_primary()
        if self._provider_cfg:
            self.provider = self._provider_cfg.kind
            if self._provider_cfg.kind == KIND_OPENAI:
                self.provider = "openai"
            elif self._provider_cfg.kind == KIND_ANTHROPIC:
                self.provider = "anthropic"
            elif self._provider_cfg.kind == KIND_LOCAL:
                self.provider = "local"
            else:
                self.provider = self._provider_cfg.id
        else:
            self.provider = (self.s.provider or "openai").lower()

    @classmethod
    def for_provider(cls, cfg: ProviderConfig) -> LLMClient:
        return LLMClient(provider=cfg)

    @property
    def model(self) -> str:
        if self._provider_cfg and self._provider_cfg.default_model:
            return self._provider_cfg.default_model
        if self.provider == "anthropic":
            return self.s.anthropic_model
        if self.provider == "local":
            return self.s.local_llm_model
        return self.s.openai_model

    @property
    def available(self) -> bool:
        if self._provider_cfg:
            return self._provider_cfg.available()
        if self.provider == "openai":
            return bool(self.s.openai_api_key)
        if self.provider == "anthropic":
            return bool(self.s.anthropic_api_key)
        if self.provider == "local":
            return bool(self.s.local_llm_base_url)
        return False

    def chat_json(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        max_tokens: int | None = None,
        operation: str = "chat_json",
        consultation_id: str | None = None,
        org_id: int | None = None,
    ) -> dict[str, Any] | None:
        if not self.available:
            return None
        max_tokens = max_tokens or self.s.max_tokens

        cached = self.cache.get(self.provider, self.model, operation, system_prompt, user_prompt)
        if cached is not None:
            self.telemetry.record_cache_hit(
                operation, provider=self.provider, model=self.model,
                consultation_id=consultation_id, org_id=org_id,
            )
            return cached

        ok, reason = self.telemetry.can_spend(max_tokens)
        if not ok:
            self.telemetry.record_skip(
                operation, reason or "budget", provider=self.provider, model=self.model,
                consultation_id=consultation_id, org_id=org_id,
            )
            return None

        with timed_call() as t:
            try:
                raw, usage = self._dispatch_chat(system_prompt, user_prompt, max_tokens)
            except Exception as exc:  # noqa: BLE001
                logger.warning("LLM chat gagal (%s): %s", self.provider, exc)
                self.telemetry.record(LLMUsageRecord(
                    operation=operation, provider=self.provider, model=self.model,
                    status="failed", latency_ms=t.latency_ms,
                    consultation_id=consultation_id, org_id=org_id,
                ))
                return None

        parsed = _safe_json(raw)
        if parsed is not None:
            self.cache.set(self.provider, self.model, operation, parsed, system_prompt, user_prompt)

        pt = usage.get("prompt_tokens", 0)
        ct = usage.get("completion_tokens", 0)
        self.telemetry.record(LLMUsageRecord(
            operation=operation, provider=self.provider, model=self.model,
            prompt_tokens=pt, completion_tokens=ct, total_tokens=pt + ct,
            cost_usd=estimate_cost(self.model, pt, ct),
            latency_ms=t.latency_ms, consultation_id=consultation_id, org_id=org_id,
        ))
        return parsed

    def _dispatch_chat(self, system: str, user: str, max_tokens: int) -> tuple[str, dict]:
        cfg = self._provider_cfg
        kind = cfg.kind if cfg else self.provider

        if kind == KIND_ANTHROPIC or self.provider == "anthropic":
            return self._anthropic_chat(system, user, max_tokens)
        if kind == KIND_LOCAL or self.provider == "local":
            return self._openai_compatible_chat(system, user, max_tokens, use_json=True)
        if cfg and cfg.base_url:
            return self._openai_compatible_chat(system, user, max_tokens, use_json=True)
        return self._openai_chat(system, user, max_tokens)

    def _openai_compatible_chat(
        self, system: str, user: str, max_tokens: int, use_json: bool = True,
    ) -> tuple[str, dict]:
        from openai import OpenAI

        cfg = self._provider_cfg
        base_url = (cfg.base_url if cfg else None) or self.s.local_llm_base_url
        api_key = (cfg.api_key if cfg else None) or self.s.local_llm_api_key or "ollama"
        model = self.model

        client = OpenAI(api_key=api_key, base_url=base_url.rstrip("/"))
        kwargs: dict[str, Any] = {
            "model": model,
            "temperature": self.s.temperature,
            "max_tokens": max_tokens,
            "messages": [
                {"role": "system", "content": system + "\nJawab JSON valid saja."},
                {"role": "user", "content": user},
            ],
        }
        if use_json:
            kwargs["response_format"] = {"type": "json_object"}
        resp = client.chat.completions.create(**kwargs)
        usage = resp.usage
        return resp.choices[0].message.content or "", {
            "prompt_tokens": getattr(usage, "prompt_tokens", 0) or 0,
            "completion_tokens": getattr(usage, "completion_tokens", 0) or 0,
        }

    def _openai_chat(self, system: str, user: str, max_tokens: int) -> tuple[str, dict]:
        from openai import OpenAI

        api_key = (
            self._provider_cfg.api_key if self._provider_cfg and self._provider_cfg.api_key
            else self.s.openai_api_key
        )
        client = OpenAI(api_key=api_key)
        resp = client.chat.completions.create(
            model=self.model,
            temperature=self.s.temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        usage = resp.usage
        return resp.choices[0].message.content or "", {
            "prompt_tokens": getattr(usage, "prompt_tokens", 0) or 0,
            "completion_tokens": getattr(usage, "completion_tokens", 0) or 0,
        }

    def _anthropic_chat(self, system: str, user: str, max_tokens: int) -> tuple[str, dict]:
        import anthropic

        api_key = (
            self._provider_cfg.api_key if self._provider_cfg and self._provider_cfg.api_key
            else self.s.anthropic_api_key
        )
        client = anthropic.Anthropic(api_key=api_key)
        msg = client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=self.s.temperature,
            system=system + "\n\nWAJIB jawab dalam satu objek JSON valid.",
            messages=[{"role": "user", "content": user}],
        )
        text = "".join(
            block.text for block in msg.content if getattr(block, "type", "") == "text"
        )
        usage = msg.usage
        return text, {
            "prompt_tokens": getattr(usage, "input_tokens", 0) or 0,
            "completion_tokens": getattr(usage, "output_tokens", 0) or 0,
        }

    def transcribe(
        self, audio_bytes: bytes, mime_type: str | None = None, **ctx
    ) -> str | None:
        if not self.s.openai_api_key:
            return None
        cache_key = base64.b64encode(audio_bytes[:4096]).decode("ascii")
        cached = self.cache.get("openai", "whisper-1", "transcribe", cache_key)
        if cached:
            self.telemetry.record_cache_hit("transcribe", provider="openai", model="whisper-1")
            return cached

        with timed_call() as t:
            try:
                import io
                from openai import OpenAI

                client = OpenAI(api_key=self.s.openai_api_key)
                buf = io.BytesIO(audio_bytes)
                buf.name = _filename_for_mime(mime_type)
                resp = client.audio.transcriptions.create(model="whisper-1", file=buf)
                text = getattr(resp, "text", None)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Transkripsi audio gagal: %s", exc)
                return None

        if text:
            self.cache.set("openai", "whisper-1", "transcribe", text, cache_key)
            est_tokens = max(len(text.split()) * 2, 100)
            self.telemetry.record(LLMUsageRecord(
                operation="transcribe", provider="openai", model="whisper-1",
                prompt_tokens=est_tokens, completion_tokens=len(text.split()),
                total_tokens=est_tokens + len(text.split()),
                cost_usd=estimate_cost("whisper-1", est_tokens, 0),
                latency_ms=t.latency_ms,
            ))
        return text

    def describe_image(
        self,
        image_bytes: bytes,
        mime_type: str | None = None,
        *,
        prompt: str | None = None,
        structured: bool = False,
        **ctx,
    ) -> str | dict[str, Any] | None:
        """Describe an image, optionally returning structured JSON output.

        Args:
            image_bytes: Raw image data
            mime_type: MIME type of the image
            prompt: Optional custom prompt (overrides default)
            structured: If True, request and parse structured JSON output.
                Returns dict matching StructuredVisionOutput schema.
                If False (default), returns plain text description.
            **ctx: Additional context for telemetry

        Returns:
            For structured=False: str | None - plain text description
            For structured=True: dict | None - parsed JSON if valid,
                falls back to text string if JSON parsing fails,
                None on error
        """
        if not self.available:
            return None
        mime = mime_type or "image/jpeg"
        b64 = base64.b64encode(image_bytes).decode("ascii")

        if structured:
            return self._describe_image_structured(b64, mime, prompt=prompt, **ctx)

        # Text-only mode (original behavior)
        prompt = prompt or (
            "Deskripsikan temuan klinis TERLIHAT pada gambar hewan (lokasi, lesi, luka, "
            "bengkak). Objektif saja, Bahasa Indonesia, maks 120 kata."
        )
        cached = self.cache.get(self.provider, self.model, "vision", b64[:256], prompt)
        if cached:
            self.telemetry.record_cache_hit("vision", provider=self.provider, model=self.model)
            return cached

        with timed_call() as t:
            try:
                if self.provider == "anthropic":
                    text, usage = self._anthropic_vision(b64, mime, prompt)
                else:
                    text, usage = self._openai_vision(b64, mime, prompt)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Analisa gambar gagal: %s", exc)
                return None

        if text:
            self.cache.set(self.provider, self.model, "vision", text, b64[:256], prompt)
            pt = usage.get("prompt_tokens", 500)
            ct = usage.get("completion_tokens", len(text.split()))
            self.telemetry.record(LLMUsageRecord(
                operation="vision", provider=self.provider, model=self.model,
                prompt_tokens=pt, completion_tokens=ct, total_tokens=pt + ct,
                cost_usd=estimate_cost(self.model, pt, ct), latency_ms=t.latency_ms,
            ))
        return text

    def _describe_image_structured(
        self, b64: str, mime: str, *, prompt: str | None = None, **ctx
    ) -> dict[str, Any] | str | None:
        """Internal: structured vision analysis with JSON output.

        Returns:
            - dict: Successfully parsed JSON matching StructuredVisionOutput
            - str: Fallback to text description if JSON parsing fails
            - None: On error
        """
        consultation_id = ctx.get("consultation_id")
        org_id = ctx.get("org_id")

        structured_prompt = prompt or """Analisa gambar hewan ini secara klinis untuk dokter hewan.
Output JSON VALID SAJA (no markdown, no explanation, no code blocks).

Field yang harus ada dalam JSON:
- species_detected: salah satu dari [dog, cat, rabbit, hamster, poultry, fish, reptile, amphibian, ferret, guinea_pig] atau null
- breed_hints: list string kemiripan ras (maks 3, bisa kosong array)
- age_estimate_min_years: angka atau null
- age_estimate_max_years: angka atau null
- age_confidence: float 0.0-1.0
- lesions: list of objects, masing-masing dengan:
    location (string lokasi anatomis),
    type (string jenis lesi),
    severity (string: "mild" | "moderate" | "severe"),
    description (string deskripsi detail),
    confidence (float 0.0-1.0, opsional default 0.8)
- red_flags: list string tanda darurat (pale_mucosa, respiratory_distress, active_bleeding, seizures, trauma_parah)
- extracted_symptoms: list string gejala yang terlihat (gunakan istilah medis umum yang sesuai)
- raw_description: deskripsi natural lengkap dalam Bahasa Indonesia (seolah menjelaskan ke dokter)

Pastikan semua field ada. Jika tidak yakin, isi dengan null atau array kosong."""

        cache_key = f"structured:{b64[:200]}"
        cached = self.cache.get(self.provider, self.model, "vision_structured", cache_key)
        if cached:
            self.telemetry.record_cache_hit(
                "vision_structured", provider=self.provider, model=self.model,
                consultation_id=consultation_id, org_id=org_id,
            )
            return cached

        with timed_call() as t:
            try:
                if self.provider == "anthropic":
                    raw_response, usage = self._anthropic_vision(b64, mime, structured_prompt)
                else:
                    raw_response, usage = self._openai_vision(b64, mime, structured_prompt)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Structured vision analysis failed: %s", exc)
                return None

        latency_ms = t.latency_ms

        if not raw_response:
            logger.warning("Empty response from structured vision")
            return None

        # Try to parse JSON
        parsed = _safe_json(raw_response)

        pt = usage.get("prompt_tokens", 700)
        ct = usage.get("completion_tokens", len(raw_response.split()))

        if parsed is not None:
            # Add processing time
            parsed["processing_time_ms"] = latency_ms
            self.cache.set(
                self.provider, self.model, "vision_structured", parsed, cache_key
            )
            self.telemetry.record(LLMUsageRecord(
                operation="vision_structured", provider=self.provider, model=self.model,
                prompt_tokens=pt, completion_tokens=ct, total_tokens=pt + ct,
                cost_usd=estimate_cost(self.model, pt, ct), latency_ms=latency_ms,
                consultation_id=consultation_id, org_id=org_id,
            ))
            return parsed

        # Fallback: return raw text if JSON parsing fails
        logger.warning(
            "Failed to parse structured vision response as JSON. "
            "First 200 chars: %s", raw_response[:200] if len(raw_response) > 200 else raw_response
        )
        self.telemetry.record(LLMUsageRecord(
            operation="vision_structured", provider=self.provider, model=self.model,
            prompt_tokens=pt, completion_tokens=ct, total_tokens=pt + ct,
            cost_usd=estimate_cost(self.model, pt, ct), latency_ms=latency_ms,
            consultation_id=consultation_id, org_id=org_id,
            status="partial",  # Got response but not valid JSON
        ))
        # Return as text fallback for backward compatibility
        return raw_response

    def _openai_vision(self, b64: str, mime: str, prompt: str) -> tuple[str, dict]:
        from openai import OpenAI

        api_key = self.s.openai_api_key
        base_url = None
        if self._provider_cfg and self._provider_cfg.base_url:
            api_key = self._provider_cfg.api_key or api_key
            base_url = self._provider_cfg.base_url.rstrip("/")
        client = OpenAI(api_key=api_key, base_url=base_url) if base_url else OpenAI(api_key=api_key)
        resp = client.chat.completions.create(
            model=self.model,
            max_tokens=min(self.s.max_tokens, 400),
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}},
                ],
            }],
        )
        usage = resp.usage
        return resp.choices[0].message.content or "", {
            "prompt_tokens": getattr(usage, "prompt_tokens", 500) or 500,
            "completion_tokens": getattr(usage, "completion_tokens", 0) or 0,
        }

    def _anthropic_vision(self, b64: str, mime: str, prompt: str) -> tuple[str, dict]:
        import anthropic

        client = anthropic.Anthropic(api_key=self.s.anthropic_api_key)
        msg = client.messages.create(
            model=self.model,
            max_tokens=min(self.s.max_tokens, 400),
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image", "source": {
                        "type": "base64", "media_type": mime, "data": b64}},
                ],
            }],
        )
        text = "".join(
            block.text for block in msg.content if getattr(block, "type", "") == "text"
        )
        usage = msg.usage
        return text, {
            "prompt_tokens": getattr(usage, "input_tokens", 500) or 500,
            "completion_tokens": getattr(usage, "output_tokens", 0) or 0,
        }


def _filename_for_mime(mime_type: str | None) -> str:
    mapping = {
        "audio/wav": "audio.wav", "audio/x-wav": "audio.wav",
        "audio/mpeg": "audio.mp3", "audio/mp3": "audio.mp3",
        "audio/mp4": "audio.mp4", "audio/m4a": "audio.m4a",
        "audio/webm": "audio.webm", "audio/ogg": "audio.ogg",
    }
    return mapping.get((mime_type or "").lower(), "audio.wav")


def _safe_json(raw: str) -> dict[str, Any] | None:
    if not raw:
        return None
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.strip("`")
        raw = raw[raw.find("{"):] if "{" in raw else raw
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        start, end = raw.find("{"), raw.rfind("}")
        if 0 <= start < end:
            try:
                return json.loads(raw[start:end + 1])
            except json.JSONDecodeError:
                return None
    return None
