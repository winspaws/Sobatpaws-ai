"""Observability LLM: token, biaya, latensi, budget harian, cache hit.

Log append-only ke `artifacts/learning/ai_requests.jsonl` (selaras skema ai_requests).
"""
from __future__ import annotations

import json
import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from ..config import AISettings, ARTIFACTS_DIR

# Perkiraan USD per 1K token (input/output) — perkiraan kasar untuk monitoring
COST_PER_1K: dict[str, dict[str, float]] = {
    "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
    "gpt-4o": {"input": 0.0025, "output": 0.01},
    "claude-3-5-sonnet-latest": {"input": 0.003, "output": 0.015},
    "whisper-1": {"input": 0.006, "output": 0.0},
}

LOG_PATH = ARTIFACTS_DIR / "learning" / "ai_requests.jsonl"


@dataclass
class LLMUsageRecord:
    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    operation: str = "chat_json"
    provider: str = ""
    model: str = ""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0
    latency_ms: int = 0
    status: str = "completed"
    cached: bool = False
    skipped: bool = False
    skip_reason: str | None = None
    consultation_id: str | None = None
    org_id: int | None = None
    recorded_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "kind": "ai_request",
            "operation": self.operation,
            "provider": self.provider,
            "model": self.model,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "cost_usd": round(self.cost_usd, 6),
            "latency_ms": self.latency_ms,
            "status": self.status,
            "cached": self.cached,
            "skipped": self.skipped,
            "skip_reason": self.skip_reason,
            "consultation_id": self.consultation_id,
            "org_id": self.org_id,
            "recorded_at": self.recorded_at,
        }


def estimate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    rates = COST_PER_1K.get(model, {"input": 0.001, "output": 0.002})
    return (prompt_tokens / 1000 * rates["input"]) + (completion_tokens / 1000 * rates["output"])


class AITelemetry:
    """Thread-safe tracker + persist JSONL."""

    def __init__(self, log_path: Path | None = None):
        self.log_path = log_path or LOG_PATH
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._today = date.today()
        self._daily_tokens = 0
        self._cache_hits = 0
        self._skipped = 0
        self._calls = 0

    def _roll_day(self) -> None:
        today = date.today()
        if today != self._today:
            self._today = today
            self._daily_tokens = 0

    def can_spend(self, estimated_tokens: int = 800) -> tuple[bool, str | None]:
        """Cek budget harian token (0 = unlimited)."""
        self._roll_day()
        budget = AISettings().daily_token_budget
        if budget <= 0:
            return True, None
        if self._daily_tokens + estimated_tokens > budget:
            return False, f"budget_harian_tercapai ({self._daily_tokens}/{budget} token)"
        return True, None

    def record(self, rec: LLMUsageRecord) -> dict[str, Any]:
        with self._lock:
            self._roll_day()
            if rec.skipped:
                self._skipped += 1
            elif rec.cached:
                self._cache_hits += 1
            else:
                self._calls += 1
                self._daily_tokens += rec.total_tokens
            line = json.dumps(rec.to_dict(), ensure_ascii=False)
            with self.log_path.open("a", encoding="utf-8") as fh:
                fh.write(line + "\n")
        return rec.to_dict()

    def record_skip(self, operation: str, reason: str, **ctx) -> dict:
        return self.record(LLMUsageRecord(
            operation=operation, status="skipped", skipped=True,
            skip_reason=reason, **{k: v for k, v in ctx.items() if k in LLMUsageRecord.__dataclass_fields__},
        ))

    def record_cache_hit(self, operation: str, **ctx) -> dict:
        return self.record(LLMUsageRecord(
            operation=operation, status="cached", cached=True, **ctx,
        ))

    def _read_all(self) -> list[dict]:
        if not self.log_path.exists():
            return []
        rows = []
        with self.log_path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    try:
                        rows.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        return rows

    def summary(self, limit_recent: int = 50) -> dict[str, Any]:
        rows = self._read_all()
        today_iso = date.today().isoformat()
        today_rows = [r for r in rows if r.get("recorded_at", "").startswith(today_iso)]
        total_tokens = sum(r.get("total_tokens", 0) for r in rows if not r.get("skipped"))
        today_tokens = sum(r.get("total_tokens", 0) for r in today_rows if not r.get("skipped"))
        total_cost = sum(r.get("cost_usd", 0) for r in rows)
        today_cost = sum(r.get("cost_usd", 0) for r in today_rows)
        cache_hits = sum(1 for r in rows if r.get("cached"))
        skipped = sum(1 for r in rows if r.get("skipped"))
        calls = sum(1 for r in rows if not r.get("cached") and not r.get("skipped"))
        budget = AISettings().daily_token_budget
        by_operation: dict[str, int] = {}
        for r in rows:
            if r.get("skipped"):
                continue
            op = r.get("operation", "unknown")
            by_operation[op] = by_operation.get(op, 0) + r.get("total_tokens", 0)

        return {
            "total_requests": len(rows),
            "llm_calls": calls,
            "cache_hits": cache_hits,
            "skipped": skipped,
            "cache_hit_rate": round(cache_hits / max(calls + cache_hits, 1), 4),
            "token_savings_skipped": skipped,
            "total_tokens": total_tokens,
            "total_cost_usd": round(total_cost, 4),
            "today_tokens": today_tokens,
            "today_cost_usd": round(today_cost, 4),
            "daily_budget": budget,
            "daily_budget_remaining": max(budget - today_tokens, 0) if budget > 0 else None,
            "by_operation": by_operation,
            "recent": rows[-limit_recent:][::-1],
            "settings": {
                "augmentation_mode": AISettings().augmentation_mode,
                "max_tokens": AISettings().max_tokens,
                "cache_ttl_sec": AISettings().cache_ttl_sec,
            },
        }


_telemetry: AITelemetry | None = None


def get_telemetry() -> AITelemetry:
    global _telemetry
    if _telemetry is None:
        _telemetry = AITelemetry()
    return _telemetry


class timed_call:
    """Context manager untuk mengukur latensi."""

    def __enter__(self):
        self.t0 = time.perf_counter()
        return self

    def __exit__(self, *args):
        self.latency_ms = int((time.perf_counter() - self.t0) * 1000)
