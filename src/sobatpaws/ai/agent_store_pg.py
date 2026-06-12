"""Backend PostgreSQL untuk AgentStore (mirror ke tabel DBML bila tersedia)."""
from __future__ import annotations

import json
import logging
from typing import Any

from ..config import DATABASE_URL

logger = logging.getLogger("sobatpaws.ai.agent_store.pg")

_CREATE_SQL = """
CREATE TABLE IF NOT EXISTS ai_agent_events (
  id              TEXT PRIMARY KEY,
  kind            TEXT NOT NULL,
  consultation_id TEXT NOT NULL,
  payload         JSONB NOT NULL,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_ai_agent_events_consultation
  ON ai_agent_events (consultation_id);
CREATE INDEX IF NOT EXISTS idx_ai_agent_events_kind
  ON ai_agent_events (kind);
"""


class PostgresAgentBackend:
    def __init__(self, database_url: str | None = None):
        self.url = database_url or DATABASE_URL
        self._engine = None
        self._ready = False

    @property
    def available(self) -> bool:
        if self._ready:
            return True
        try:
            self._connect()
            return self._ready
        except Exception:  # noqa: BLE001
            return False

    def _connect(self) -> None:
        if self._engine is not None:
            return
        from sqlalchemy import create_engine, text

        self._engine = create_engine(
            self.url, pool_pre_ping=True, connect_args={"connect_timeout": 3}
        )
        with self._engine.begin() as conn:
            conn.execute(text(_CREATE_SQL))
        self._ready = True

    def append(self, kind: str, record: dict[str, Any]) -> None:
        if not self.available:
            return
        from sqlalchemy import text

        cid = record.get("consultation_id", "")
        payload = {k: v for k, v in record.items()}
        with self._engine.begin() as conn:  # type: ignore[union-attr]
            conn.execute(
                text("""
                    INSERT INTO ai_agent_events (id, kind, consultation_id, payload, created_at)
                    VALUES (:id, :kind, :cid, CAST(:payload AS jsonb),
                            COALESCE(:ts::timestamptz, now()))
                    ON CONFLICT (id) DO NOTHING
                """),
                {
                    "id": record["id"],
                    "kind": kind,
                    "cid": cid,
                    "payload": json.dumps(payload, ensure_ascii=False, default=str),
                    "ts": record.get("created_at"),
                },
            )
