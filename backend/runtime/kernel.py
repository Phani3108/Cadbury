"""
DelegateRuntime: lifecycle manager for all delegate workers.
Manages pause/resume state and runs the recruiter polling loop.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)

_runtime: Optional["DelegateRuntime"] = None


def get_runtime() -> Optional["DelegateRuntime"]:
    return _runtime


def set_runtime(runtime: "DelegateRuntime") -> None:
    global _runtime
    _runtime = runtime


class DelegateRuntime:
    def __init__(self):
        self._paused: set[str] = set()
        self._tasks: list[asyncio.Task] = []

    async def pause(self, delegate_id: str) -> None:
        self._paused.add(delegate_id)

    async def resume(self, delegate_id: str) -> None:
        self._paused.discard(delegate_id)

    def is_paused(self, delegate_id: str) -> bool:
        return delegate_id in self._paused

    async def start(self) -> None:
        """Start background polling loops for all delegates."""
        task = asyncio.create_task(self._recruiter_poll_loop(), name="recruiter-poll")
        self._tasks.append(task)
        logger.info("Recruiter polling loop started")

    async def stop(self) -> None:
        """Graceful shutdown of all background tasks."""
        for task in self._tasks:
            task.cancel()
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()

    # ─── Recruiter polling loop ────────────────────────────────────────────────

    async def _recruiter_poll_loop(self) -> None:
        """
        Every `email_poll_interval_seconds` seconds, run the recruiter pipeline
        (using MockEmailProvider so no MS Graph credentials needed for MVP).
        Skips execution if the delegate is paused.
        """
        from config.settings import settings
        from memory.graph import MemoryGraph
        from runtime.event_bus import get_event_bus
        from delegates.recruiter.pipeline import RecruiterPipeline
        from skills.email.mock import MockEmailProvider

        interval = settings.email_poll_interval_seconds

        # Initial delay so the server fully starts before first run
        await asyncio.sleep(5)

        while True:
            try:
                if not self.is_paused("recruiter"):
                    logger.info("Recruiter poll: running pipeline")
                    pipeline = RecruiterPipeline(
                        email_provider=MockEmailProvider(),
                        graph=MemoryGraph(),
                        event_bus=get_event_bus(),
                        llm_enabled=bool(settings.openai_api_key),
                    )
                    ctx = await pipeline.run()
                    logger.info(
                        "Recruiter poll complete: %d emails, %d opportunities, %d events",
                        len(ctx.emails_ingested),
                        len(ctx.opportunities),
                        len(ctx.events_emitted),
                    )
                    if ctx.errors:
                        logger.warning("Recruiter poll errors: %s", ctx.errors)
                else:
                    logger.debug("Recruiter poll: delegate paused, skipping")
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("Recruiter poll loop error — will retry next interval")

            await asyncio.sleep(interval)
