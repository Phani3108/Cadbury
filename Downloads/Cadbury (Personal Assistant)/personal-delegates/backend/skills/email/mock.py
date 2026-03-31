"""Mock email provider with realistic recruiter email samples for development/testing."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from skills.email.provider import EmailProvider, RawEmail

_SAMPLE_EMAILS: list[dict] = [
    {
        "message_id": "msg_001",
        "sender_name": "Sarah Chen",
        "sender_email": "sarah.chen@techrecruit.io",
        "subject": "Senior Product Manager - Fintech Startup (Series B, $180k-$220k)",
        "body": (
            "Hi,\n\nI hope this message finds you well! I'm reaching out because I came across your "
            "profile and I think you'd be a great fit for an exciting opportunity at Luminary Pay, "
            "a Series B fintech startup based in Bangalore (with remote-first policy).\n\n"
            "Role: Senior Product Manager – Payments Core\n"
            "Compensation: ₹80L–₹1Cr base + equity (0.15% - 0.3%)\n"
            "Location: Bangalore / Remote-first\n"
            "Company size: ~120 people\n\n"
            "The role focuses on owning the payments infrastructure product — you'd be working "
            "directly with the CTO. They're profitable, growing 40% YoY, and planning a Series C "
            "in 12 months.\n\n"
            "Are you open to a conversation? Happy to share the full JD.\n\n"
            "Best,\nSarah"
        ),
        "received_at": datetime.now(timezone.utc) - timedelta(hours=2),
        "thread_id": "thread_001",
    },
    {
        "message_id": "msg_002",
        "sender_name": "Rahul Mehta",
        "sender_email": "rahul@talentbridge.in",
        "subject": "Exciting PM opportunity at a crypto exchange",
        "body": (
            "Hi there,\n\nI wanted to connect with you about a fantastic opportunity at CryptoEdge, "
            "one of India's leading crypto exchanges.\n\n"
            "Role: Product Lead – Trading Platform\n"
            "Compensation: ₹45L–₹60L + tokens\n"
            "Location: Mumbai (5 days in office)\n\n"
            "They're looking for someone to own their spot and derivatives trading product. "
            "The token component could be significant if they do well.\n\n"
            "Let me know if you're interested!\n\nRahul"
        ),
        "received_at": datetime.now(timezone.utc) - timedelta(hours=5),
        "thread_id": "thread_002",
    },
    {
        "message_id": "msg_003",
        "sender_name": "Priya Sharma",
        "sender_email": "priya.sharma@toptal.com",
        "subject": "VP Product - Enterprise SaaS (Remote, ₹1.2Cr - ₹1.5Cr)",
        "body": (
            "Dear candidate,\n\nI'm reaching out on behalf of Orbit Analytics, a B2B SaaS company "
            "building AI-powered analytics for enterprise clients (think Tableau meets GPT-4).\n\n"
            "Role: VP of Product\n"
            "Compensation: ₹1.2Cr – ₹1.5Cr total comp (base + bonus + equity)\n"
            "Location: Fully remote (India-based team, US founders)\n"
            "Stage: Series A ($18M raised), profitable core product\n\n"
            "You'd be the first product hire reporting directly to the CEO. The team is 35 people, "
            "engineering-heavy, with strong product-market fit in the mid-market segment.\n\n"
            "Would you be open to a 30-min exploratory call this week?\n\n"
            "Warm regards,\nPriya"
        ),
        "received_at": datetime.now(timezone.utc) - timedelta(hours=8),
        "thread_id": "thread_003",
    },
]

_marked_read: set[str] = set()
_replies_sent: dict[str, str] = {}


class MockEmailProvider(EmailProvider):
    """Returns hardcoded sample emails. Does not call any external service."""

    async def list_recruiter_emails(self, limit: int = 20) -> list[RawEmail]:
        unread = [e for e in _SAMPLE_EMAILS if e["message_id"] not in _marked_read]
        return [
            RawEmail(
                message_id=e["message_id"],
                sender_name=e["sender_name"],
                sender_email=e["sender_email"],
                subject=e["subject"],
                body=e["body"],
                received_at=e["received_at"],
                thread_id=e.get("thread_id"),
            )
            for e in unread[:limit]
        ]

    async def send_reply(self, message_id: str, body: str) -> bool:
        _replies_sent[message_id] = body
        return True

    async def mark_read(self, message_id: str) -> bool:
        _marked_read.add(message_id)
        return True

    def get_sent_replies(self) -> dict[str, str]:
        """Test helper — returns all replies sent so far."""
        return dict(_replies_sent)
