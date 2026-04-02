"""Abstract base class for calendar providers."""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime


class CalendarProvider(ABC):
    """
    Interface for calendar integration.

    Concrete implementations may connect to Google Calendar, Microsoft
    Outlook, or return mock data for development/testing.
    """

    @abstractmethod
    async def get_busy_periods(
        self, start: datetime, end: datetime
    ) -> list[dict]:
        """
        Return busy periods within the given time range.

        Returns
        -------
        list[dict]
            Each dict has ``start`` (datetime) and ``end`` (datetime) keys.
        """

    @abstractmethod
    async def create_event(
        self,
        title: str,
        start: datetime,
        end: datetime,
        attendees: list[str] | None = None,
        tentative: bool = False,
    ) -> dict:
        """
        Create a calendar event.

        Returns
        -------
        dict
            ``{event_id, title, start, end}``
        """

    @abstractmethod
    async def cancel_event(self, event_id: str) -> bool:
        """
        Cancel a calendar event by its ID.

        Returns
        -------
        bool
            True if the event was successfully cancelled.
        """
