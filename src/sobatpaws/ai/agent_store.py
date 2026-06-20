"""Penyimpanan agent AI: konsultasi, request LLM, saran, feedback, pesan chat."""
from __future__ import annotations

import json
import logging
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..config import ARTIFACTS_DIR, AI_STORE_BACKEND
from .schemas import AISuggestion, ConsultationContext, DoctorInput, SuggestionFeedback

logger = logging.getLogger("sobatpaws.ai.agent_store")

AI_DIR = ARTIFACTS_DIR / "ai"

FILES = {
    "conversation": "conversations.jsonl",
    "request": "requests.jsonl",
    "suggestion": "suggestions.jsonl",
    "feedback": "feedback.jsonl",
    "message": "messages.jsonl",
    "doctor_input": "doctor_inputs.jsonl",
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class AgentStore:
    """JSONL append-only (+ opsional PostgreSQL) untuk siklus agent AI."""

    def __init__(self, base_dir: Path | None = None, backend: str | None = None):
        self.base_dir = base_dir or AI_DIR
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.backend = (backend or AI_STORE_BACKEND or "jsonl").lower()
        self._lock = threading.Lock()
        self._pg = None
        if self.backend in ("postgres", "both", "pg"):
            try:
                from .agent_store_pg import PostgresAgentBackend
                self._pg = PostgresAgentBackend()
            except Exception as exc:  # noqa: BLE001
                logger.warning("PG agent backend tidak tersedia: %s", exc)

    @property
    def pg_available(self) -> bool:
        return self._pg is not None and self._pg.available

    def _append(self, kind: str, record: dict[str, Any]) -> dict[str, Any]:
        record.setdefault("id", uuid.uuid4().hex)
        record.setdefault("created_at", _now_iso())
        with self._lock:
            if self.backend in ("jsonl", "both", "file", ""):
                path = self.base_dir / FILES.get(kind, f"{kind}.jsonl")
                with open(path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
            if self._pg and self.backend in ("postgres", "both", "pg"):
                self._pg.append(kind, record)
        return record

    def _read(self, kind: str, limit: int = 500) -> list[dict[str, Any]]:
        path = self.base_dir / FILES.get(kind, f"{kind}.jsonl")
        if not path.exists():
            return []
        rows: list[dict[str, Any]] = []
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    rows.append(json.loads(line))
        rows.reverse()
        return rows[:limit]

    def create_conversation(
        self,
        consultation_id: str,
        context: ConsultationContext,
        title: str | None = None,
    ) -> dict[str, Any]:
        return self._append("conversation", {
            "consultation_id": consultation_id,
            "org_id": context.org_id,
            "user_id": context.user_id,
            "vet_id": context.vet_id,
            "owner_id": context.owner_id,
            "customer_id": context.customer_id,
            "pet_id": context.pet_id,
            "case_id": context.case_id,
            "external_consultation_id": context.external_consultation_id,
            "external_refs": context.external_refs,
            "title": title or f"Konsultasi {consultation_id[:8]}",
            "context": context.model_dump(mode="json"),
        })

    def log_request(
        self,
        consultation_id: str,
        provider_id: str,
        model: str,
        operation: str,
        status: str,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        cost_usd: float = 0.0,
        latency_ms: int = 0,
        request_payload: dict | None = None,
        response_payload: dict | None = None,
        error_message: str | None = None,
    ) -> dict[str, Any]:
        return self._append("request", {
            "consultation_id": consultation_id,
            "provider_id": provider_id,
            "model": model,
            "operation": operation,
            "status": status,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
            "cost_usd": cost_usd,
            "latency_ms": latency_ms,
            "request_payload": request_payload or {},
            "response_payload": response_payload,
            "error_message": error_message,
        })

    def save_suggestion(
        self,
        consultation_id: str,
        suggestion: AISuggestion,
        request_id: str | None = None,
        case_id: int | None = None,
        pet_id: int | None = None,
    ) -> dict[str, Any]:
        sug_ref = suggestion.model_dump(mode="json")
        rec = self._append("suggestion", {
            "consultation_id": consultation_id,
            "request_id": request_id,
            "case_id": case_id,
            "pet_id": pet_id,
            "suggestion_type": suggestion.suggestion_type,
            "summary": suggestion.summary,
            "is_emergency": suggestion.is_emergency,
            "is_reviewed": False,
            "generated_by": suggestion.generated_by,
            "payload": sug_ref,
        })
        rec["suggestion_ref"] = rec["id"]
        return rec

    def save_doctor_input(self, doctor_input: DoctorInput) -> dict[str, Any]:
        return self._append("doctor_input", doctor_input.model_dump(mode="json"))

    def save_feedback(
        self,
        feedback: SuggestionFeedback,
        ai_suggestion_id: str | None = None,
    ) -> dict[str, Any]:
        data = feedback.model_dump(mode="json")
        data["ai_suggestion_id"] = ai_suggestion_id or feedback.suggestion_ref
        return self._append("feedback", data)

    def add_message(
        self,
        consultation_id: str,
        role: str,
        content: str,
        meta: dict | None = None,
    ) -> dict[str, Any]:
        return self._append("message", {
            "consultation_id": consultation_id,
            "role": role,
            "content": content,
            "meta": meta or {},
        })

    def get_conversation(self, consultation_id: str) -> dict | None:
        for row in self._read("conversation", limit=10000):
            if row.get("consultation_id") == consultation_id:
                return row
        return None

    def list_suggestions(
        self,
        consultation_id: str | None = None,
        reviewed: bool | None = None,
        limit: int = 50,
    ) -> list[dict]:
        rows = self._read("suggestion", limit=10000)
        out = []
        for r in rows:
            if consultation_id and r.get("consultation_id") != consultation_id:
                continue
            if reviewed is not None and r.get("is_reviewed") != reviewed:
                continue
            out.append(r)
            if len(out) >= limit:
                break
        return out

    def get_suggestion(self, suggestion_id: str) -> dict | None:
        for r in self._read("suggestion", limit=10000):
            if r.get("id") == suggestion_id:
                return r
        return None

    def review_suggestion(
        self, suggestion_id: str, reviewed: bool = True, note: str | None = None,
    ) -> dict | None:
        # JSONL: append review event (immutable log)
        sug = self.get_suggestion(suggestion_id)
        if not sug:
            return None
        return self._append("suggestion", {
            **{k: v for k, v in sug.items() if k != "id"},
            "id": suggestion_id,
            "is_reviewed": reviewed,
            "review_note": note,
            "reviewed_at": _now_iso(),
            "_event": "review_update",
        })

    def list_messages(self, consultation_id: str, limit: int = 100) -> list[dict]:
        rows = self._read("message", limit=10000)
        msgs = [r for r in rows if r.get("consultation_id") == consultation_id]
        msgs.sort(key=lambda x: x.get("created_at", ""))
        return msgs[-limit:]

    def list_conversations(self, limit: int = 30) -> list[dict]:
        return self._read("conversation", limit=limit)

    def stats(self) -> dict[str, int]:
        counts = {}
        for kind, fname in FILES.items():
            path = self.base_dir / fname
            if path.exists():
                with open(path, encoding="utf-8") as f:
                    counts[kind] = sum(1 for _ in f)
            else:
                counts[kind] = 0
        return counts

    def backend_info(self) -> dict:
        return {
            "backend": self.backend,
            "pg_available": self.pg_available,
            "directory": str(self.base_dir),
        }


def rec_id_placeholder() -> str:
    return uuid.uuid4().hex


_store_singleton: AgentStore | None = None


def get_agent_store() -> AgentStore:
    global _store_singleton
    if _store_singleton is None:
        _store_singleton = AgentStore()
    return _store_singleton
