"""Cache respons LLM in-memory dengan TTL — hemat token untuk input identik."""
from __future__ import annotations

import hashlib
import threading
import time
from typing import Any

from ..config import AISettings


class LLMCache:
    def __init__(self, ttl_sec: int | None = None, max_entries: int = 512):
        self.ttl = ttl_sec if ttl_sec is not None else AISettings().cache_ttl_sec
        self.max_entries = max_entries
        self._store: dict[str, tuple[float, Any]] = {}
        self._lock = threading.Lock()

    def _key(self, provider: str, model: str, operation: str, *parts: str) -> str:
        raw = "|".join([provider, model, operation, *parts])
        return hashlib.sha256(raw.encode()).hexdigest()

    def get(self, provider: str, model: str, operation: str, *parts: str) -> Any | None:
        if self.ttl <= 0:
            return None
        k = self._key(provider, model, operation, *parts)
        with self._lock:
            item = self._store.get(k)
            if not item:
                return None
            ts, val = item
            if time.time() - ts > self.ttl:
                del self._store[k]
                return None
            return val

    def set(self, provider: str, model: str, operation: str, value: Any, *parts: str) -> None:
        if self.ttl <= 0:
            return
        k = self._key(provider, model, operation, *parts)
        with self._lock:
            if len(self._store) >= self.max_entries:
                oldest = min(self._store, key=lambda x: self._store[x][0])
                del self._store[oldest]
            self._store[k] = (time.time(), value)

    def stats(self) -> dict:
        with self._lock:
            return {"entries": len(self._store), "ttl_sec": self.ttl, "max_entries": self.max_entries}


_cache: LLMCache | None = None


def get_llm_cache() -> LLMCache:
    global _cache
    if _cache is None:
        _cache = LLMCache()
    return _cache
