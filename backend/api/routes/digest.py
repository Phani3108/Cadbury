"""
Digest API — endpoints for generating and sending activity digest reports.
"""
from __future__ import annotations

import dataclasses
import logging

from fastapi import APIRouter, Query

from skills.notifications.digest_sender import generate_digest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/digest", tags=["digest"])


@router.get("")
async def get_digest(period: str = Query(default="daily", regex="^(daily|weekly)$")):
    """
    Generate a digest report for the given period.

    Args:
        period: Either "daily" (last 24 hours) or "weekly" (last 7 days).

    Returns:
        The digest report as a JSON dict.
    """
    report = await generate_digest(period=period)
    return dataclasses.asdict(report)


@router.post("/send")
async def send_digest(period: str = Query(default="daily", regex="^(daily|weekly)$")):
    """
    Placeholder endpoint for sending a digest report via email.

    Actual email sending will be implemented in a future iteration.

    Args:
        period: Either "daily" or "weekly".

    Returns:
        Status confirmation with the period.
    """
    logger.info("Digest send requested for period=%s (placeholder)", period)
    return {"status": "sent", "period": period}
