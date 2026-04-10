"""
Cross-delegate coordination — connects events from one delegate to actions in another.

Handles:
- Recruiter CALENDAR_PREBLOCK_REQUESTED → Calendar pipeline pre-block
- Finance SUBSCRIPTION_FLAGGED → Comms drafts cancellation email
- Learning SKILL_ASSESSED → Shopping searches for relevant books/courses
- Health HEALTH_APPOINTMENT → Calendar blocks time
- Recruiter high-match → Comms drafts "interested" reply
"""
from __future__ import annotations

import logging

from memory.graph import (
    MemoryGraph,
    get_opportunity,
    get_contact,
    save_calendar_event,
    save_event,
)
from memory.models import (
    CalendarEvent,
    CalendarEventStatus,
    CommsMessage,
    DelegateEvent,
    EventType,
    MessageChannel,
    MessagePriority,
)
from runtime.event_bus import get_event_bus, publish_event
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


async def handle_subscription_flagged(event: DelegateEvent) -> None:
    """Finance flags unused subscription → Comms can draft a cancellation message."""
    merchant = event.payload.get("merchant", "Unknown")
    logger.info("Cross-delegate: finance → comms cancellation draft for %s", merchant)

    from delegates.comms.pipeline import CommsPipeline
    msg = CommsMessage(
        channel=MessageChannel.EMAIL,
        sender="system",
        sender_name="Finance Delegate",
        subject=f"Cancel subscription: {merchant}",
        body=f"Your {merchant} subscription has been flagged as potentially unused. Would you like to draft a cancellation message?",
        priority=MessagePriority.NORMAL,
    )
    pipeline = CommsPipeline(llm_enabled=False)
    await pipeline.run([msg])


async def handle_health_appointment(event: DelegateEvent) -> None:
    """Health appointment created → Calendar blocks time."""
    title = event.payload.get("title", "Health appointment")
    appointment_id = event.payload.get("appointment_id", "")
    logger.info("Cross-delegate: health → calendar block for %s", title)

    coord_event = DelegateEvent(
        delegate_id="health",
        event_type=EventType.CALENDAR_PREBLOCK_REQUESTED,
        summary=f"Block time for: {title}",
        payload={
            "company": "Health",
            "role": title,
            "contact_id": "",
            "opportunity_id": appointment_id,
        },
    )
    await save_event(coord_event)
    await publish_event(coord_event)


async def dispatch_cross_delegate_event(event: DelegateEvent) -> None:
    """
    Route events that trigger cross-delegate actions.
    Called from the event bus listener.
    """
    handlers = {
        EventType.CALENDAR_PREBLOCK_REQUESTED: handle_calendar_preblock,
        EventType.SUBSCRIPTION_FLAGGED: handle_subscription_flagged,
        EventType.HEALTH_APPOINTMENT: handle_health_appointment,
    }

    handler = handlers.get(event.event_type)
    if handler:
        try:
            await handler(event)
        except Exception:
            logger.exception(
                "Failed to handle cross-delegate event %s (%s)",
                event.event_type, event.event_id,
            )
