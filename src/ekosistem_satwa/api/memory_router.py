"""Memory API Router - Endpoints for managing short-term and long-term memory.

Endpoints:
- POST /api/v1/memory/set — Set memory key-value
- GET /api/v1/memory/get?scope=short_term|long_term — Get memory
- DELETE /api/v1/memory/{key} — Delete specific memory
- POST /api/v1/memory/clear — Clear session memory
- GET /api/v1/memory/stats — Memory statistics
- GET /api/v1/memory/context — Load consolidated context for AI Gateway
"""
from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field

from .auth import optional_client, require_vet
from ..ai.memory_store import MemoryService, get_memory_service
from ..integration.identity import resolve_consultation_id


class MemorySetRequest(BaseModel):
    """Request to set a memory entry."""

    scope: Literal["short_term", "long_term"] = Field(
        default="short_term",
        description="Memory scope: short_term (session, TTL) or long_term (permanent)",
    )
    key: str = Field(..., min_length=1, max_length=255, description="Memory key")
    value: Any = Field(..., description="Memory value (any JSON serializable)")
    session_id: str | None = Field(
        default=None,
        description="Session/consultation ID (required for short_term)",
    )
    user_id: int | None = Field(default=None, description="User ID for context")
    pet_id: int | None = Field(default=None, description="Pet ID for context")


class MemoryClearRequest(BaseModel):
    """Request to clear memory entries."""

    scope: Literal["short_term", "long_term"] = Field(
        default="short_term",
        description="Scope to clear",
    )
    session_id: str | None = Field(default=None, description="Session ID for short_term")
    user_id: int | None = Field(default=None, description="User ID filter")
    pet_id: int | None = Field(default=None, description="Pet ID filter")


class ConversationSaveRequest(BaseModel):
    """Request to save a conversation turn."""

    session_id: str = Field(..., description="Session/consultation ID")
    message: dict[str, Any] = Field(..., description="Message to save")
    user_id: int | None = None
    pet_id: int | None = None


router = APIRouter(prefix="/api/v1/memory", tags=["Memory Service"])


def _resolve_session(session_id: str | None, request: Request) -> str:
    """Resolve session ID from param, headers, or request context."""
    if session_id:
        resolved = resolve_consultation_id(session_id)
        if resolved:
            return resolved
        return session_id

    # Try header
    header_session = request.headers.get("X-Consultation-ID")
    if header_session:
        resolved = resolve_consultation_id(header_session)
        if resolved:
            return resolved
        return header_session

    # Generate temporary
    import uuid
    return f"temp_{uuid.uuid4().hex[:12]}"


# =============================================================================
# Memory CRUD Endpoints
# =============================================================================


@router.post("/set", dependencies=[Depends(require_vet)])
def memory_set(
    req: MemorySetRequest,
    request: Request,
    memory: MemoryService = Depends(get_memory_service),
) -> dict:
    """Set a memory entry.

    For short_term: session_id is required (can be in X-Consultation-ID header)
    For long_term: user_id/pet_id are used for scoping

    **Example request:**
    ```json
    {
        "scope": "short_term",
        "key": "current_intent",
        "value": {"intent": "symptom_discussion", "confidence": 0.85},
        "session_id": "consult-123",
        "user_id": 42,
        "pet_id": 15
    }
    ```
    """
    # Resolve session
    if req.scope == "short_term":
        session_id = _resolve_session(req.session_id, request)
    else:
        session_id = None

    result = memory.set(
        scope=req.scope,
        key=req.key,
        value=req.value,
        user_id=req.user_id,
        pet_id=req.pet_id,
        session_id=session_id,
    )

    return {
        "status": "ok",
        "scope": req.scope,
        "key": req.key,
        "result": result,
    }


@router.get("/get", dependencies=[Depends(require_vet)])
def memory_get(
    request: Request,
    scope: Literal["short_term", "long_term"] = Query(
        default="short_term",
        description="Memory scope to query",
    ),
    key: str | None = Query(default=None, description="Specific key to get (all if omitted)"),
    session_id: str | None = Query(default=None, description="Session ID for short_term"),
    user_id: int | None = Query(default=None, description="User ID filter"),
    pet_id: int | None = Query(default=None, description="Pet ID filter"),
    memory: MemoryService = Depends(get_memory_service),
) -> dict:
    """Get memory entries.

    If `key` is provided: returns single entry with {key, value, ...}
    If `key` is omitted: returns dict {key1: {value: ...}, key2: {value: ...}, ...}

    **Examples:**
    - `GET /api/v1/memory/get?scope=short_term&session_id=abc` — get all session memory
    - `GET /api/v1/memory/get?scope=short_term&key=current_intent&session_id=abc` — get specific key
    - `GET /api/v1/memory/get?scope=long_term&user_id=42&pet_id=15` — get pet preferences
    """
    if scope == "short_term":
        actual_session_id = _resolve_session(session_id, request)
    else:
        actual_session_id = None

    result = memory.get(
        scope=scope,
        key=key,
        user_id=user_id,
        pet_id=pet_id,
        session_id=actual_session_id,
    )

    if result is None:
        if key:
            raise HTTPException(status_code=404, detail=f"Key '{key}' not found in {scope}")
        return {"status": "ok", "scope": scope, "count": 0, "entries": {}}

    if key:
        return {
            "status": "ok",
            "scope": scope,
            "key": result.get("key"),
            "value": result.get("value"),
            "user_id": result.get("user_id"),
            "pet_id": result.get("pet_id"),
            "session_id": result.get("session_id"),
            "updated_at": result.get("updated_at"),
        }
    else:
        # result is dict of key -> {value, ...}
        count = len(result) if isinstance(result, dict) else 0
        return {
            "status": "ok",
            "scope": scope,
            "count": count,
            "entries": result,
        }


@router.delete("/{key:path}", dependencies=[Depends(require_vet)])
def memory_delete(
    key: str,
    request: Request,
    scope: Literal["short_term", "long_term"] = Query(
        default="short_term",
        description="Memory scope",
    ),
    session_id: str | None = Query(default=None, description="Session ID for short_term"),
    user_id: int | None = Query(default=None, description="User ID filter"),
    pet_id: int | None = Query(default=None, description="Pet ID filter"),
    memory: MemoryService = Depends(get_memory_service),
) -> dict:
    """Delete a specific memory entry.

    **Example:**
    `DELETE /api/v1/memory/current_intent?scope=short_term&session_id=abc`
    """
    if scope == "short_term":
        actual_session_id = _resolve_session(session_id, request)
    else:
        actual_session_id = None

    deleted = memory.delete(
        scope=scope,
        key=key,
        user_id=user_id,
        pet_id=pet_id,
        session_id=actual_session_id,
    )

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail=f"Key '{key}' not found or could not be deleted",
        )

    return {
        "status": "deleted",
        "scope": scope,
        "key": key,
    }


@router.post("/clear", dependencies=[Depends(require_vet)])
def memory_clear(
    req: MemoryClearRequest,
    request: Request,
    memory: MemoryService = Depends(get_memory_service),
) -> dict:
    """Clear all memory entries matching the criteria.

    Use this to:
    - Clear a session after consultation ends
    - Reset user/pet preferences

    **Example:**
    ```json
    {
        "scope": "short_term",
        "session_id": "consult-123"
    }
    ```
    """
    if req.scope == "short_term":
        session_id = _resolve_session(req.session_id, request)
    else:
        session_id = None

    count = memory.clear(
        scope=req.scope,
        user_id=req.user_id,
        pet_id=req.pet_id,
        session_id=session_id,
    )

    return {
        "status": "cleared",
        "scope": req.scope,
        "entries_cleared": count,
    }


# =============================================================================
# AI Gateway Integration Endpoints
# =============================================================================


@router.get("/context")
def memory_load_context(
    request: Request,
    session_id: str | None = Query(default=None, description="Session/consultation ID"),
    user_id: int | None = Query(default=None, description="User ID"),
    pet_id: int | None = Query(default=None, description="Pet ID"),
    memory: MemoryService = Depends(get_memory_service),
) -> dict:
    """Load consolidated context for AI Gateway Context Loader.

    Returns combined short_term (session state) + long_term (user/pet preferences)
    memory relevant to the conversation.

    This is called by AI Gateway BEFORE routing to agents to provide context.

    **Response format:**
    ```json
    {
        "short_term": {
            "current_intent": {...},
            "last_agent": "general_agent",
            "recent_messages": [...]
        },
        "long_term": {
            "user_preferences": {"language": "id", "clinic_preference": "PawsCare"},
            "pet_history": {"common_issues": ["skin_allergies"], "diet": "grain_free"}
        },
        "loaded_at": "2026-06-26T..."
    }
    ```
    """
    actual_session_id = _resolve_session(session_id, request) if session_id else None

    context = memory.load_context(
        user_id=user_id,
        pet_id=pet_id,
        session_id=actual_session_id,
    )

    return {
        "status": "ok",
        "context": context,
    }


@router.post("/save-conversation", dependencies=[Depends(require_vet)])
def memory_save_conversation(
    req: ConversationSaveRequest,
    memory: MemoryService = Depends(get_memory_service),
) -> dict:
    """Save a conversation turn to short-term memory.

    Called by AI Gateway AFTER generating a response to maintain conversation history.

    **Example request:**
    ```json
    {
        "session_id": "consult-123",
        "message": {
            "role": "assistant",
            "content": "Based on the symptoms, I recommend...",
            "agent_used": "symptom_analyzer"
        },
        "user_id": 42,
        "pet_id": 15
    }
    ```
    """
    result = memory.save_conversation(
        session_id=req.session_id,
        message=req.message,
        user_id=req.user_id,
        pet_id=req.pet_id,
    )

    return {
        "status": "saved",
        "session_id": req.session_id,
        "result": result,
    }


# =============================================================================
# Stats & Maintenance
# =============================================================================


@router.get("/stats")
def memory_stats(
    memory: MemoryService = Depends(get_memory_service),
) -> dict:
    """Get memory service statistics.

    Returns backend info, entry counts, and TTL configuration.
    """
    stats_data = memory.stats()

    return {
        "status": "ok",
        "stats": stats_data,
    }


@router.post("/cleanup-expired", dependencies=[Depends(require_vet)])
def memory_cleanup_expired(
    memory: MemoryService = Depends(get_memory_service),
) -> dict:
    """Manually trigger cleanup of expired short-term memory entries.

    This is normally done automatically, but can be triggered manually.
    """
    count = memory.cleanup_expired()

    return {
        "status": "ok",
        "expired_entries_removed": count,
    }
