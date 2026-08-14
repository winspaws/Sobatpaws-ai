"""In-process rate limiter (no extra dependency).

Default: 120 request / menit / IP. Override via RATE_LIMIT_PER_MINUTE.
Path publik (health, docs, static) dilewati.
"""
from __future__ import annotations

import os
import time
from collections import defaultdict, deque
from threading import Lock

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

_EXEMPT_PREFIXES = (
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/web",
    "/favicon",
)


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, *, max_per_minute: int | None = None):
        super().__init__(app)
        self.max_per_minute = max_per_minute or int(os.getenv("RATE_LIMIT_PER_MINUTE", "120"))
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def _client_key(self, request: Request) -> str:
        forwarded = request.headers.get("x-forwarded-for", "")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    async def dispatch(self, request: Request, call_next):
        if self.max_per_minute <= 0:
            return await call_next(request)
        path = request.url.path
        if any(path == p or path.startswith(p + "/") for p in _EXEMPT_PREFIXES) or path.startswith("/web"):
            return await call_next(request)
        if path.endswith((".html", ".css", ".js", ".png", ".ico", ".svg")):
            return await call_next(request)

        key = self._client_key(request)
        now = time.monotonic()
        window = 60.0
        with self._lock:
            bucket = self._hits[key]
            while bucket and now - bucket[0] > window:
                bucket.popleft()
            if len(bucket) >= self.max_per_minute:
                retry = max(1, int(window - (now - bucket[0])))
                return JSONResponse(
                    status_code=429,
                    content={
                        "status": "rate_limited",
                        "detail": f"Terlalu banyak request. Maks {self.max_per_minute}/menit.",
                        "retry_after_sec": retry,
                    },
                    headers={"Retry-After": str(retry)},
                )
            bucket.append(now)
        return await call_next(request)
