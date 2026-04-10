"""API routes for Health delegate."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter
from pydantic import BaseModel

from memory.graph import (
    list_health_routines,
    save_health_routine,
    list_health_appointments,
    save_health_appointment,
)
from memory.models import HealthRoutine, HealthAppointment, HealthRoutineType

router = APIRouter(prefix="/v1/health", tags=["health"])


class RoutineInput(BaseModel):
    name: str
    routine_type: str = "custom"
    frequency: str = "daily"
    time_of_day: str = ""


class AppointmentInput(BaseModel):
    title: str
    provider: str = ""
    appointment_type: str = ""
    scheduled_at: str | None = None
    notes: str = ""


@router.get("/routines")
async def get_routines(active_only: bool = True):
    return await list_health_routines(active_only=active_only)


@router.post("/routines")
async def add_routine(r: RoutineInput):
    routine = HealthRoutine(
        name=r.name,
        routine_type=HealthRoutineType(r.routine_type),
        frequency=r.frequency,
        time_of_day=r.time_of_day,
    )
    await save_health_routine(routine)
    return routine


@router.post("/routines/{routine_id}/log")
async def log_routine(routine_id: str):
    """Log a routine as completed for today."""
    routines = await list_health_routines(active_only=False)
    for routine in routines:
        if routine.routine_id == routine_id:
            now = datetime.now(timezone.utc)
            # Update streak
            if routine.last_logged and routine.last_logged.date() == (now.date()):
                return {"message": "Already logged today", "streak": routine.streak_days}
            if routine.last_logged and (now - routine.last_logged).days <= 1:
                routine.streak_days += 1
            else:
                routine.streak_days = 1
            routine.last_logged = now
            await save_health_routine(routine)
            return {"logged": True, "streak": routine.streak_days}
    return {"error": "Routine not found"}


@router.delete("/routines/{routine_id}")
async def deactivate_routine(routine_id: str):
    routines = await list_health_routines(active_only=False)
    for routine in routines:
        if routine.routine_id == routine_id:
            routine.active = False
            await save_health_routine(routine)
            return {"deactivated": True}
    return {"error": "Routine not found"}


@router.get("/appointments")
async def get_appointments(status: str | None = None):
    return await list_health_appointments(status=status)


@router.post("/appointments")
async def add_appointment(a: AppointmentInput):
    apt = HealthAppointment(
        title=a.title,
        provider=a.provider,
        appointment_type=a.appointment_type,
        scheduled_at=datetime.fromisoformat(a.scheduled_at) if a.scheduled_at else None,
        notes=a.notes,
    )
    await save_health_appointment(apt)
    return apt


@router.post("/check")
async def run_health_check():
    """Run health pipeline (check routines, reminders, alerts)."""
    from delegates.health.pipeline import HealthPipeline

    pipeline = HealthPipeline()
    ctx = await pipeline.run()
    return {
        "routines_checked": len(ctx.routines_checked),
        "reminders": ctx.reminders,
        "alerts": ctx.alerts,
        "errors": ctx.errors,
    }
