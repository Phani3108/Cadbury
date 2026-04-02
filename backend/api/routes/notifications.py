"""
Notifications API — in-memory notification store with CRUD endpoints.

Provides a notification system for surfacing events like new approvals,
high-match opportunities, auto-actions, and digest readiness to the UI.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/notifications", tags=["notifications"])


# ─── Models ──────────────────────────────────────────────────────────────────

class Notification(BaseModel):
    notification_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str           # new_approval, high_match, auto_acted, digest_ready, threshold_crossed
    title: str
    body: str
    link: str = ""      # deep link into the UI
    read: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class NotificationCreate(BaseModel):
    """Request body for creating a notification (unused in API but useful for validation)."""
    type: str
    title: str
    body: str
    link: str = ""


# ─── In-memory store (to be migrated to DB later) ───────────────────────────

_notifications: list[Notification] = []


# ─── Helper functions (callable from the pipeline) ──────────────────────────

def create_notification(
    type: str,
    title: str,
    body: str,
    link: str = "",
) -> Notification:
    """
    Create and store a new notification.

    This function can be called from anywhere in the pipeline (e.g., from
    the recruiter delegate when a high-match opportunity is found, or from
    the approval system when a new approval is created).

    Args:
        type: Notification type (new_approval, high_match, auto_acted,
              digest_ready, threshold_crossed).
        title: Short notification title.
        body: Notification body text.
        link: Optional deep link into the UI.

    Returns:
        The created Notification object.
    """
    notification = Notification(
        type=type,
        title=title,
        body=body,
        link=link,
    )
    _notifications.append(notification)
    logger.info(
        "Notification created: [%s] %s (id=%s)",
        type, title, notification.notification_id,
    )
    return notification


def get_notifications_store() -> list[Notification]:
    """Return a reference to the in-memory notification store (for testing)."""
    return _notifications


def clear_notifications() -> None:
    """Clear all notifications (primarily for testing)."""
    _notifications.clear()


# ─── Endpoints ───────────────────────────────────────────────────────────────

@router.get("")
async def list_notifications(
    unread_only: bool = Query(default=False, description="If true, return only unread notifications"),
    limit: int = Query(default=20, ge=1, le=200, description="Max notifications to return"),
):
    """
    List notifications, optionally filtered to unread only.

    Returns notifications sorted by creation time (newest first).
    """
    items = _notifications
    if unread_only:
        items = [n for n in items if not n.read]

    # Sort newest first and apply limit
    sorted_items = sorted(items, key=lambda n: n.created_at, reverse=True)
    return sorted_items[:limit]


@router.post("/{notification_id}/read")
async def mark_as_read(notification_id: str):
    """Mark a single notification as read."""
    for notification in _notifications:
        if notification.notification_id == notification_id:
            notification.read = True
            return {"status": "ok", "notification_id": notification_id}

    raise HTTPException(status_code=404, detail="Notification not found")


@router.post("/read-all")
async def mark_all_as_read():
    """Mark all notifications as read."""
    count = 0
    for notification in _notifications:
        if not notification.read:
            notification.read = True
            count += 1

    return {"status": "ok", "marked_read": count}
