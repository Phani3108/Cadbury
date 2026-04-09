"""
Cross-delegate coordination — connects events from one delegate to actions in another.

Currently handles:
- Recruiter CALENDAR_PREBLOCK_REQUESTED → Calendar pipeline pre-block
"""
from __future__ import annotations

import logging

from memory.graph import (
    MemoryGraph,
    get_opportunity,
    get_contact,
    save_calendar_event,
)
from memory.models import (
    CalendarEvent,
    CalendarEventStatus,
    DelegateEvent,
    EventType,
)
from runtime.event_bus import get_event_bus
from delegates.calendar.pipeline import CalendarPipeline, CalendarRequest
from skills.calendar.multi import MultiCalendarProvider

logger = logging.getLogger(__name__)


async def handle_calendar_preblock(event: DelegateEvent) -> None:
    """
    When the recruiter delegate requests a calendar pre-block for a high-match
    opportunity, run the calendar pipeline to find slots and create a preblock.
    """
    payload = event.payload
    opportunity_id = payload.get("opportunity_id")
    company = payload.get("company", "Unknown")
    role = payload.get("role", "Unknown")
    contact_id = payload.get("contact_id", "")

    # Look up the contact email
    contact_email = ""
    contact_name = ""
    if contact_id:
        contact = await get_contact(contact_id)
        if contact:
            contact_email = contact.email
            contact_name = contact.name

    logger.info(
        "Cross-delegate: recruiter → calendar preblock for %s at %s",
        role, company,
    )

    request = CalendarRequest(
        opportunity_id=opportunity_id or "",
        company=company,
        role=role,
        contact_email=contact_email,
        contact_name=contact_name or company,
        meeting_type="interview",
        duration_minutes=60,
    )

    pipeline = CalendarPipeline(
        calendar_provider=MultiCalendarProvider(),
        graph=MemoryGraph(),
        event_bus=get_event_bus(),
    )
    ctx = await pipeline.run(request)

    if ctx.errors:
        logger.warning("Calendar preblock pipeline errors: %s", ctx.errors)
    else:
        logger.info(
            "Calendar preblock complete: %d slots found for %s",
            len(ctx.available_slots), company,
        )


async def dispatch_cross_delegate_event(event: DelegateEvent) -> None:
    """
    Route events that trigger cross-delegate actions.
    Called from the event bus listener.
    """
    if event.event_type == EventType.CALENDAR_PREBLOCK_REQUESTED:
        try:
            await handle_calendar_preblock(event)
        except Exception:
            logger.exception("Failed to handle calendar preblock for event %s", event.event_id)
