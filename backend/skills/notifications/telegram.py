"""
Telegram notification skill — sends approval notifications and digest summaries.

Supports:
- New approval notifications (with inline approve/reject buttons concept)
- High-match alerts
- Daily digest summaries
- Custom messages from delegate pipelines
"""
from __future__ import annotations

import logging
from typing import Optional

import httpx

from config.settings import get_settings

logger = logging.getLogger(__name__)


async def send_telegram_message(
    text: str,
    parse_mode: str = "HTML",
    chat_id: Optional[str] = None,
) -> bool:
    """
    Send a message via the Telegram Bot API.

    Returns True if sent successfully, False otherwise.
    """
    settings = get_settings()
    bot_token = settings.telegram_bot_token
    target_chat_id = chat_id or settings.telegram_chat_id

    if not bot_token or not target_chat_id:
        logger.debug("Telegram not configured — skipping notification")
        return False

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": target_chat_id,
        "text": text,
        "parse_mode": parse_mode,
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code == 200:
                logger.info("Telegram notification sent successfully")
                return True
            else:
                logger.warning(
                    "Telegram API returned %d: %s", resp.status_code, resp.text
                )
                return False
    except (httpx.HTTPError, httpx.TimeoutException) as exc:
        logger.warning("Telegram notification failed: %s", exc)
        return False


async def notify_new_approval(
    company: str,
    role: str,
    match_score: float,
    approval_id: str,
) -> bool:
    """Send a notification about a new approval requiring human review."""
    score_pct = int(match_score * 100)
    emoji = "🟢" if score_pct >= 65 else "🟡" if score_pct >= 30 else "🔴"

    text = (
        f"{emoji} <b>New Approval Needed</b>\n\n"
        f"<b>Company:</b> {company}\n"
        f"<b>Role:</b> {role}\n"
        f"<b>Match:</b> {score_pct}%\n\n"
        f"<i>Review in dashboard → /approvals</i>"
    )
    return await send_telegram_message(text)


async def notify_high_match(
    company: str,
    role: str,
    match_score: float,
) -> bool:
    """Alert on a high-match opportunity (score >= engagement threshold)."""
    score_pct = int(match_score * 100)
    text = (
        f"🔥 <b>High Match: {score_pct}%</b>\n\n"
        f"<b>{role}</b> at <b>{company}</b>\n\n"
        f"<i>Draft engagement reply ready for review</i>"
    )
    return await send_telegram_message(text)


async def notify_auto_declined(count: int) -> bool:
    """Notify about auto-declined low-score opportunities."""
    if count == 0:
        return False
    text = f"📋 Auto-declined <b>{count}</b> low-match {'opportunity' if count == 1 else 'opportunities'}"
    return await send_telegram_message(text)


async def send_digest(
    period: str,
    new_count: int,
    pending_approvals: int,
    auto_declined: int,
    avg_score: float,
) -> bool:
    """Send a daily/weekly digest summary."""
    text = (
        f"📊 <b>{period.title()} Digest</b>\n\n"
        f"New opportunities: <b>{new_count}</b>\n"
        f"Pending approvals: <b>{pending_approvals}</b>\n"
        f"Auto-declined: <b>{auto_declined}</b>\n"
        f"Avg match score: <b>{int(avg_score * 100)}%</b>"
    )
    return await send_telegram_message(text)


async def notify_email_sent(
    approval_id: str,
    opportunity_id: str | None,
    provider: str,
) -> bool:
    """Notify that an approved email reply was actually sent."""
    text = (
        f"✅ <b>Email Sent</b>\n\n"
        f"Approved reply dispatched via {provider}.\n"
    )
    return await send_telegram_message(text)
