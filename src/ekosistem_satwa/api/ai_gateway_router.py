"""AI Gateway Router — Pawnia AI Companion entry point.

Endpoints:
- POST /api/v1/ai/chat — Main entry point for all user interactions
- GET  /api/v1/ai/status — Pawnia system status
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field

from .auth import optional_client
from ..ai.pawnia_orchestrator import (
    AgentType,
    PawniaOrchestrator,
    PawniaResponse,
    get_pawnia,
)

logger = logging.getLogger("ekosistem_satwa.api.ai_gateway")

router = APIRouter(prefix="/api/v1/ai", tags=["Pawnia AI Companion"])


# =============================================================================
# REQUEST / RESPONSE MODELS
# =============================================================================


class ChatRequest(BaseModel):
    """Request to the Pawnia AI Companion chat endpoint."""

    message: str = Field(default="", max_length=5000, description="User message (can be empty if has_image=true)")
    session_id: str | None = Field(
        default=None,
        description="Session/consultation ID for conversation continuity",
    )
    user_id: int | None = Field(default=None, description="User ID if authenticated")
    pet_id: int | None = Field(default=None, description="Pet ID for context")
    has_image: bool = Field(
        default=False,
        description="Set to true if user is uploading an image (will be processed separately)",
    )
    pet_context: dict[str, Any] | None = Field(
        default=None,
        description="Optional pet context: {name, species, breed, age_years, weight_kg, chronic_conditions}",
    )


class ChatResponse(BaseModel):
    """Response from the Pawnia AI Companion."""

    agent: str
    confidence: float
    risk_score: int
    risk_level: str
    response: dict[str, Any]
    context_used: dict[str, bool]
    escalated: bool = False
    conversation_id: str


class PawniaStatusResponse(BaseModel):
    """Pawnia system status."""

    status: str
    version: str
    pawnia_available: bool
    memory_available: bool
    knowledge_available: bool
    llm_available: bool
    agents: list[str]


# =============================================================================
# DEPENDENCIES
# =============================================================================


def _get_pawnia() -> PawniaOrchestrator:
    """Get Pawnia Orchestrator instance."""
    return get_pawnia()


# =============================================================================
# ENDPOINTS
# =============================================================================


@router.post("/chat", response_model=ChatResponse)
def pawnia_chat(
    req: ChatRequest,
    request: Request,
    pawnia: PawniaOrchestrator = Depends(_get_pawnia),
) -> ChatResponse:
    """Main entry point for Pawnia AI Companion.

    Processes user input through the full Pawnia pipeline:
    1. Intent Detection → 2. Risk Classification → 3. Context Loading
    4. Agent Routing → 5. Response Generation → 6. Safety Validation

    **Example request:**
    ```json
    {
        "message": "Kucing saya muntah-muntah dan lemas",
        "session_id": "consult-123",
        "user_id": 42,
        "pet_id": 15,
        "pet_context": {
            "name": "Milo",
            "species": "cat",
            "breed": "Persian",
            "age_years": 3,
            "weight_kg": 4.5
        }
    }
    ```

    **Example response:**
    ```json
    {
        "agent": "triage_emergency",
        "confidence": 0.85,
        "risk_score": 65,
        "risk_level": "high",
        "response": {
            "text": "...",
            "suggestions": [...],
            "cta": [...],
            "disclaimer": "..."
        },
        "context_used": {
            "intent_detection": true,
            "risk_classification": true,
            "memory": true,
            "proprietary": true
        },
        "escalated": false,
        "conversation_id": "consult-123"
    }
    ```
    """
    if not req.message.strip() and not req.has_image:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    try:
        result: PawniaResponse = pawnia.process(
            text=req.message,
            has_image=req.has_image,
            user_id=req.user_id,
            pet_id=req.pet_id,
            session_id=req.session_id,
            pet_context=req.pet_context,
        )

        return ChatResponse(
            agent=result.agent.value if isinstance(result.agent, AgentType) else str(result.agent),
            confidence=result.confidence,
            risk_score=result.risk_score,
            risk_level=result.risk_level,
            response=result.response,
            context_used=result.context_used,
            escalated=result.escalated,
            conversation_id=result.conversation_id,
        )

    except Exception as exc:
        logger.error("Pawnia chat error: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"AI processing error: {exc}") from exc


@router.get("/status", response_model=PawniaStatusResponse)
def pawnia_status(
    pawnia: PawniaOrchestrator = Depends(_get_pawnia),
) -> PawniaStatusResponse:
    """Get Pawnia AI Companion system status."""
    llm_available = pawnia.llm is not None and pawnia.llm.available if hasattr(pawnia, 'llm') else False

    return PawniaStatusResponse(
        status="ok",
        version="1.0.0",
        pawnia_available=True,
        memory_available=pawnia.memory is not None,
        knowledge_available=pawnia.knowledge is not None,
        llm_available=llm_available,
        agents=[a.value for a in AgentType],
    )


@router.post("/chat/simple")
def pawnia_chat_simple(
    message: str = Query(..., description="User message"),
    session_id: str | None = Query(None, description="Session ID"),
    pawnia: PawniaOrchestrator = Depends(_get_pawnia),
) -> dict[str, Any]:
    """Simple GET-based chat endpoint for quick testing.

    **Example:** `GET /api/v1/ai/chat/simple?message=Halo&session_id=test123`
    """
    result = pawnia.process(
        text=message,
        session_id=session_id,
    )
    return {
        "agent": result.agent.value if isinstance(result.agent, AgentType) else str(result.agent),
        "confidence": result.confidence,
        "risk_score": result.risk_score,
        "risk_level": result.risk_level,
        "response": result.response,
        "conversation_id": result.conversation_id,
    }
