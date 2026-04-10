"""
Digest API — endpoints for generating and sending activity digest reports.
"""
from __future__ import annotations

import dataclasses
import logging

from fastapi import APIRouter, Query

from skills.notifications.digest_sender import generate_digest, generate_cross_delegate_digest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/digest", tags=["digest"])


@router.get("")
async def get_digest(
    period: str = Query(default="daily", regex="^(daily|weekly)$"),
    scope: str = Query(default="all", regex="^(all|recruiter)$"),
):
    """
    Generate a digest report for the given period.
    scope=all returns cross-delegate digest, scope=recruiter returns recruiter-only.
    """
    if scope == "all":
        report = await generate_cross_delegate_digest(period=period)
    else:
        report = await generate_digest(period=period)
    return dataclasses.asdict(report)


@router.post("/send")
async def send_digest(period: str = Query(default="daily", regex="^(daily|weekly)$")):
    """Generate cross-delegate digest and send to all configured channels."""
    report = await generate_cross_delegate_digest(period=period)

    try:
        from skills.channels.providers import send_to_all_configured_channels
        results = await send_to_all_configured_channels(report.summary)
        logger.info("Digest sent to channels: %s", results)
        return {"status": "sent", "period": period, "channels": results}
    except Exception as exc:
        logger.error("Failed to send digest: %s", exc)
        return {"status": "partial", "period": period, "error": str(exc)}
