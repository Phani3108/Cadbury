"""Calendar API routes — slots, bookings, and event management."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from memory.graph import MemoryGraph
from memory.models import DelegateEvent, EventType
from skills.calendar.mock import MockCalendarProvider
from delegates.calendar.conflict_checker import find_available_slots

router = APIRouter(prefix="/v1/calendar", tags=["calendar"])

# Shared instances (replaced with DI in production)
_provider = MockCalendarProvider()
_graph = MemoryGraph()


# ─── Request / Response schemas ──────────────────────────────────────────────


class BookRequest(BaseModel):
    """Body for the POST /book endpoint."""

    opportunity_id: str
    slot_start: datetime
    slot_end: datetime
    title: str = "Interview"
    attendees: list[str] = Field(default_factory=list)


class CalendarEventOut(BaseModel):
    """Serialised calendar event returned by the API."""

    event_id: str
    title: str
    start: datetime
    end: datetime
    attendees: list[str] = Field(default_factory=list)
    opportunity_id: Optional[str] = None
    cancelled: bool = False


# Module-level store mapping event_id -> metadata (supplements the provider)
_event_meta: dict[str, dict] = {}


# ─── Routes ──────────────────────────────────────────────────────────────────


@router.get("/slots")
async def get_available_slots(
    from_date: Optional[datetime] = Query(None, description="Start of search window (ISO 8601)"),
    to_date: Optional[datetime] = Query(None, description="End of search window (ISO 8601)"),
    duration_mins: int = Query(60, ge=15, le=480, description="Desired slot duration in minutes"),
):
    """
    Return available calendar slots within the requested window.

    If ``from_date`` / ``to_date`` are omitted the search defaults to
    tomorrow through 14 days from now.
    """
    now = datetime.now(timezone.utc)
    start = from_date or (now + timedelta(days=1))
    end = to_date or (now + timedelta(days=14))

    if end <= start:
        raise HTTPException(400, "to_date must be after from_date")

    try:
        busy = await _provider.get_busy_periods(start=start, end=end)
    except Exception as exc:
        raise HTTPException(502, f"Calendar provider error: {exc}") from exc

    days_ahead = max(1, (end - start).days)
    slots = find_available_slots(
        busy_periods=busy,
        duration_minutes=duration_mins,
        days_ahead=days_ahead,
        working_hours=(9, 18),
        max_slots=10,
    )

    return {
        "slots": [
            {
                "start": s["start"].isoformat(),
                "end": s["end"].isoformat(),
                "label": s["label"],
            }
            for s in slots
        ],
        "count": len(slots),
    }


@router.post("/book", response_model=CalendarEventOut)
async def book_slot(body: BookRequest):
    """
    Book a calendar slot.

    Creates an event via the calendar provider and persists a
    ``CALENDAR_BOOKED`` delegate event to the memory graph.
    """
    if body.slot_end <= body.slot_start:
        raise HTTPException(400, "slot_end must be after slot_start")

    # Check for conflicts before booking
    busy = await _provider.get_busy_periods(start=body.slot_start, end=body.slot_end)
    for period in busy:
        if body.slot_start < period["end"] and body.slot_end > period["start"]:
            raise HTTPException(
                409,
                "Time slot conflicts with an existing calendar event",
            )

    try:
        result = await _provider.create_event(
            title=body.title,
            start=body.slot_start,
            end=body.slot_end,
            attendees=body.attendees,
            tentative=False,
        )
    except Exception as exc:
        raise HTTPException(502, f"Calendar provider error: {exc}") from exc

    event_id = result["event_id"]

    # Persist metadata for the /events listing
    _event_meta[event_id] = {
        "event_id": event_id,
        "title": body.title,
        "start": body.slot_start,
        "end": body.slot_end,
        "attendees": body.attendees,
        "opportunity_id": body.opportunity_id,
        "cancelled": False,
    }

    # Emit a delegate event for audit trail
    delegate_event = DelegateEvent(
        delegate_id="calendar",
        event_type=EventType.CALENDAR_BOOKED,
        summary=f"Booked: {body.title} ({body.slot_start.isoformat()} - {body.slot_end.isoformat()})",
        payload={
            "calendar_event_id": event_id,
            "opportunity_id": body.opportunity_id,
            "title": body.title,
            "start": body.slot_start.isoformat(),
            "end": body.slot_end.isoformat(),
            "attendees": body.attendees,
        },
    )
    await _graph.save_event(delegate_event)

    return CalendarEventOut(**_event_meta[event_id])


@router.get("/events", response_model=list[CalendarEventOut])
async def list_events():
    """List all calendar events, sorted by start time descending."""
    events = sorted(
        _event_meta.values(),
        key=lambda e: e["start"],
        reverse=True,
    )
    return [CalendarEventOut(**e) for e in events]


@router.post("/events/{event_id}/cancel")
async def cancel_event(event_id: str):
    """Cancel a calendar event by its ID."""
    if event_id not in _event_meta:
        raise HTTPException(404, "Event not found")

    meta = _event_meta[event_id]
    if meta.get("cancelled"):
        raise HTTPException(400, "Event is already cancelled")

    success = await _provider.cancel_event(event_id)
    if not success:
        raise HTTPException(502, "Calendar provider failed to cancel event")

    meta["cancelled"] = True

    # Emit audit event
    delegate_event = DelegateEvent(
        delegate_id="calendar",
        event_type=EventType.CALENDAR_BOOKED,
        summary=f"Cancelled: {meta['title']} ({meta['start'].isoformat()})",
        payload={
            "calendar_event_id": event_id,
            "opportunity_id": meta.get("opportunity_id"),
            "action": "cancel",
        },
    )
    await _graph.save_event(delegate_event)

    return {"status": "cancelled", "event_id": event_id}
