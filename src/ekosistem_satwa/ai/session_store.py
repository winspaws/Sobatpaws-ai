"""Persistent session store untuk ConsultationState.

Menggantikan dictionary in-memory `ConsultationService._sessions` dengan
penyimpanan persisten yang bertahan saat server restart.

Backend penyimpanan:
- Default: JSONL + in-memory cache di `artifacts/sessions/`
- Opsional: PostgreSQL via `ai_sessions` table
- Dual-write: `both` untuk menulis ke keduanya
"""
from __future__ import annotations

import json
import logging
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..config import ARTIFACTS_DIR, SESSION_STORE_BACKEND

logger = logging.getLogger("ekosistem_satwa.ai.session_store")

SESSIONS_DIR = ARTIFACTS_DIR / "sessions"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _serialize_state(state_dict: dict[str, Any]) -> dict[str, Any]:
    """Serialize ConsultationState components for JSON storage.

    Handles Pydantic models by converting them to dict.
    """
    out: dict[str, Any] = {}
    for key, value in state_dict.items():
        if hasattr(value, "model_dump"):
            # Pydantic v2 model
            out[key] = value.model_dump(mode="json")
        elif isinstance(value, list):
            out[key] = [
                v.model_dump(mode="json") if hasattr(v, "model_dump") else v
                for v in value
            ]
        else:
            out[key] = value
    return out


def _deserialize_state(data: dict[str, Any]) -> dict[str, Any]:
    """Deserialize stored state back into Python objects.

    Note: Pydantic model reconstruction is done by the caller (ConsultationService)
    because this module shouldn't import consultation.py (circular dependency).
    """
    return dict(data)


class PostgresSessionBackend:
    """PostgreSQL backend untuk SessionStore (tabel ai_sessions)."""

    _CREATE_SQL = """
CREATE TABLE IF NOT EXISTS ai_sessions (
  consultation_id TEXT PRIMARY KEY,
  state_data JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_ai_sessions_created
  ON ai_sessions (created_at);
CREATE INDEX IF NOT EXISTS idx_ai_sessions_updated
  ON ai_sessions (updated_at);
"""

    def __init__(self, database_url: str | None = None):
        from ..config import DATABASE_URL

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
            conn.execute(text(self._CREATE_SQL))
        self._ready = True
        logger.info("PostgreSQL session backend siap (%s)", PostgresSessionBackend._mask_url(self.url))

    def save(self, consultation_id: str, state_data: dict[str, Any]) -> None:
        """Simpan atau update state sesi."""
        if not self.available:
            return
        from sqlalchemy import text

        payload = json.dumps(state_data, ensure_ascii=False, default=str)
        with self._engine.begin() as conn:  # type: ignore[union-attr]
            conn.execute(
                text("""
                    INSERT INTO ai_sessions (consultation_id, state_data, created_at, updated_at)
                    VALUES (:cid, CAST(:payload AS jsonb), now(), now())
                    ON CONFLICT (consultation_id) DO UPDATE
                    SET state_data = CAST(:payload AS jsonb), updated_at = now()
                """),
                {"cid": consultation_id, "payload": payload},
            )

    def load(self, consultation_id: str) -> dict[str, Any] | None:
        """Load state sesi dari PostgreSQL."""
        if not self.available:
            return None
        from sqlalchemy import text

        with self._engine.connect() as conn:  # type: ignore[union-attr]
            rows = conn.execute(
                text("SELECT state_data FROM ai_sessions WHERE consultation_id = :cid"),
                {"cid": consultation_id},
            ).mappings().all()

        if not rows:
            return None
        payload = rows[0]["state_data"]
        if isinstance(payload, dict):
            return payload
        return json.loads(payload)

    def delete(self, consultation_id: str) -> bool:
        """Hapus state sesi dari PostgreSQL."""
        if not self.available:
            return False
        from sqlalchemy import text

        with self._engine.begin() as conn:  # type: ignore[union-attr]
            result = conn.execute(
                text("DELETE FROM ai_sessions WHERE consultation_id = :cid"),
                {"cid": consultation_id},
            )
            return result.rowcount > 0  # type: ignore[attr-defined]

    def list_all(self, limit: int = 1000) -> list[tuple[str, dict[str, Any]]]:
        """Daftar semua sesi (untuk rehydrate saat startup)."""
        if not self.available:
            return []
        from sqlalchemy import text

        with self._engine.connect() as conn:  # type: ignore[union-attr]
            rows = conn.execute(
                text("""
                    SELECT consultation_id, state_data
                    FROM ai_sessions
                    ORDER BY updated_at DESC
                    LIMIT :limit
                """),
                {"limit": limit},
            ).mappings().all()

        out = []
        for r in rows:
            cid = r["consultation_id"]
            payload = r["state_data"]
            if not isinstance(payload, dict):
                payload = json.loads(payload)
            out.append((cid, payload))
        return out

    @staticmethod
    def _mask_url(url: str) -> str:
        if "@" in url:
            scheme_creds, _, host = url.partition("@")
            scheme = scheme_creds.split("//", 1)[0]
            return f"{scheme}//***@{host}"
        return url


class SessionStore:
    """Persistent session store untuk ConsultationState.

    Mengikuti pola dual-backend seperti LearningStore:
    - jsonl: file JSONL + in-memory cache (development)
    - postgres: tabel ai_sessions (produksi)
    - both: dual-write untuk migrasi

    Thread-safe dan mendukung rehydrate setelah server restart.
    """

    def __init__(
        self,
        base_dir: Path | None = None,
        backend: str | None = None,
    ):
        self.base_dir = base_dir or SESSIONS_DIR
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.backend = (backend or SESSION_STORE_BACKEND).lower()
        self._lock = threading.Lock()

        # In-memory cache (untuk kecepatan)
        self._cache: dict[str, dict[str, Any]] = {}

        # PostgreSQL backend
        self._pg: PostgresSessionBackend | None = None
        if self.backend in ("postgres", "both", "pg"):
            try:
                self._pg = PostgresSessionBackend()
            except Exception as exc:  # noqa: BLE001
                logger.warning("PG session backend tidak tersedia: %s", exc)

        # Load existing sessions from persistent storage on init
        self._rehydrate_cache()

    @property
    def pg_available(self) -> bool:
        return self._pg is not None and self._pg.available

    def _use_jsonl(self) -> bool:
        return self.backend in ("jsonl", "both", "file", "")

    def _use_pg(self) -> bool:
        return self.backend in ("postgres", "both", "pg") and self.pg_available

    def _rehydrate_cache(self) -> None:
        """Load semua sesi yang ada dari persistent storage ke in-memory cache.

        Dipanggil saat startup agar sesi lama tersedia langsung.
        Prioritas: postgres > jsonl (jika keduanya ada).
        """
        # Coba PostgreSQL dulu
        if self._use_pg() and self._pg:
            try:
                rows = self._pg.list_all(limit=10000)
                for cid, data in rows:
                    self._cache[cid] = data
                logger.info("Rehydrated %d sessions from PostgreSQL", len(rows))
                return  # Jika PG berhasil, tidak perlu dari JSONL
            except Exception as exc:  # noqa: BLE001
                logger.warning("Failed to rehydrate from PG: %s", exc)

        # Fallback ke JSONL
        if self._use_jsonl():
            count = 0
            for path in self.base_dir.glob("*.json"):
                try:
                    with path.open("r", encoding="utf-8") as f:
                        data = json.load(f)
                    cid = data.get("consultation_id") or path.stem
                    self._cache[cid] = data
                    count += 1
                except Exception:  # noqa: BLE001
                    continue
            if count > 0:
                logger.info("Rehydrated %d sessions from JSON files", count)

    def _save_jsonl(self, consultation_id: str, state_data: dict[str, Any]) -> None:
        """Simpan state ke file JSON (satu file per sesi, bukan append-only)."""
        path = self.base_dir / f"{consultation_id}.json"
        # Tulis ke file temporary dulu untuk atomicity
        tmp_path = self.base_dir / f".{consultation_id}.{uuid.uuid4().hex}.tmp"
        with tmp_path.open("w", encoding="utf-8") as f:
            json.dump(state_data, f, ensure_ascii=False, default=str, indent=2)
        # Atomic rename
        tmp_path.replace(path)

    def save(self, consultation_id: str, state: dict[str, Any]) -> None:
        """Simpan atau update state sesi ke semua backend yang aktif.

        Args:
            consultation_id: ID sesi
            state: Dict representasi ConsultationState (sudah diserialize)
        """
        with self._lock:
            # Update cache dulu (cepat)
            self._cache[consultation_id] = dict(state)

            # Persist ke backend
            if self._use_jsonl():
                try:
                    self._save_jsonl(consultation_id, state)
                except Exception as exc:  # noqa: BLE001
                    logger.warning("Failed to save session to JSON: %s", exc)

            if self._use_pg() and self._pg:
                try:
                    self._pg.save(consultation_id, state)
                except Exception as exc:  # noqa: BLE001
                    logger.warning("Failed to save session to PG: %s", exc)

    def load(self, consultation_id: str) -> dict[str, Any] | None:
        """Load state sesi.

        Urutan prioritas:
        1. In-memory cache (cepat)
        2. PostgreSQL
        3. File JSON
        """
        # Cek cache dulu
        with self._lock:
            cached = self._cache.get(consultation_id)
            if cached is not None:
                return dict(cached)

        # Coba PostgreSQL
        if self._use_pg() and self._pg:
            try:
                data = self._pg.load(consultation_id)
                if data is not None:
                    with self._lock:
                        self._cache[consultation_id] = dict(data)
                    return data
            except Exception as exc:  # noqa: BLE001
                logger.warning("Failed to load session from PG: %s", exc)

        # Coba file JSON
        if self._use_jsonl():
            path = self.base_dir / f"{consultation_id}.json"
            if path.exists():
                try:
                    with path.open("r", encoding="utf-8") as f:
                        data = json.load(f)
                    with self._lock:
                        self._cache[consultation_id] = dict(data)
                    return data
                except Exception as exc:  # noqa: BLE001
                    logger.warning("Failed to load session from JSON: %s", exc)

        return None

    def delete(self, consultation_id: str) -> bool:
        """Hapus sesi dari semua backend."""
        found = False
        with self._lock:
            if consultation_id in self._cache:
                del self._cache[consultation_id]
                found = True

        if self._use_jsonl():
            path = self.base_dir / f"{consultation_id}.json"
            if path.exists():
                path.unlink()
                found = True

        if self._use_pg() and self._pg:
            try:
                if self._pg.delete(consultation_id):
                    found = True
            except Exception:  # noqa: BLE001
                pass

        return found

    def list_ids(self, limit: int = 1000) -> list[str]:
        """Daftar semua consultation_id yang ada."""
        with self._lock:
            return list(self._cache.keys())[:limit]

    def stats(self) -> dict[str, int]:
        """Statistik jumlah sesi."""
        count = len(self._cache)
        return {"sessions": count, "backend": self.backend}

    def backend_info(self) -> dict[str, Any]:
        """Info konfigurasi backend."""
        return {
            "backend": self.backend,
            "postgres_available": self.pg_available,
            "cache_count": len(self._cache),
            "directory": str(self.base_dir),
        }


# Singleton
_store_singleton: SessionStore | None = None


def get_session_store() -> SessionStore:
    global _store_singleton
    if _store_singleton is None:
        _store_singleton = SessionStore()
    return _store_singleton
