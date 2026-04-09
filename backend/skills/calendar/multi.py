"""
Multi-provider calendar — merges availability from all connected calendar providers.

If Google and Microsoft are both connected, busy periods from both are combined
before finding available slots. Falls back to mock for development.
"""
from __future__ import annotations

import logging
from datetime import datetime

from skills.auth.token_store import has_tokens
from skills.calendar.provider import CalendarProvider

logger = logging.getLogger(__name__)


class MultiCalendarProvider(CalendarProvider):
    """Merges busy periods from all connected calendar providers."""

    def __init__(self):
        self._providers: list[CalendarProvider] = []
        self._initialized = False

    async def _ensure_providers(self) -> None:
        """Lazily build the provider list based on connected accounts."""
        if self._initialized:
            return
        self._initialized = True

        if await has_tokens("google"):
            from skills.calendar.google import GoogleCalendarProvider
            self._providers.append(GoogleCalendarProvider())
            logger.info("Google Calendar connected")

        if await has_tokens("microsoft"):
            from skills.calendar.msgraph import MSGraphCalendarProvider
            self._providers.append(MSGraphCalendarProvider())
            logger.info("Microsoft Calendar connected")

        if not self._providers:
            from skills.calendar.mock import MockCalendarProvider
            self._providers.append(MockCalendarProvider())
            logger.info("No calendar providers connected — using mock")

    async def get_busy_periods(
        self, start: datetime, end: datetime
    ) -> list[dict]:
        """Merge busy periods from all connected providers."""
        await self._ensure_providers()
        all_busy: list[dict] = []

        for provider in self._providers:
            try:
                busy = await provider.get_busy_periods(start, end)
                all_busy.extend(busy)
            except Exception:
                logger.exception("Failed to get busy periods from %s", type(provider).__name__)

        # Sort and merge overlapping periods
        return _merge_busy_periods(all_busy)

    async def create_event(
        self,
        title: str,
        start: datetime,
        end: datetime,
        attendees: list[str] | None = None,
        tentative: bool = False,
    ) -> dict:
        """Create an event on the primary provider (first connected)."""
        await self._ensure_providers()
        # Use the first real (non-mock) provider, or fall back to the first available
        provider = self._providers[0]
        return await provider.create_event(title, start, end, attendees, tentative)

    async def cancel_event(self, event_id: str) -> bool:
        """Try to cancel the event on all providers (only one will have it)."""
        await self._ensure_providers()
        for provider in self._providers:
            try:
                if await provider.cancel_event(event_id):
                    return True
            except Exception:
                pass
        return False


def _merge_busy_periods(periods: list[dict]) -> list[dict]:
    """Merge overlapping busy periods into non-overlapping intervals."""
    if not periods:
        return []

    sorted_periods = sorted(periods, key=lambda p: p["start"])
    merged: list[dict] = [sorted_periods[0]]

    for period in sorted_periods[1:]:
        last = merged[-1]
        if period["start"] <= last["end"]:
            # Overlapping — extend the end
            if period["end"] > last["end"]:
                last["end"] = period["end"]
        else:
            merged.append(period)

    return merged
