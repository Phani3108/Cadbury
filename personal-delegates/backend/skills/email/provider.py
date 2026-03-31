"""Abstract base class for email providers."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


@dataclass
class RawEmail:
    message_id: str
    sender_name: str
    sender_email: str
    subject: str
    body: str
    received_at: datetime
    thread_id: str | None = None


class EmailProvider(ABC):
    """Interface for email ingestion and reply sending."""

    @abstractmethod
    async def list_recruiter_emails(self, limit: int = 20) -> list[RawEmail]:
        """Return unread recruiter emails, newest first."""

    @abstractmethod
    async def send_reply(self, message_id: str, body: str) -> bool:
        """Send a reply to the given message. Returns True on success."""

    @abstractmethod
    async def mark_read(self, message_id: str) -> bool:
        """Mark a message as read."""
