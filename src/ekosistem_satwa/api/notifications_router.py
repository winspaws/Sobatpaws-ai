"""Notifications API Router - Endpoints for managing notification service.

Endpoints:
- POST /api/v1/notifications — Create notification
- GET /api/v1/notifications — List notifications for user
- GET /api/v1/notifications/{id} — Get single notification
- POST /api/v1/notifications/{id}/confirm — Confirm reminder (read/click/dismiss/snooze)
- GET /api/v1/notifications/upcoming — Upcoming reminders (for AI Gateway)

Integration with AI Gateway:
- GET /api/v1/notifications/upcoming is called by Context Loader to include in agent context
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field

from .auth import optional_client, require_vet
from .deps import get_emr_service
from ..emr.models import Notification
from ..emr.schemas import (
    NotificationConfirmRequest,
    NotificationCreate,
    NotificationListResponse,
    NotificationResponse,
    NotificationUpdate,
)
from ..emr.service import EMRService


router = APIRouter(prefix="/api/v1/notifications", tags=["Notification Service"])


def _get_current_user_id(request: Request) -> int:
    """Get current user ID from request state or headers.

    In production: extract from JWT token or auth session.
    For now: look for X-User-ID header or default to test user.
    """
    user_id_header = request.headers.get("X-User-ID")
    if user_id_header:
        try:
            return int(user_id_header)
        except ValueError:
            pass
    # Default test user for development
    return 1


# =============================================================================
# Notification CRUD Endpoints
# =============================================================================


@router.post("", response_model=NotificationResponse, dependencies=[Depends(require_vet)])
def create_notification(
    req: NotificationCreate,
    request: Request,
    emr: EMRService = Depends(get_emr_service),
) -> NotificationResponse:
    """Create a new notification.

    **Required:** user_id (in body or X-User-ID header)

    **Example request:**
    ```json
    {
        "user_id": 1,
        "pet_id": 5,
        "type": "vaccine_reminder",
        "channel": "in_app",
        "title": "Rabies Vaccine Due Soon",
        "body": "Your pet's rabies vaccine is due in 7 days",
        "scheduled_at": "2026-07-05T09:00:00Z",
        "data": {"vaccine_type": "rabies", "next_due": "2026-07-12"}
    }
    ```
    """
    user_id = req.user_id if req.user_id else _get_current_user_id(request)

    with emr.session() as session:
        notif = emr.create_notification(
            session=session,
            user_id=user_id,
            pet_id=req.pet_id,
            type=req.type,
            channel=req.channel,
            title=req.title,
            body=req.body,
            template_id=req.template_id,
            data=req.data,
            scheduled_at=req.scheduled_at,
            consultation_id=req.consultation_id,
            recommendation_id=req.recommendation_id,
            extra_metadata=req.extra_metadata,
            status="pending",
        )
        session.refresh(notif)
        return NotificationResponse.model_validate(notif)


@router.get("", response_model=NotificationListResponse)
def list_notifications(
    request: Request,
    user_id: int | None = Query(default=None, description="Filter by user ID (admin only)"),
    status: str | None = Query(default=None, description="Filter by status: pending|scheduled|sent|delivered|read|clicked|dismissed|failed"),
    type_filter: str | None = Query(default=None, alias="type", description="Filter by notification type"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    emr: EMRService = Depends(get_emr_service),
) -> NotificationListResponse:
    """List notifications for the current user.

    **Query params:**
    - status: filter by status
    - type: filter by notification type (vaccine_reminder, medication_reminder, etc.)
    - limit: max items to return
    - offset: pagination offset

    **For admin:** pass user_id to filter by specific user (requires admin role)
    """
    effective_user_id = user_id if user_id else _get_current_user_id(request)

    with emr.session() as session:
        notifications, total, pending_count, unread_count = emr.list_notifications_by_user(
            session=session,
            user_id=effective_user_id,
            status=status,
            type_filter=type_filter,
            limit=limit,
            offset=offset,
        )
        return NotificationListResponse(
            notifications=[NotificationResponse.model_validate(n) for n in notifications],
            total=total,
            pending_count=pending_count,
            unread_count=unread_count,
        )


@router.get("/upcoming", response_model=NotificationListResponse)
def get_upcoming_notifications(
    request: Request,
    user_id: int | None = Query(default=None, description="User ID (for admin override)"),
    hours_ahead: int = Query(default=24, ge=1, le=168, description="Hours window to look ahead"),
    limit: int = Query(default=20, ge=1, le=100),
    emr: EMRService = Depends(get_emr_service),
) -> NotificationListResponse:
    """Get upcoming scheduled notifications.

    **AI Gateway Integration:**
    This endpoint is called by the Context Loader BEFORE routing to agents
    to include upcoming medication reminders and vaccine schedules in the
    conversation context for the Medication Adherence Agent.

    Returns notifications that are pending/scheduled and due within hours_ahead.
    """
    effective_user_id = user_id if user_id else _get_current_user_id(request)

    with emr.session() as session:
        notifications = emr.list_upcoming_notifications(
            session=session,
            user_id=effective_user_id,
            hours_ahead=hours_ahead,
            limit=limit,
        )
        # Get counts separately for the same user
        _, total, pending_count, unread_count = emr.list_notifications_by_user(
            session=session,
            user_id=effective_user_id,
            status=None,
            type_filter=None,
            limit=1,
            offset=0,
        )
        return NotificationListResponse(
            notifications=[NotificationResponse.model_validate(n) for n in notifications],
            total=len(notifications),
            pending_count=pending_count,
            unread_count=unread_count,
        )


@router.get("/context")
def get_notification_context(
    request: Request,
    user_id: int | None = Query(default=None),
    pet_id: int | None = Query(default=None),
    hours_ahead: int = Query(default=48, ge=1, le=168),
    emr: EMRService = Depends(get_emr_service),
) -> dict:
    """Get structured notification context for AI Gateway Context Loader.

    **Special endpoint for AI Gateway:**
    Returns upcoming reminders in a structured format optimized for LLM context:

    ```json
    {
        "status": "ok",
        "upcoming_reminders": [
            {
                "id": 1,
                "type": "medication_reminder",
                "title": "Give Amoxicillin",
                "body": "Give 1 tablet now",
                "scheduled_at": "2026-06-26T10:00:00Z",
                "pet_id": 5,
                "data": {"medication_name": "Amoxicillin", "dosage": "1 tablet"}
            }
        ],
        "vaccine_reminders": [...],
        "medication_reminders": [...],
        "unread_count": 3,
        "loaded_at": "2026-06-26T08:00:00Z"
    }
    ```
    """
    from datetime import datetime, timezone

    effective_user_id = user_id if user_id else _get_current_user_id(request)

    with emr.session() as session:
        notifications = emr.list_upcoming_notifications(
            session=session,
            user_id=effective_user_id,
            hours_ahead=hours_ahead,
            limit=50,
        )

        # Filter by pet_id if specified
        if pet_id:
            notifications = [n for n in notifications if n.pet_id == pet_id]

        vaccine_reminders = [n for n in notifications if n.type == "vaccine_reminder"]
        medication_reminders = [n for n in notifications if n.type == "medication_reminder"]
        other_reminders = [n for n in notifications if n.type not in ("vaccine_reminder", "medication_reminder")]

        _, _, pending_count, unread_count = emr.list_notifications_by_user(
            session=session,
            user_id=effective_user_id,
            limit=1,
            offset=0,
        )

        def _serialize_notif(n: Notification) -> dict[str, Any]:
            return {
                "id": n.id,
                "type": n.type,
                "channel": n.channel,
                "title": n.title,
                "body": n.body,
                "scheduled_at": n.scheduled_at.isoformat() if n.scheduled_at else None,
                "pet_id": n.pet_id,
                "data": n.data,
                "status": n.status,
            }

        return {
            "status": "ok",
            "upcoming_reminders": [_serialize_notif(n) for n in notifications],
            "vaccine_reminders": [_serialize_notif(n) for n in vaccine_reminders],
            "medication_reminders": [_serialize_notif(n) for n in medication_reminders],
            "other_reminders": [_serialize_notif(n) for n in other_reminders],
            "counts": {
                "total_upcoming": len(notifications),
                "vaccine": len(vaccine_reminders),
                "medication": len(medication_reminders),
                "other": len(other_reminders),
                "pending_overall": pending_count,
                "unread_overall": unread_count,
            },
            "loaded_at": datetime.now(timezone.utc).isoformat(),
        }


@router.get("/{notif_id}", response_model=NotificationResponse)
def get_notification(
    notif_id: int,
    request: Request,
    emr: EMRService = Depends(get_emr_service),
) -> NotificationResponse:
    """Get a single notification by ID.

    Returns 404 if notification doesn't exist or doesn't belong to the current user.
    """
    user_id = _get_current_user_id(request)

    with emr.session() as session:
        notif = emr.get_notification_for_user(session, notif_id, user_id)
        if not notif:
            raise HTTPException(
                status_code=404,
                detail=f"Notification {notif_id} not found or access denied",
            )
        return NotificationResponse.model_validate(notif)


@router.post("/{notif_id}/confirm", response_model=NotificationResponse)
def confirm_notification(
    notif_id: int,
    req: NotificationConfirmRequest,
    request: Request,
    emr: EMRService = Depends(get_emr_service),
) -> NotificationResponse:
    """Confirm a notification (mark as read, clicked, dismissed, or snoozed).

    **Actions:**
    - `read`: Mark notification as read (most common for in-app)
    - `clicked`: User tapped/clicked on the notification
    - `dismissed`: User swiped away or dismissed
    - `snoozed`: User wants to be reminded later (requires `snooze_minutes`)

    **Example request (snooze):**
    ```json
    {
        "action": "snoozed",
        "snooze_minutes": 60
    }
    ```
    """
    user_id = _get_current_user_id(request)

    if req.action == "snoozed" and req.snooze_minutes is None:
        raise HTTPException(
            status_code=400,
            detail="snooze_minutes is required when action='snoozed'",
        )

    with emr.session() as session:
        notif = emr.confirm_notification(
            session=session,
            notif_id=notif_id,
            user_id=user_id,
            action=req.action,
            snooze_minutes=req.snooze_minutes,
        )
        if not notif:
            raise HTTPException(
                status_code=404,
                detail=f"Notification {notif_id} not found or access denied",
            )
        session.refresh(notif)
        return NotificationResponse.model_validate(notif)


@router.patch("/{notif_id}", response_model=NotificationResponse, dependencies=[Depends(require_vet)])
def update_notification(
    notif_id: int,
    req: NotificationUpdate,
    request: Request,
    emr: EMRService = Depends(get_emr_service),
) -> NotificationResponse:
    """Update a notification (admin/vet only).

    Can update: title, body, data, scheduled_at, status
    """
    user_id = _get_current_user_id(request)

    with emr.session() as session:
        notif = emr.get_notification_for_user(session, notif_id, user_id)
        if not notif:
            raise HTTPException(
                status_code=404,
                detail=f"Notification {notif_id} not found or access denied",
            )

        update_data = req.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(notif, key, value)

        session.flush()
        session.refresh(notif)
        return NotificationResponse.model_validate(notif)
