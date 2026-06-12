"""Backend PostgreSQL untuk LearningStore (tabel learning_events).

Menyimpan event konsultasi ke PostgreSQL selain (atau menggantikan) JSONL lokal.
Degradasi anggun: bila DB tidak tersedia, operasi di-skip tanpa memblokir alur.
"""
from __future__ import annotations

import json
import logging
from typing import Any

from ..config import DATABASE_URL

logger = logging.getLogger("sobatpaws.ai.store.pg")

_CREATE_SQL = """
CREATE TABLE IF NOT EXISTS learning_events (
  id              TEXT PRIMARY KEY,
  consultation_id TEXT NOT NULL,
  kind            TEXT NOT NULL,
  payload         JSONB NOT NULL,
  recorded_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_learning_events_consultation
  ON learning_events (consultation_id);
CREATE INDEX IF NOT EXISTS idx_learning_events_kind
  ON learning_events (kind);
"""


class PostgresLearningBackend:
    """Penulis/pembaca event ke tabel learning_events."""

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
        logger.info("PostgreSQL learning backend siap (%s)", self._mask_url())

    def append(self, kind: str, record: dict[str, Any]) -> None:
        if not self.available:
            return
        from sqlalchemy import text

        cid = record.get("consultation_id", "")
        payload = {k: v for k, v in record.items() if k != "consultation_id"}
        with self._engine.begin() as conn:  # type: ignore[union-attr]
            conn.execute(
                text("""
                    INSERT INTO learning_events (id, consultation_id, kind, payload, recorded_at)
                    VALUES (:id, :cid, :kind, CAST(:payload AS jsonb), COALESCE(:ts::timestamptz, now()))
                    ON CONFLICT (id) DO NOTHING
                """),
                {
                    "id": record["id"],
                    "cid": cid,
                    "kind": kind,
                    "payload": json.dumps(payload, ensure_ascii=False, default=str),
                    "ts": record.get("recorded_at"),
                },
            )

    def read(self, kind: str) -> list[dict]:
        if not self.available:
            return []
        from sqlalchemy import text

        with self._engine.connect() as conn:  # type: ignore[union-attr]
            rows = conn.execute(
                text("""
                    SELECT payload, consultation_id, id, kind, recorded_at
                    FROM learning_events WHERE kind = :kind
                    ORDER BY recorded_at
                """),
                {"kind": kind},
            ).mappings().all()
        out: list[dict] = []
        for r in rows:
            rec = dict(r["payload"]) if isinstance(r["payload"], dict) else json.loads(r["payload"])
            rec.setdefault("id", r["id"])
            rec.setdefault("kind", r["kind"])
            rec.setdefault("consultation_id", r["consultation_id"])
            rec.setdefault("recorded_at", str(r["recorded_at"]))
            out.append(rec)
        return out

    def stats(self) -> dict[str, int]:
        if not self.available:
            return {}
        from sqlalchemy import text

        with self._engine.connect() as conn:  # type: ignore[union-attr]
            rows = conn.execute(
                text("SELECT kind, COUNT(*) AS n FROM learning_events GROUP BY kind")
            ).mappings().all()
        return {r["kind"]: int(r["n"]) for r in rows}

    @staticmethod
    def _mask_url(url: str) -> str:
        if "@" in url:
            scheme_creds, _, host = url.partition("@")
            scheme = scheme_creds.split("//", 1)[0]
            return f"{scheme}//***@{host}"
        return url
