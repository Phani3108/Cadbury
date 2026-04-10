"""Calendar Delegate — 4-stage pipeline for scheduling management."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from memory.graph import MemoryGraph
from memory.models import (
    ApprovalItem,
    DelegateEvent,
    EventType,
)
from runtime.tracker import tracked_pipeline
from skills.calendar.provider import CalendarProvider
from delegates.calendar.conflict_checker import find_available_slots


# ─── Data Classes ────────────────────────────────────────────────────────────


@dataclass
class CalendarRequest:
    """Inbound request to schedule a calendar event."""

    opportunity_id: str
    company: str
    role: str
    contact_email: str
    contact_name: str
    meeting_type: str = "interview"  # interview, intro_call, follow_up
    duration_minutes: int = 60
    preferred_time: str = ""  # e.g. "morning", "afternoon"


@dataclass
class CalendarContext:
    """Mutable state carried through the 4-stage calendar pipeline."""

    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    request: CalendarRequest | None = None
    available_slots: list[dict] = field(default_factory=list)  # [{start, end, label}]
    draft_message: str = ""
    events_emitted: list[DelegateEvent] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def emit(self, event: DelegateEvent) -> DelegateEvent:
        """Record an emitted event and return it."""
        self.events_emitted.append(event)
        return event


# ─── Pipeline ────────────────────────────────────────────────────────────────


class CalendarPipeline:
    """
    Orchestrates a 4-stage calendar scheduling pipeline.

    Stage 1 — Parse:       Extract meeting details from the request.
    Stage 2 — Find Slots:  Query the calendar provider for availability.
    Stage 3 — Propose:     Generate a draft reply proposing time slots.
    Stage 4 — Act:         Create an ApprovalItem for human review.
    """

    def __init__(
        self,
        calendar_provider: CalendarProvider,
        graph: MemoryGraph,
        event_bus=None,
    ):
        self.calendar_provider = calendar_provider
        self.graph = graph
        self.event_bus = event_bus

    @tracked_pipeline("calendar")
    async def run(self, request: CalendarRequest) -> CalendarContext:
        """Execute all 4 pipeline stages and return the completed context."""
        ctx = CalendarContext()
        ctx.request = request

        await self._stage_1_parse(ctx)
        await self._stage_2_find_slots(ctx)
        await self._stage_3_propose(ctx)
        await self._stage_4_act(ctx)

        return ctx

    # ─── Stage 1: PARSE ──────────────────────────────────────────────────────

    async def _stage_1_parse(self, ctx: CalendarContext) -> None:
        """
        Parse and validate the calendar request.
        Extract meeting type, duration, attendees, and preferred time window.
        """
        req = ctx.request
        if req is None:
            ctx.errors.append("No calendar request provided")
            return

        # Validate required fields
        if not req.contact_email:
            ctx.errors.append("Missing contact email")
            return

        if req.duration_minutes < 15 or req.duration_minutes > 480:
            ctx.errors.append(
                f"Invalid duration: {req.duration_minutes} minutes "
                f"(must be between 15 and 480)"
            )
            return

        # Normalise meeting type
        valid_types = {"interview", "intro_call", "follow_up"}
        if req.meeting_type not in valid_types:
            req.meeting_type = "interview"

        event = DelegateEvent(
            delegate_id="calendar",
            event_type=EventType.EMAIL_RECEIVED,
            trace_id=ctx.trace_id,
            summary=(
                f"Calendar request parsed: {req.meeting_type} with "
                f"{req.contact_name} ({req.company}) — {req.duration_minutes} min"
            ),
            payload={
                "opportunity_id": req.opportunity_id,
                "company": req.company,
                "role": req.role,
                "contact_email": req.contact_email,
                "contact_name": req.contact_name,
                "meeting_type": req.meeting_type,
                "duration_minutes": req.duration_minutes,
                "preferred_time": req.preferred_time,
            },
        )
        await self.graph.save_event(event)
        if self.event_bus:
            await self.event_bus.publish_event(event)
        ctx.emit(event)

    # ─── Stage 2: FIND SLOTS ─────────────────────────────────────────────────

    async def _stage_2_find_slots(self, ctx: CalendarContext) -> None:
        """
        Query the calendar provider for free/busy data and find the
        top 3 available slots in the next 14 days during working hours
        (9 AM - 6 PM IST, Monday - Friday).
        """
        if ctx.errors:
            return

        req = ctx.request
        assert req is not None

        now = datetime.now(timezone.utc)
        window_start = now
        window_end = now + timedelta(days=14)

        try:
            busy_periods = await self.calendar_provider.get_busy_periods(
                start=window_start,
                end=window_end,
            )
        except Exception as exc:
            ctx.errors.append(f"Failed to fetch busy periods: {exc}")
            return

        # Apply preferred_time filter to working hours
        working_start, working_end = 9, 18  # IST working hours
        if req.preferred_time == "morning":
            working_end = 12
        elif req.preferred_time == "afternoon":
            working_start = 13

        slots = find_available_slots(
            busy_periods=busy_periods,
            duration_minutes=req.duration_minutes,
            days_ahead=14,
            working_hours=(working_start, working_end),
            max_slots=3,
        )

        ctx.available_slots = slots

        event = DelegateEvent(
            delegate_id="calendar",
            event_type=EventType.OPPORTUNITY_EXTRACTED,
            trace_id=ctx.trace_id,
            summary=f"Found {len(slots)} available slot(s) for {req.company}",
            payload={
                "opportunity_id": req.opportunity_id,
                "slots_found": len(slots),
                "slots": [
                    {"start": s["start"].isoformat(), "end": s["end"].isoformat(), "label": s["label"]}
                    for s in slots
                ],
            },
        )
        await self.graph.save_event(event)
        if self.event_bus:
            await self.event_bus.publish_event(event)
        ctx.emit(event)

    # ─── Stage 3: PROPOSE ────────────────────────────────────────────────────

    async def _stage_3_propose(self, ctx: CalendarContext) -> None:
        """Generate a draft reply proposing the available time slots."""
        if ctx.errors:
            return

        req = ctx.request
        assert req is not None

        if not ctx.available_slots:
            ctx.draft_message = (
                f"Hi {req.contact_name},\n\n"
                f"Thank you for reaching out about the {req.role} position at "
                f"{req.company}. Unfortunately, I don't have any available slots "
                f"in the next two weeks. Could you suggest some times that work "
                f"on your end?\n\n"
                f"Best regards"
            )
        else:
            slot_lines = []
            for i, slot in enumerate(ctx.available_slots, 1):
                slot_lines.append(f"  {i}. {slot['label']}")

            meeting_label = req.meeting_type.replace("_", " ")
            ctx.draft_message = (
                f"Hi {req.contact_name},\n\n"
                f"Thank you for reaching out about the {req.role} position at "
                f"{req.company}. I'd be happy to schedule a {meeting_label}. "
                f"Here are a few times that work for me:\n\n"
                + "\n".join(slot_lines)
                + "\n\n"
                f"Each slot is {req.duration_minutes} minutes. Please let me know "
                f"which works best for you, and I'll send over a calendar invite.\n\n"
                f"Best regards"
            )

        event = DelegateEvent(
            delegate_id="calendar",
            event_type=EventType.DRAFT_CREATED,
            trace_id=ctx.trace_id,
            summary=f"Draft scheduling reply for {req.company} — {req.role}",
            payload={
                "opportunity_id": req.opportunity_id,
                "draft_preview": (
                    ctx.draft_message[:120] + "..."
                    if len(ctx.draft_message) > 120
                    else ctx.draft_message
                ),
                "slots_proposed": len(ctx.available_slots),
            },
        )
        await self.graph.save_event(event)
        if self.event_bus:
            await self.event_bus.publish_event(event)
        ctx.emit(event)

    # ─── Stage 4: ACT (Human-in-the-Loop gate) ──────────────────────────────

    async def _stage_4_act(self, ctx: CalendarContext) -> None:
        """
        Create an ApprovalItem for human review.
        The user must approve before any calendar invite or reply is sent.
        """
        if ctx.errors:
            return

        req = ctx.request
        assert req is not None

        action = "propose_times" if ctx.available_slots else "propose_times"
        action_label = (
            f"Propose {len(ctx.available_slots)} time slot(s) to {req.contact_name}"
            if ctx.available_slots
            else f"Send no-availability reply to {req.contact_name}"
        )

        approval = ApprovalItem(
            delegate_id="calendar",
            event_id=ctx.events_emitted[-1].event_id if ctx.events_emitted else "",
            opportunity_id=req.opportunity_id,
            action=action,
            action_label=action_label,
            context_summary=(
                f"{req.company} - {req.role} - "
                f"{req.meeting_type.replace('_', ' ')} with {req.contact_name}"
            ),
            draft_content=ctx.draft_message,
            risk_score=0.2,
            reasoning=(
                f"Found {len(ctx.available_slots)} available slot(s) in next 14 days. "
                f"Meeting type: {req.meeting_type}, duration: {req.duration_minutes} min."
            ),
            policy_check={
                "delegate_id": "calendar",
                "action": action,
                "slots_found": len(ctx.available_slots),
                "meeting_type": req.meeting_type,
            },
        )
        await self.graph.save_approval(approval)

        event = DelegateEvent(
            delegate_id="calendar",
            event_type=EventType.APPROVAL_REQUESTED,
            trace_id=ctx.trace_id,
            summary=f"Approval needed: {action_label}",
            payload={
                "approval_id": approval.approval_id,
                "opportunity_id": req.opportunity_id,
                "action": action,
                "action_label": action_label,
            },
            requires_approval=True,
            policy_rules_checked=["calendar.propose_times:review"],
        )
        await self.graph.save_event(event)
        if self.event_bus:
            await self.event_bus.publish_event(event)
            await self.event_bus.publish_typed_event(
                "approval.new", approval.model_dump(mode="json")
            )
        ctx.emit(event)
