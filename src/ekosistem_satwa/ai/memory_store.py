"""Memory Service untuk menyimpan dan mengambil konteks percakapan.

Short-term Memory:
- Active conversation state (current intent, last agent, recent messages)
- TTL: 24 jam inactivity -> expire
- Storage: JSONL + in-memory cache (development), PostgreSQL (produksi)

Long-term Memory:
- User preferences (preferred brand, clinic, language)
- Pet history summary (common issues, behavior notes, dietary preferences)
- TTL: permanent (bisa dihapus user)
- Storage: PostgreSQL (ai_memory table), JSONL fallback
"""
from __future__ import annotations

import json
import logging
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from ..config import (
    DATABASE_URL,
    MEMORY_BACKEND,
    MEMORY_DIR,
    SHORT_TERM_MEMORY_TTL_SECONDS,
)

logger = logging.getLogger("ekosistem_satwa.ai.memory")

# Memory scopes
MemoryScope = Literal["short_term", "long_term"]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _now_ts() -> float:
    return datetime.now(timezone.utc).timestamp()


# =============================================================================
# PostgreSQL Backend for Memory
# =============================================================================

_CREATE_MEMORY_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS ai_memory (
  id              TEXT PRIMARY KEY,
  scope           TEXT NOT NULL,          -- short_term | long_term
  user_id         INTEGER,                 -- nullable for anonymous sessions
  pet_id          INTEGER,                 -- nullable
  session_id      TEXT,                    -- for short_term: consultation/session ID
  memory_key      TEXT NOT NULL,           -- key within the scope
  value           JSONB NOT NULL,          -- the memory value
  expires_at      TIMESTAMPTZ,             -- NULL for permanent (long_term)
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_ai_memory_scope
  ON ai_memory (scope);
CREATE INDEX IF NOT EXISTS idx_ai_memory_user
  ON ai_memory (user_id);
CREATE INDEX IF NOT EXISTS idx_ai_memory_session
  ON ai_memory (session_id);
CREATE INDEX IF NOT EXISTS idx_ai_memory_lookup
  ON ai_memory (scope, user_id, pet_id, session_id, memory_key);
CREATE INDEX IF NOT EXISTS idx_ai_memory_expires
  ON ai_memory (expires_at) WHERE expires_at IS NOT NULL;
"""


class PostgresMemoryBackend:
    """PostgreSQL backend untuk MemoryService (tabel ai_memory)."""

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
            conn.execute(text(_CREATE_MEMORY_TABLE_SQL))
        self._ready = True
        logger.info("PostgreSQL memory backend siap (%s)", self._mask_url())

    def _mask_url(self) -> str:
        if "@" in self.url:
            scheme_creds, _, host = self.url.partition("@")
            scheme = scheme_creds.split("//", 1)[0]
            return f"{scheme}//***@{host}"
        return self.url

    def set(
        self,
        scope: MemoryScope,
        memory_key: str,
        value: Any,
        user_id: int | None = None,
        pet_id: int | None = None,
        session_id: str | None = None,
        ttl_seconds: int | None = None,
    ) -> dict[str, Any]:
        """Set or update a memory entry."""
        if not self.available:
            return {}

        from sqlalchemy import text

        memory_id = f"{scope}:{user_id or 'anon'}:{pet_id or 'any'}:{session_id or 'any'}:{memory_key}"
        memory_id = uuid.uuid5(uuid.NAMESPACE_URL, memory_id).hex

        expires_at = None
        if ttl_seconds:
            expires_ts = _now_ts() + ttl_seconds
            expires_at = datetime.fromtimestamp(expires_ts, timezone.utc).isoformat()

        payload = {
            "id": memory_id,
            "scope": scope,
            "memory_key": memory_key,
            "value": json.dumps(value, ensure_ascii=False, default=str),
            "user_id": user_id,
            "pet_id": pet_id,
            "session_id": session_id,
            "expires_at": expires_at,
        }

        with self._engine.begin() as conn:  # type: ignore[union-attr]
            conn.execute(
                text("""
                    INSERT INTO ai_memory
                      (id, scope, user_id, pet_id, session_id, memory_key, value, expires_at, created_at, updated_at)
                    VALUES
                      (:id, :scope, :user_id, :pet_id, :session_id, :memory_key, CAST(:value AS jsonb),
                       COALESCE(CAST(:expires_at AS timestamptz), NULL), now(), now())
                    ON CONFLICT (id) DO UPDATE
                    SET value = CAST(:value AS jsonb), updated_at = now(),
                        expires_at = COALESCE(CAST(:expires_at AS timestamptz), ai_memory.expires_at)
                """),
                payload,
            )

        return {
            "id": memory_id,
            "scope": scope,
            "key": memory_key,
            "updated_at": _now_iso(),
        }

    def get(
        self,
        scope: MemoryScope,
        memory_key: str | None = None,
        user_id: int | None = None,
        pet_id: int | None = None,
        session_id: str | None = None,
    ) -> dict[str, Any] | None:
        """Get memory entry(ies). If memory_key is None, returns all matching."""
        if not self.available:
            return None

        from sqlalchemy import text

        conditions = ["scope = :scope"]
        params: dict[str, Any] = {"scope": scope, "now_ts": _now_ts()}

        if user_id is not None:
            conditions.append("(user_id = :user_id OR user_id IS NULL)")
            params["user_id"] = user_id

        if pet_id is not None:
            conditions.append("(pet_id = :pet_id OR pet_id IS NULL)")
            params["pet_id"] = pet_id

        if session_id is not None:
            conditions.append("(session_id = :session_id OR session_id IS NULL)")
            params["session_id"] = session_id

        if memory_key is not None:
            conditions.append("memory_key = :memory_key")
            params["memory_key"] = memory_key

        # Expiry check: either no expiry, or not yet expired
        conditions.append("(expires_at IS NULL OR expires_at > now())")

        where_clause = " AND ".join(conditions)

        with self._engine.connect() as conn:  # type: ignore[union-attr]
            rows = conn.execute(
                text(f"""
                    SELECT id, scope, user_id, pet_id, session_id, memory_key, value,
                           expires_at, created_at, updated_at
                    FROM ai_memory
                    WHERE {where_clause}
                    ORDER BY updated_at DESC
                """),
                params,
            ).mappings().all()

        if not rows:
            return None

        # If specific key requested, return single value
        if memory_key is not None:
            r = rows[0]
            value = dict(r["value"]) if isinstance(r["value"], dict) else json.loads(r["value"])
            return {
                "key": r["memory_key"],
                "value": value,
                "scope": r["scope"],
                "user_id": r["user_id"],
                "pet_id": r["pet_id"],
                "session_id": r["session_id"],
                "created_at": str(r["created_at"]),
                "updated_at": str(r["updated_at"]),
            }

        # Return all matching as dict key->value
        result: dict[str, Any] = {}
        for r in rows:
            key = r["memory_key"]
            value = dict(r["value"]) if isinstance(r["value"], dict) else json.loads(r["value"])
            result[key] = {
                "value": value,
                "user_id": r["user_id"],
                "pet_id": r["pet_id"],
                "session_id": r["session_id"],
                "updated_at": str(r["updated_at"]),
            }
        return result

    def delete(
        self,
        scope: MemoryScope,
        memory_key: str,
        user_id: int | None = None,
        pet_id: int | None = None,
        session_id: str | None = None,
    ) -> bool:
        """Delete a specific memory entry."""
        if not self.available:
            return False

        from sqlalchemy import text

        conditions = ["scope = :scope", "memory_key = :memory_key"]
        params: dict[str, Any] = {"scope": scope, "memory_key": memory_key}

        if user_id is not None:
            conditions.append("user_id = :user_id")
            params["user_id"] = user_id
        if pet_id is not None:
            conditions.append("pet_id = :pet_id")
            params["pet_id"] = pet_id
        if session_id is not None:
            conditions.append("session_id = :session_id")
            params["session_id"] = session_id

        where_clause = " AND ".join(conditions)

        with self._engine.begin() as conn:  # type: ignore[union-attr]
            result = conn.execute(
                text(f"DELETE FROM ai_memory WHERE {where_clause}"),
                params,
            )
            return result.rowcount > 0  # type: ignore[attr-defined]

    def clear_scope(
        self,
        scope: MemoryScope,
        user_id: int | None = None,
        pet_id: int | None = None,
        session_id: str | None = None,
    ) -> int:
        """Clear all memory entries matching the criteria."""
        if not self.available:
            return 0

        from sqlalchemy import text

        conditions = ["scope = :scope"]
        params: dict[str, Any] = {"scope": scope}

        if user_id is not None:
            conditions.append("user_id = :user_id")
            params["user_id"] = user_id
        if pet_id is not None:
            conditions.append("pet_id = :pet_id")
            params["pet_id"] = pet_id
        if session_id is not None:
            conditions.append("session_id = :session_id")
            params["session_id"] = session_id

        where_clause = " AND ".join(conditions)

        with self._engine.begin() as conn:  # type: ignore[union-attr]
            result = conn.execute(
                text(f"DELETE FROM ai_memory WHERE {where_clause}"),
                params,
            )
            return result.rowcount or 0  # type: ignore[attr-defined]

    def cleanup_expired(self) -> int:
        """Remove expired short-term memory entries. Returns count removed."""
        if not self.available:
            return 0

        from sqlalchemy import text

        with self._engine.begin() as conn:  # type: ignore[union-attr]
            result = conn.execute(
                text("DELETE FROM ai_memory WHERE expires_at IS NOT NULL AND expires_at < now()")
            )
            return result.rowcount or 0  # type: ignore[attr-defined]

    def stats(self) -> dict[str, Any]:
        """Get memory statistics."""
        if not self.available:
            return {}

        from sqlalchemy import text

        with self._engine.connect() as conn:  # type: ignore[union-attr]
            rows = conn.execute(
                text("""
                    SELECT scope, COUNT(*) AS n
                    FROM ai_memory
                    WHERE (expires_at IS NULL OR expires_at > now())
                    GROUP BY scope
                """)
            ).mappings().all()

        expired = conn.execute(  # type: ignore[name-defined]
            text("SELECT COUNT(*) AS n FROM ai_memory WHERE expires_at IS NOT NULL AND expires_at < now()")
        ).mappings().one()

        return {
            "by_scope": {r["scope"]: int(r["n"]) for r in rows},
            "expired_waiting": int(expired["n"]),
        }


# =============================================================================
# JSONL Backend (for development)
# =============================================================================

class JsonlMemoryBackend:
    """JSONL-based memory backend for development/testing.

    Structure:
    - short_term/: session-based memory with TTL
    - long_term/: permanent memory organized by user_id/pet_id
    """

    def __init__(self, base_dir: Path | None = None):
        self.base_dir = base_dir or MEMORY_DIR
        self.short_term_dir = self.base_dir / "short_term"
        self.long_term_dir = self.base_dir / "long_term"
        self._lock = threading.Lock()

        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.short_term_dir.mkdir(exist_ok=True)
        self.long_term_dir.mkdir(exist_ok=True)

    def _get_short_term_path(self, session_id: str | None, memory_key: str) -> Path:
        safe_session = session_id or "default"
        # Sanitize for filesystem
        safe_session = "".join(c if c.isalnum() or c in "-_." else "_" for c in safe_session)
        safe_key = "".join(c if c.isalnum() or c in "-_." else "_" for c in memory_key)
        return self.short_term_dir / f"{safe_session}__{safe_key}.json"

    def _get_long_term_path(self, user_id: int | None, pet_id: int | None, memory_key: str) -> Path:
        safe_user = f"user_{user_id}" if user_id else "user_anon"
        safe_pet = f"pet_{pet_id}" if pet_id else "pet_any"
        safe_key = "".join(c if c.isalnum() or c in "-_." else "_" for c in memory_key)
        return self.long_term_dir / f"{safe_user}__{safe_pet}__{safe_key}.json"

    def _load_file(self, path: Path) -> dict[str, Any] | None:
        if not path.exists():
            return None
        try:
            with path.open("r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:  # noqa: BLE001
            return None

    def _save_file(self, path: Path, data: dict[str, Any]) -> None:
        # Atomic write via temp file
        tmp_path = path.parent / f".{path.name}.{uuid.uuid4().hex}.tmp"
        with tmp_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, default=str, indent=2)
        tmp_path.replace(path)

    def _is_expired(self, data: dict[str, Any]) -> bool:
        expires_at = data.get("expires_at")
        if not expires_at:
            return False
        try:
            # Parse ISO format
            if isinstance(expires_at, str):
                import re
                # Handle both with and without timezone
                ts_str = expires_at.replace("Z", "+00:00")
                # Python 3.11+ has fromisoformat that handles this, but be safe
                if "+" in ts_str:
                    dt = datetime.fromisoformat(ts_str)
                else:
                    dt = datetime.fromisoformat(ts_str).replace(tzinfo=timezone.utc)
                return dt < datetime.now(timezone.utc)
            elif isinstance(expires_at, (int, float)):
                return expires_at < _now_ts()
        except Exception:  # noqa: BLE001
            pass
        return False

    def set(
        self,
        scope: MemoryScope,
        memory_key: str,
        value: Any,
        user_id: int | None = None,
        pet_id: int | None = None,
        session_id: str | None = None,
        ttl_seconds: int | None = None,
    ) -> dict[str, Any]:
        with self._lock:
            if scope == "short_term":
                path = self._get_short_term_path(session_id, memory_key)
            else:
                path = self._get_long_term_path(user_id, pet_id, memory_key)

            expires_at = None
            if ttl_seconds and scope == "short_term":
                expires_ts = _now_ts() + ttl_seconds
                expires_at = datetime.fromtimestamp(expires_ts, timezone.utc).isoformat()

            record = {
                "id": uuid.uuid4().hex,
                "scope": scope,
                "key": memory_key,
                "value": value,
                "user_id": user_id,
                "pet_id": pet_id,
                "session_id": session_id,
                "expires_at": expires_at,
                "created_at": _now_iso(),
                "updated_at": _now_iso(),
            }

            self._save_file(path, record)
            return {"key": memory_key, "updated_at": record["updated_at"]}

    def get(
        self,
        scope: MemoryScope,
        memory_key: str | None = None,
        user_id: int | None = None,
        pet_id: int | None = None,
        session_id: str | None = None,
    ) -> dict[str, Any] | None:
        with self._lock:
            if memory_key is not None:
                # Get single key
                if scope == "short_term":
                    path = self._get_short_term_path(session_id, memory_key)
                else:
                    path = self._get_long_term_path(user_id, pet_id, memory_key)

                data = self._load_file(path)
                if data and not self._is_expired(data):
                    return {
                        "key": data["key"],
                        "value": data["value"],
                        "scope": data["scope"],
                        "user_id": data.get("user_id"),
                        "pet_id": data.get("pet_id"),
                        "session_id": data.get("session_id"),
                        "created_at": data.get("created_at"),
                        "updated_at": data.get("updated_at"),
                    }
                return None

            # Get all matching - scan directory
            result: dict[str, Any] = {}
            target_dir = self.short_term_dir if scope == "short_term" else self.long_term_dir

            for p in target_dir.glob("*.json"):
                if p.name.startswith("."):
                    continue
                data = self._load_file(p)
                if not data or self._is_expired(data):
                    continue

                # Filter by criteria
                # Semantic: if filter is provided, data must either match OR be None (user-level)
                # This matches PostgreSQL logic: (col = :val OR col IS NULL)
                if session_id is not None:
                    data_session = data.get("session_id")
                    if data_session is not None and data_session != session_id:
                        continue
                if user_id is not None:
                    data_user = data.get("user_id")
                    if data_user is not None and data_user != user_id:
                        continue
                if pet_id is not None:
                    data_pet = data.get("pet_id")
                    if data_pet is not None and data_pet != pet_id:
                        continue

                key = data.get("key") or p.stem
                result[key] = {
                    "value": data["value"],
                    "user_id": data.get("user_id"),
                    "pet_id": data.get("pet_id"),
                    "session_id": data.get("session_id"),
                    "updated_at": data.get("updated_at"),
                }

            return result if result else None

    def delete(
        self,
        scope: MemoryScope,
        memory_key: str,
        user_id: int | None = None,
        pet_id: int | None = None,
        session_id: str | None = None,
    ) -> bool:
        with self._lock:
            if scope == "short_term":
                path = self._get_short_term_path(session_id, memory_key)
            else:
                path = self._get_long_term_path(user_id, pet_id, memory_key)

            if path.exists():
                path.unlink()
                return True
            return False

    def clear_scope(
        self,
        scope: MemoryScope,
        user_id: int | None = None,
        pet_id: int | None = None,
        session_id: str | None = None,
    ) -> int:
        with self._lock:
            target_dir = self.short_term_dir if scope == "short_term" else self.long_term_dir
            count = 0

            # Build prefix pattern for matching
            safe_session = session_id or ""
            safe_user = f"user_{user_id}" if user_id else ""
            safe_pet = f"pet_{pet_id}" if pet_id else ""

            for p in target_dir.glob("*.json"):
                if p.name.startswith("."):
                    continue

                data = self._load_file(p)
                if not data:
                    continue

                # Filter by criteria - strict match for clear operations
                # This is different from get() - we don't want to accidentally
                # delete user-level preferences when clearing pet-specific data
                match = True
                if session_id is not None and data.get("session_id") != session_id:
                    match = False
                if user_id is not None and data.get("user_id") != user_id:
                    match = False
                if pet_id is not None and data.get("pet_id") != pet_id:
                    match = False

                if match:
                    p.unlink()
                    count += 1

            return count

    def cleanup_expired(self) -> int:
        with self._lock:
            count = 0
            # Only short_term has TTL
            for p in self.short_term_dir.glob("*.json"):
                if p.name.startswith("."):
                    continue
                data = self._load_file(p)
                if data and self._is_expired(data):
                    p.unlink()
                    count += 1
            return count

    def stats(self) -> dict[str, Any]:
        with self._lock:
            short_count = len(list(self.short_term_dir.glob("*.json")))
            long_count = len(list(self.long_term_dir.glob("*.json")))
            expired = self.cleanup_expired()
            return {
                "by_scope": {"short_term": short_count, "long_term": long_count},
                "expired_removed": expired,
            }


# =============================================================================
# Memory Service - Unified API
# =============================================================================

class MemoryService:
    """Unified Memory Service combining short-term and long-term memory.

    Short-term: session-based, TTL-expiring memory for conversation state
    Long-term: permanent user/pet preferences and history
    """

    def __init__(
        self,
        backend: str | None = None,
        ttl_seconds: int | None = None,
    ):
        self.backend = (backend or MEMORY_BACKEND).lower()
        self.ttl_seconds = ttl_seconds or SHORT_TERM_MEMORY_TTL_SECONDS
        self._lock = threading.Lock()

        # Initialize backends
        self._jsonl: JsonlMemoryBackend | None = None
        self._pg: PostgresMemoryBackend | None = None

        if self._use_jsonl():
            self._jsonl = JsonlMemoryBackend()
        if self._use_pg():
            try:
                self._pg = PostgresMemoryBackend()
            except Exception as exc:
                logger.warning("PG memory backend tidak tersedia: %s", exc)

    def _use_jsonl(self) -> bool:
        return self.backend in ("jsonl", "both", "file", "")

    def _use_pg(self) -> bool:
        return self.backend in ("postgres", "both", "pg") and self.pg_available

    @property
    def pg_available(self) -> bool:
        return self._pg is not None and self._pg.available

    # -------------------------------------------------------------------------
    # Short-term Memory (session-scoped, TTL)
    # -------------------------------------------------------------------------

    def set_short_term(
        self,
        session_id: str,
        key: str,
        value: Any,
        user_id: int | None = None,
        pet_id: int | None = None,
        ttl_seconds: int | None = None,
    ) -> dict[str, Any]:
        """Store short-term memory for a session.

        Short-term memory expires after TTL (default 24h).
        Used for: current intent, last agent, recent messages, conversation state.
        """
        actual_ttl = ttl_seconds or self.ttl_seconds

        if self._use_pg() and self._pg:
            return self._pg.set(
                scope="short_term",
                memory_key=key,
                value=value,
                user_id=user_id,
                pet_id=pet_id,
                session_id=session_id,
                ttl_seconds=actual_ttl,
            )

        if self._use_jsonl() and self._jsonl:
            return self._jsonl.set(
                scope="short_term",
                memory_key=key,
                value=value,
                user_id=user_id,
                pet_id=pet_id,
                session_id=session_id,
                ttl_seconds=actual_ttl,
            )

        return {"key": key, "status": "no_backend_available"}

    def get_short_term(
        self,
        session_id: str,
        key: str | None = None,
        user_id: int | None = None,
        pet_id: int | None = None,
    ) -> dict[str, Any] | None:
        """Retrieve short-term memory.

        If key is None, returns all short-term memory for the session.
        """
        # Try PG first
        if self._use_pg() and self._pg:
            result = self._pg.get(
                scope="short_term",
                memory_key=key,
                user_id=user_id,
                pet_id=pet_id,
                session_id=session_id,
            )
            if result is not None:
                return result

        # Fallback to JSONL
        if self._use_jsonl() and self._jsonl:
            return self._jsonl.get(
                scope="short_term",
                memory_key=key,
                user_id=user_id,
                pet_id=pet_id,
                session_id=session_id,
            )

        return None

    def delete_short_term(
        self,
        session_id: str,
        key: str,
        user_id: int | None = None,
        pet_id: int | None = None,
    ) -> bool:
        """Delete a specific short-term memory entry."""
        deleted = False

        if self._use_pg() and self._pg:
            if self._pg.delete(
                scope="short_term",
                memory_key=key,
                user_id=user_id,
                pet_id=pet_id,
                session_id=session_id,
            ):
                deleted = True

        if self._use_jsonl() and self._jsonl:
            if self._jsonl.delete(
                scope="short_term",
                memory_key=key,
                user_id=user_id,
                pet_id=pet_id,
                session_id=session_id,
            ):
                deleted = True

        return deleted

    def clear_short_term(
        self,
        session_id: str,
        user_id: int | None = None,
        pet_id: int | None = None,
    ) -> int:
        """Clear ALL short-term memory for a session.

        Used when session ends or user explicitly clears.
        """
        count = 0

        if self._use_pg() and self._pg:
            count += self._pg.clear_scope(
                scope="short_term",
                user_id=user_id,
                pet_id=pet_id,
                session_id=session_id,
            )

        if self._use_jsonl() and self._jsonl:
            count += self._jsonl.clear_scope(
                scope="short_term",
                user_id=user_id,
                pet_id=pet_id,
                session_id=session_id,
            )

        return count

    # -------------------------------------------------------------------------
    # Long-term Memory (user/pet-scoped, permanent)
    # -------------------------------------------------------------------------

    def set_long_term(
        self,
        key: str,
        value: Any,
        user_id: int | None = None,
        pet_id: int | None = None,
    ) -> dict[str, Any]:
        """Store long-term memory.

        Long-term memory is permanent (no TTL) but can be deleted.
        Used for: user preferences, pet history, dietary restrictions, behavior notes.
        """
        if self._use_pg() and self._pg:
            return self._pg.set(
                scope="long_term",
                memory_key=key,
                value=value,
                user_id=user_id,
                pet_id=pet_id,
                session_id=None,
                ttl_seconds=None,
            )

        if self._use_jsonl() and self._jsonl:
            return self._jsonl.set(
                scope="long_term",
                memory_key=key,
                value=value,
                user_id=user_id,
                pet_id=pet_id,
                session_id=None,
                ttl_seconds=None,
            )

        return {"key": key, "status": "no_backend_available"}

    def get_long_term(
        self,
        key: str | None = None,
        user_id: int | None = None,
        pet_id: int | None = None,
    ) -> dict[str, Any] | None:
        """Retrieve long-term memory.

        If key is None, returns all matching long-term memory for user/pet.
        """
        if self._use_pg() and self._pg:
            result = self._pg.get(
                scope="long_term",
                memory_key=key,
                user_id=user_id,
                pet_id=pet_id,
                session_id=None,
            )
            if result is not None:
                return result

        if self._use_jsonl() and self._jsonl:
            return self._jsonl.get(
                scope="long_term",
                memory_key=key,
                user_id=user_id,
                pet_id=pet_id,
                session_id=None,
            )

        return None

    def delete_long_term(
        self,
        key: str,
        user_id: int | None = None,
        pet_id: int | None = None,
    ) -> bool:
        """Delete a specific long-term memory entry."""
        deleted = False

        if self._use_pg() and self._pg:
            if self._pg.delete(
                scope="long_term",
                memory_key=key,
                user_id=user_id,
                pet_id=pet_id,
                session_id=None,
            ):
                deleted = True

        if self._use_jsonl() and self._jsonl:
            if self._jsonl.delete(
                scope="long_term",
                memory_key=key,
                user_id=user_id,
                pet_id=pet_id,
                session_id=None,
            ):
                deleted = True

        return deleted

    # -------------------------------------------------------------------------
    # Unified API for Gateway
    # -------------------------------------------------------------------------

    def set(
        self,
        scope: MemoryScope,
        key: str,
        value: Any,
        user_id: int | None = None,
        pet_id: int | None = None,
        session_id: str | None = None,
    ) -> dict[str, Any]:
        """Unified set API for Gateway integration."""
        if scope == "short_term":
            if not session_id:
                raise ValueError("session_id required for short_term memory")
            return self.set_short_term(
                session_id=session_id,
                key=key,
                value=value,
                user_id=user_id,
                pet_id=pet_id,
            )
        else:
            return self.set_long_term(
                key=key,
                value=value,
                user_id=user_id,
                pet_id=pet_id,
            )

    def get(
        self,
        scope: MemoryScope,
        key: str | None = None,
        user_id: int | None = None,
        pet_id: int | None = None,
        session_id: str | None = None,
    ) -> dict[str, Any] | None:
        """Unified get API for Gateway integration."""
        if scope == "short_term":
            return self.get_short_term(
                session_id=session_id or "",
                key=key,
                user_id=user_id,
                pet_id=pet_id,
            )
        else:
            return self.get_long_term(
                key=key,
                user_id=user_id,
                pet_id=pet_id,
            )

    def delete(
        self,
        scope: MemoryScope,
        key: str,
        user_id: int | None = None,
        pet_id: int | None = None,
        session_id: str | None = None,
    ) -> bool:
        """Unified delete API."""
        if scope == "short_term":
            return self.delete_short_term(
                session_id=session_id or "",
                key=key,
                user_id=user_id,
                pet_id=pet_id,
            )
        else:
            return self.delete_long_term(
                key=key,
                user_id=user_id,
                pet_id=pet_id,
            )

    def clear(
        self,
        scope: MemoryScope,
        user_id: int | None = None,
        pet_id: int | None = None,
        session_id: str | None = None,
    ) -> int:
        """Unified clear API (clear all matching entries)."""
        if scope == "short_term":
            return self.clear_short_term(
                session_id=session_id or "",
                user_id=user_id,
                pet_id=pet_id,
            )
        else:
            # For long_term, we need to iterate and delete matching
            all_long = self.get_long_term(user_id=user_id, pet_id=pet_id)
            count = 0
            if all_long and isinstance(all_long, dict):
                for key in all_long.keys():
                    if self.delete_long_term(key, user_id=user_id, pet_id=pet_id):
                        count += 1
            return count

    # -------------------------------------------------------------------------
    # Context Loading for AI Gateway
    # -------------------------------------------------------------------------

    def load_context(
        self,
        user_id: int | None = None,
        pet_id: int | None = None,
        session_id: str | None = None,
    ) -> dict[str, Any]:
        """Load consolidated context for AI Gateway Context Loader.

        Returns combined short_term + long_term memory relevant to the conversation.
        Called before routing to AI agents.
        """
        context: dict[str, Any] = {
            "short_term": {},
            "long_term": {},
            "loaded_at": _now_iso(),
        }

        # Load short-term (session state)
        if session_id:
            short_term = self.get_short_term(session_id=session_id, key=None)
            if short_term:
                # Unwrap the {key: {value: ...}} format
                for k, v in short_term.items():
                    if isinstance(v, dict) and "value" in v:
                        context["short_term"][k] = v["value"]
                    else:
                        context["short_term"][k] = v

        # Load long-term (user + pet preferences)
        if user_id or pet_id:
            long_term = self.get_long_term(key=None, user_id=user_id, pet_id=pet_id)
            if long_term:
                for k, v in long_term.items():
                    if isinstance(v, dict) and "value" in v:
                        context["long_term"][k] = v["value"]
                    else:
                        context["long_term"][k] = v

        return context

    def save_conversation(
        self,
        session_id: str,
        message: dict[str, Any],
        user_id: int | None = None,
        pet_id: int | None = None,
    ) -> dict[str, Any]:
        """Save conversation turn to short-term memory.

        Called after AI generates response to maintain conversation history.
        """
        # Get existing messages
        messages: list[dict[str, Any]] = []
        existing = self.get_short_term(session_id=session_id, key="recent_messages")
        if existing and "value" in existing:
            messages = existing["value"] if isinstance(existing["value"], list) else []

        # Append new message (keep last N)
        messages.append({**message, "saved_at": _now_iso()})
        if len(messages) > 50:  # Keep reasonable history
            messages = messages[-50:]

        return self.set_short_term(
            session_id=session_id,
            key="recent_messages",
            value=messages,
            user_id=user_id,
            pet_id=pet_id,
        )

    # -------------------------------------------------------------------------
    # Stats & Maintenance
    # -------------------------------------------------------------------------

    def stats(self) -> dict[str, Any]:
        """Get memory statistics."""
        stats_data: dict[str, Any] = {
            "backend": self.backend,
            "ttl_seconds": self.ttl_seconds,
            "postgres_available": self.pg_available,
        }

        if self._use_pg() and self._pg:
            try:
                stats_data["pg_stats"] = self._pg.stats()
            except Exception:  # noqa: BLE001
                pass

        if self._use_jsonl() and self._jsonl:
            stats_data["jsonl_stats"] = self._jsonl.stats()

        return stats_data

    def cleanup_expired(self) -> int:
        """Remove expired short-term memory entries."""
        count = 0
        if self._use_pg() and self._pg:
            count += self._pg.cleanup_expired()
        if self._use_jsonl() and self._jsonl:
            count += self._jsonl.cleanup_expired()
        return count


# Singleton
_default_service: MemoryService | None = None


def get_memory_service() -> MemoryService:
    global _default_service
    if _default_service is None:
        _default_service = MemoryService()
    return _default_service
