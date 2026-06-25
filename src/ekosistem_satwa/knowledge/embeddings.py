"""Embedding service for RAG.

Uses OpenAI embeddings when available, with fallback to simple hash-based
embeddings for offline testing.
"""
from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field
from typing import Any

from ..config import AISettings

logger = logging.getLogger("ekosistem_satwa.knowledge.embeddings")

# Default embedding dimensions for OpenAI text-embedding-3-small
DEFAULT_EMBEDDING_DIM = 1536
# Fallback embedding dim when using hash-based
FALLBACK_EMBEDDING_DIM = 256


@dataclass
class EmbeddingResult:
    """Result of an embedding operation."""

    embedding: list[float]
    model: str
    tokens_used: int = 0
    from_cache: bool = False


class EmbeddingService:
    """Service for generating text embeddings.

    Primary: OpenAI text-embedding-3-small
    Fallback: Simple hash-based embeddings (for offline testing only)
    """

    def __init__(self, settings: AISettings | None = None):
        self.settings = settings or AISettings()
        self._openai_client: Any | None = None
        self._model = self._determine_model()
        self._dimensions = DEFAULT_EMBEDDING_DIM
        self._cache: dict[str, EmbeddingResult] = {}

    def _determine_model(self) -> str:
        # Check if local Ollama is configured with embedding model
        if self.settings.provider == "local" and self.settings.local_llm_base_url:
            # Could use nomic-embed-text or similar via Ollama
            return "local-embedding"
        return "text-embedding-3-small"

    @property
    def available(self) -> bool:
        """Check if real embeddings are available."""
        return bool(self.settings.openai_api_key) or bool(
            self.settings.local_llm_base_url
            and self.settings.provider == "local"
        )

    @property
    def dimensions(self) -> int:
        return self._dimensions

    def embed(self, text: str) -> EmbeddingResult:
        """Generate embedding for a single text string.

        Uses cached result if available. Falls back to hash-based
        embeddings when API is unavailable.
        """
        # Check cache first
        cache_key = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
        if cache_key in self._cache:
            return EmbeddingResult(
                embedding=self._cache[cache_key].embedding,
                model=self._cache[cache_key].model,
                tokens_used=0,
                from_cache=True,
            )

        # Try OpenAI embeddings first
        if self.settings.openai_api_key:
            result = self._embed_openai(text)
            if result:
                self._cache[cache_key] = result
                return result

        # Try local/Ollama embeddings
        if self.settings.local_llm_base_url and self.settings.provider == "local":
            result = self._embed_local(text)
            if result:
                self._cache[cache_key] = result
                return result

        # Fallback to hash-based (for testing only)
        result = self._embed_fallback(text)
        self._cache[cache_key] = result
        return result

    def embed_batch(self, texts: list[str]) -> list[EmbeddingResult]:
        """Generate embeddings for multiple texts."""
        return [self.embed(text) for text in texts]

    def _embed_openai(self, text: str) -> EmbeddingResult | None:
        """Generate embedding using OpenAI API."""
        try:
            from openai import OpenAI

            if self._openai_client is None:
                self._openai_client = OpenAI(api_key=self.settings.openai_api_key)

            response = self._openai_client.embeddings.create(
                input=text,
                model="text-embedding-3-small",
            )

            embedding = response.data[0].embedding
            tokens = response.usage.total_tokens if response.usage else 0
            self._dimensions = len(embedding)

            return EmbeddingResult(
                embedding=embedding,
                model="text-embedding-3-small",
                tokens_used=tokens,
            )
        except Exception as exc:
            logger.warning("OpenAI embedding failed: %s", exc)
            return None

    def _embed_local(self, text: str) -> EmbeddingResult | None:
        """Generate embedding using local/Ollama API."""
        try:
            from openai import OpenAI

            if self._openai_client is None:
                self._openai_client = OpenAI(
                    base_url=self.settings.local_llm_base_url.rstrip("/"),
                    api_key=self.settings.local_llm_api_key or "ollama",
                )

            # Use nomic-embed-text or similar for Ollama
            # Fall back to hash if embedding model not available
            try:
                response = self._openai_client.embeddings.create(
                    input=text,
                    model="nomic-embed-text",  # Common Ollama embedding model
                )
                embedding = response.data[0].embedding
                tokens = response.usage.total_tokens if response.usage else 0
                self._dimensions = len(embedding)

                return EmbeddingResult(
                    embedding=embedding,
                    model="nomic-embed-text",
                    tokens_used=tokens,
                )
            except Exception:
                # Fall through to fallback
                pass
        except Exception as exc:
            logger.debug("Local embedding not available: %s", exc)

        return None

    def _embed_fallback(self, text: str) -> EmbeddingResult:
        """Generate deterministic hash-based embedding for offline testing.

        NOT suitable for production use - only for testing the RAG pipeline.
        Creates a deterministic embedding based on word hashes.
        """
        import math

        words = text.lower().split()
        embedding = [0.0] * FALLBACK_EMBEDDING_DIM

        for word in words:
            # Hash word to a position and value
            h = hashlib.md5(word.encode("utf-8")).hexdigest()
            # Use first 8 hex chars for position
            pos = int(h[:8], 16) % FALLBACK_EMBEDDING_DIM
            # Use next 4 for sign and magnitude
            sign = 1 if int(h[8], 16) < 8 else -1
            mag = (int(h[9:12], 16) / 4095.0) * 0.5 + 0.01

            # Spread to nearby positions with decay
            for offset in range(-3, 4):
                idx = (pos + offset) % FALLBACK_EMBEDDING_DIM
                decay = 1.0 - (abs(offset) * 0.2)
                embedding[idx] += sign * mag * decay

        # Normalize to unit length
        norm = math.sqrt(sum(x * x for x in embedding))
        if norm > 0:
            embedding = [x / norm for x in embedding]

        self._dimensions = FALLBACK_EMBEDDING_DIM

        return EmbeddingResult(
            embedding=embedding,
            model="hash-fallback",
            tokens_used=0,
        )
