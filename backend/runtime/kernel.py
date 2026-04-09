"""
DelegateRuntime: lifecycle manager for all delegate workers.

Manages:
- Per-delegate pause/resume state
- Flexible scheduler with configurable intervals per delegate
- One-shot scheduled tasks (e.g., "check on this opportunity in 3 days")
- Graceful shutdown of all background tasks
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, Coroutine, Optional

logger = logging.getLogger(__name__)

_runtime: Optional["DelegateRuntime"] = None


def get_runtime() -> Optional["DelegateRuntime"]:
    return _runtime


def set_runtime(runtime: "DelegateRuntime") -> None:
    global _runtime
    _runtime = runtime


@dataclass
class ScheduledJob:
    """A recurring or one-shot job."""
    name: str
    delegate_id: str
    interval_seconds: int
    callback: Callable[[], Coroutine]
    one_shot: bool = False
    fire_at: Optional[datetime] = None  # For one-shot jobs


class DelegateRuntime:
    def __init__(self):
        self._paused: set[str] = set()
        self._tasks: list[asyncio.Task] = []
        self._jobs: list[ScheduledJob] = []
        self._one_shot_tasks: list[asyncio.Task] = []

    async def pause(self, delegate_id: str) -> None:
        self._paused.add(delegate_id)
        logger.info("Delegate %s paused", delegate_id)

    async def resume(self, delegate_id: str) -> None:
        self._paused.discard(delegate_id)
        logger.info("Delegate %s resumed", delegate_id)

    def is_paused(self, delegate_id: str) -> bool:
        return delegate_id in self._paused

    def schedule_recurring(
        self, name: str, delegate_id: str, interval_seconds: int, callback: Callable
    ) -> None:
        """Register a recurring job. Call before start()."""
        self._jobs.append(ScheduledJob(
            name=name,
            delegate_id=delegate_id,
            interval_seconds=interval_seconds,
            callback=callback,
        ))

    async def schedule_one_shot(
        self, name: str, delegate_id: str, fire_at: datetime, callback: Callable
    ) -> None:
        """Schedule a one-shot task at a specific time."""
        delay = (fire_at - datetime.now(timezone.utc)).total_seconds()
        if delay < 0:
            delay = 0

        async def _run_one_shot():
            await asyncio.sleep(delay)
            if not self.is_paused(delegate_id):
                try:
                    logger.info("One-shot job '%s' firing", name)
                    await callback()
                except Exception:
                    logger.exception("One-shot job '%s' failed", name)

        task = asyncio.create_task(_run_one_shot(), name=f"oneshot-{name}")
        self._one_shot_tasks.append(task)
        logger.info("Scheduled one-shot '%s' for %s (delay=%.0fs)", name, fire_at, delay)

    async def start(self) -> None:
        """Start all registered recurring jobs plus the default recruiter poll."""
        # Register default recruiter poll if no custom jobs registered
        if not any(j.delegate_id == "recruiter" for j in self._jobs):
            self.schedule_recurring(
                name="recruiter-poll",
                delegate_id="recruiter",
                interval_seconds=0,  # Uses settings value
                callback=self._run_recruiter_pipeline,
            )

        for job in self._jobs:
            task = asyncio.create_task(
                self._poll_loop(job), name=job.name
            )
            self._tasks.append(task)
            logger.info("Started job '%s' (interval=%ds)", job.name, job.interval_seconds)

    async def stop(self) -> None:
        """Graceful shutdown of all background tasks."""
        all_tasks = self._tasks + self._one_shot_tasks
        for task in all_tasks:
            task.cancel()
        if all_tasks:
            await asyncio.gather(*all_tasks, return_exceptions=True)
        self._tasks.clear()
        self._one_shot_tasks.clear()
        logger.info("All runtime tasks stopped")

    def get_status(self) -> dict:
        """Return runtime status for monitoring."""
        return {
            "paused_delegates": list(self._paused),
            "active_jobs": [
                {"name": j.name, "delegate": j.delegate_id, "interval": j.interval_seconds}
                for j in self._jobs
            ],
            "pending_one_shots": len([t for t in self._one_shot_tasks if not t.done()]),
        }

    # ─── Internal polling loop ─────────────────────────────────────────────────

    async def _poll_loop(self, job: ScheduledJob) -> None:
        """Generic polling loop for recurring jobs."""
        from config.settings import settings

        interval = job.interval_seconds or settings.email_poll_interval_seconds

        # Initial delay so the server fully starts before first run
        await asyncio.sleep(5)

        while True:
            try:
                if not self.is_paused(job.delegate_id):
                    logger.info("Job '%s': running", job.name)
                    await job.callback()
                else:
                    logger.debug("Job '%s': delegate paused, skipping", job.name)
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("Job '%s' error — will retry next interval", job.name)

            await asyncio.sleep(interval)

    # ─── Default recruiter pipeline ────────────────────────────────────────────

    @staticmethod
    async def _run_recruiter_pipeline() -> None:
        """Run the recruiter pipeline once."""
        from config.settings import settings
        from memory.graph import MemoryGraph
        from runtime.event_bus import get_event_bus
        from delegates.recruiter.pipeline import RecruiterPipeline
        from skills.email.mock import MockEmailProvider

        pipeline = RecruiterPipeline(
            email_provider=MockEmailProvider(),
            graph=MemoryGraph(),
            event_bus=get_event_bus(),
            llm_enabled=bool(settings.openai_api_key),
        )
        ctx = await pipeline.run()
        logger.info(
            "Recruiter pipeline complete: %d emails, %d opportunities, %d events",
            len(ctx.emails_ingested),
            len(ctx.opportunities),
            len(ctx.events_emitted),
        )
        if ctx.errors:
            logger.warning("Recruiter pipeline errors: %s", ctx.errors)
