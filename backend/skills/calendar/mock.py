"""Mock calendar provider with hardcoded busy slots for development/testing."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from skills.calendar.provider import CalendarProvider


# Module-level store for mock events
_events: dict[str, dict] = {}


class MockCalendarProvider(CalendarProvider):
    """Returns hardcoded busy periods. Does not call any external service."""

    async def get_busy_periods(
        self, start: datetime, end: datetime
    ) -> list[dict]:
        """
        Return 2-3 hardcoded busy slots relative to the current time.

        The slots simulate a realistic working schedule so the conflict
        checker has something to route around.
        """
        now = datetime.now(timezone.utc)
        tomorrow_10am = (now + timedelta(days=1)).replace(
            hour=4, minute=30, second=0, microsecond=0  # 10:00 IST = 04:30 UTC
        )
        tomorrow_2pm = (now + timedelta(days=1)).replace(
            hour=8, minute=30, second=0, microsecond=0  # 14:00 IST = 08:30 UTC
        )
        day_after_11am = (now + timedelta(days=2)).replace(
            hour=5, minute=30, second=0, microsecond=0  # 11:00 IST = 05:30 UTC
        )

        busy = [
            {
                "start": tomorrow_10am,
                "end": tomorrow_10am + timedelta(hours=1),
            },
            {
                "start": tomorrow_2pm,
                "end": tomorrow_2pm + timedelta(minutes=90),
            },
            {
                "start": day_after_11am,
                "end": day_after_11am + timedelta(hours=1),
            },
        ]

        # Filter to the requested window
        return [
            b
            for b in busy
            if b["end"] > start and b["start"] < end
        ]

    async def create_event(
        self,
        title: str,
        start: datetime,
        end: datetime,
        attendees: list[str] | None = None,
        tentative: bool = False,
    ) -> dict:
        """Store a mock event and return a fake event_id."""
        event_id = f"evt_{uuid.uuid4().hex[:12]}"
        event = {
            "event_id": event_id,
            "title": title,
            "start": start,
            "end": end,
            "attendees": attendees or [],
            "tentative": tentative,
        }
        _events[event_id] = event
        return {
            "event_id": event_id,
            "title": title,
            "start": start,
            "end": end,
        }

    async def cancel_event(self, event_id: str) -> bool:
        """Remove a mock event from the store. Returns False if not found."""
        if event_id in _events:
            del _events[event_id]
            return True
        return False

    # ─── Test helpers ────────────────────────────────────────────────────────

    def get_all_events(self) -> dict[str, dict]:
        """Return a copy of all stored mock events."""
        return dict(_events)

    @staticmethod
    def reset() -> None:
        """Clear all mock events. Useful between test runs."""
        _events.clear()
