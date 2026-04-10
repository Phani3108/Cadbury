"""
Health Delegate Pipeline — track routines, manage appointments, send reminders.

Pipeline: Schedule → Track → Remind → Alert → Act
"""
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from memory.graph import (
    save_health_routine,
    list_health_routines,
    save_health_appointment,
    list_health_appointments,
    save_event,
    save_approval,
    log_decision,
)
from memory.models import (
    HealthRoutine,
    HealthAppointment,
    DelegateEvent,
    EventType,
    ApprovalItem,
    DecisionLog,
)
from runtime.event_bus import publish_event

logger = logging.getLogger(__name__)

DELEGATE_ID = "health"


@dataclass
class HealthContext:
    routines_checked: list[HealthRoutine] = field(default_factory=list)
    reminders: list[str] = field(default_factory=list)
    alerts: list[str] = field(default_factory=list)
    appointments_flagged: list[HealthAppointment] = field(default_factory=list)
    events_emitted: list[DelegateEvent] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))


class HealthPipeline:
    def __init__(self, graph=None, event_bus=None, llm_enabled: bool = False):
        self.graph = graph
        self.event_bus = event_bus
        self.llm_enabled = llm_enabled

    async def run(self) -> HealthContext:
        ctx = HealthContext()
        try:
            await self._stage_1_schedule(ctx)
            await self._stage_2_track(ctx)
            await self._stage_3_remind(ctx)
            await self._stage_4_alert(ctx)
            await self._stage_5_act(ctx)
        except Exception as exc:
            ctx.errors.append(f"Pipeline error: {exc}")
            logger.exception("Health pipeline error")
        return ctx

    async def _stage_1_schedule(self, ctx: HealthContext) -> None:
        """Check for upcoming and overdue appointments."""
        appointments = await list_health_appointments()
        now = datetime.now(timezone.utc)

        for apt in appointments:
            if apt.status == "scheduled" and apt.scheduled_at:
                if apt.scheduled_at < now:
                    apt.status = "overdue"
                    await save_health_appointment(apt)
                    ctx.appointments_flagged.append(apt)
                elif apt.scheduled_at < now + timedelta(days=1):
                    # Upcoming within 24 hours
                    ctx.reminders.append(
                        f"Appointment tomorrow: {apt.title} with {apt.provider or 'TBD'}"
                    )
                    event = DelegateEvent(
                        delegate_id=DELEGATE_ID,
                        event_type=EventType.HEALTH_APPOINTMENT,
                        trace_id=ctx.trace_id,
                        summary=f"Upcoming: {apt.title} in 24h",
                        payload={"appointment_id": apt.appointment_id, "title": apt.title},
                    )
                    await save_event(event)
                    await publish_event(event)
                    ctx.events_emitted.append(event)

    async def _stage_2_track(self, ctx: HealthContext) -> None:
        """Check routine compliance and streaks."""
        routines = await list_health_routines(active_only=True)
        now = datetime.now(timezone.utc)

        for routine in routines:
            ctx.routines_checked.append(routine)
            if routine.last_logged:
                days_missed = (now - routine.last_logged).days
                if routine.frequency == "daily" and days_missed >= 1:
                    # Streak broken
                    if days_missed == 1:
                        routine.streak_days = 0
                        await save_health_routine(routine)
                elif routine.frequency == "weekly" and days_missed >= 7:
                    routine.streak_days = 0
                    await save_health_routine(routine)

    async def _stage_3_remind(self, ctx: HealthContext) -> None:
        """Generate reminders for routines due today."""
        now = datetime.now(timezone.utc)

        for routine in ctx.routines_checked:
            should_remind = False
            if routine.frequency == "daily":
                # Remind if not logged today
                if not routine.last_logged or routine.last_logged.date() < now.date():
                    should_remind = True
            elif routine.frequency == "weekly":
                if not routine.last_logged or (now - routine.last_logged).days >= 7:
                    should_remind = True

            if should_remind:
                reminder = f"Reminder: {routine.name} ({routine.routine_type})"
                ctx.reminders.append(reminder)
                event = DelegateEvent(
                    delegate_id=DELEGATE_ID,
                    event_type=EventType.HEALTH_REMINDER,
                    trace_id=ctx.trace_id,
                    summary=reminder,
                    payload={"routine_id": routine.routine_id, "name": routine.name,
                             "streak": routine.streak_days},
                )
                await save_event(event)
                await publish_event(event)
                ctx.events_emitted.append(event)

    async def _stage_4_alert(self, ctx: HealthContext) -> None:
        """Alert on overdue appointments and missed routines."""
        for apt in ctx.appointments_flagged:
            alert = f"Overdue appointment: {apt.title}"
            ctx.alerts.append(alert)
            event = DelegateEvent(
                delegate_id=DELEGATE_ID,
                event_type=EventType.HEALTH_ALERT,
                trace_id=ctx.trace_id,
                summary=alert,
                payload={"appointment_id": apt.appointment_id, "title": apt.title},
            )
            await save_event(event)
            await publish_event(event)
            ctx.events_emitted.append(event)

        # Alert if any routine has been missed 3+ days
        for routine in ctx.routines_checked:
            now = datetime.now(timezone.utc)
            if routine.last_logged and routine.frequency == "daily":
                days_missed = (now - routine.last_logged).days
                if days_missed >= 3:
                    alert = f"Missed {routine.name} for {days_missed} days"
                    ctx.alerts.append(alert)
                    event = DelegateEvent(
                        delegate_id=DELEGATE_ID,
                        event_type=EventType.HEALTH_ALERT,
                        trace_id=ctx.trace_id,
                        summary=alert,
                        payload={"routine_id": routine.routine_id, "days_missed": days_missed},
                    )
                    await save_event(event)
                    await publish_event(event)
                    ctx.events_emitted.append(event)

    async def _stage_5_act(self, ctx: HealthContext) -> None:
        """Create approvals for appointment bookings — never auto-book."""
        for apt in ctx.appointments_flagged:
            approval = ApprovalItem(
                delegate_id=DELEGATE_ID,
                event_id=ctx.events_emitted[-1].event_id if ctx.events_emitted else "",
                action="reschedule_appointment",
                action_label=f"Reschedule: {apt.title}",
                context_summary=f"Overdue: {apt.title} with {apt.provider}",
                risk_score=0.3,
                reasoning="Appointment overdue — needs rescheduling",
            )
            await save_approval(approval)
            event = DelegateEvent(
                delegate_id=DELEGATE_ID,
                event_type=EventType.APPROVAL_REQUESTED,
                trace_id=ctx.trace_id,
                requires_approval=True,
                summary=f"Approval needed: reschedule {apt.title}",
                payload={"approval_id": approval.approval_id, "appointment_id": apt.appointment_id},
            )
            await save_event(event)
            await publish_event(event)
            ctx.events_emitted.append(event)
