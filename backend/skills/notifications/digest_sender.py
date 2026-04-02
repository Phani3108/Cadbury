"""
Digest Sender — generates and optionally sends daily/weekly activity summaries.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)


@dataclass
class DigestReport:
    period: str                    # "daily" or "weekly"
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    highlights: list[str] = field(default_factory=list)
    action_items: list[str] = field(default_factory=list)
    stats: dict = field(default_factory=dict)
    summary: str = ""


async def generate_digest(
    period: str = "daily",
) -> DigestReport:
    """
    Generate a digest report for the given period.

    Pulls data from the memory graph (opportunities, approvals, events, decisions)
    and produces a summary with highlights, action items, and aggregate stats.

    Args:
        period: Either "daily" (last 24 hours) or "weekly" (last 7 days).

    Returns:
        A DigestReport containing highlights, action items, stats, and summary.
    """
    from memory.graph import list_opportunities, list_approvals, list_events, list_decisions

    report = DigestReport(period=period)

    # Determine date range
    now = datetime.now(timezone.utc)
    if period == "weekly":
        cutoff = now - timedelta(days=7)
    else:
        cutoff = now - timedelta(hours=24)

    # Fetch all data
    try:
        all_opportunities = await list_opportunities(limit=500)
        all_approvals = await list_approvals()
        all_events = await list_events(limit=500)
        all_decisions = await list_decisions(limit=500)
    except Exception as exc:
        logger.error("Failed to fetch data for digest: %s", exc)
        report.summary = f"Error generating {period} digest: {exc}"
        return report

    # Filter to the period
    period_opportunities = [
        opp for opp in all_opportunities if opp.created_at >= cutoff
    ]
    period_approvals = [
        item for item in all_approvals if item.created_at >= cutoff
    ]
    period_events = [
        evt for evt in all_events if evt.timestamp >= cutoff
    ]
    period_decisions = [
        dec for dec in all_decisions if dec.timestamp >= cutoff
    ]

    # Calculate stats
    scored_opportunities = [
        opp for opp in period_opportunities if opp.match_score > 0
    ]
    pending_approvals = [
        item for item in period_approvals if item.status == "pending"
    ]
    auto_declined = [
        dec for dec in period_decisions
        if "rejected" in dec.action_taken.lower() or "declined" in dec.action_taken.lower()
    ]
    scores = [opp.match_score for opp in scored_opportunities]
    avg_score = round(sum(scores) / len(scores) * 100, 1) if scores else 0.0

    # Estimate time saved: ~5 min per auto-processed event
    time_saved = len(period_decisions) * 5.0

    # Highest match
    highest_match = max(scored_opportunities, key=lambda o: o.match_score, default=None)

    # Build highlights
    highlights: list[str] = []
    if scored_opportunities:
        highlights.append(f"{len(scored_opportunities)} new opportunities scored")
    if pending_approvals:
        highlights.append(f"{len(pending_approvals)} approvals pending")
    if auto_declined:
        highlights.append(f"{len(auto_declined)} auto-declined")
    if highest_match:
        score_pct = round(highest_match.match_score * 100, 1)
        highlights.append(f"Highest match: {highest_match.company} at {score_pct}%")
    if not highlights:
        highlights.append(f"No new activity in the last {'24 hours' if period == 'daily' else '7 days'}")

    report.highlights = highlights

    # Build action items from pending approvals
    action_items: list[str] = []
    for item in pending_approvals:
        action_items.append(f"[{item.approval_id[:8]}] {item.action_label}: {item.context_summary}")
    report.action_items = action_items

    # Build stats dict
    report.stats = {
        "new_opportunities": len(period_opportunities),
        "pending_approvals": len(pending_approvals),
        "auto_declined": len(auto_declined),
        "avg_score": avg_score,
        "time_saved_minutes": time_saved,
        "total_events": len(period_events),
        "total_decisions": len(period_decisions),
    }

    # Build summary
    summary_parts = []
    period_label = "24 hours" if period == "daily" else "7 days"
    summary_parts.append(f"{period.capitalize()} digest for the last {period_label}:")
    summary_parts.extend(f"  - {h}" for h in highlights)
    if time_saved > 0:
        summary_parts.append(f"  - Estimated {time_saved:.0f} minutes saved through automation")
    report.summary = "\n".join(summary_parts)

    logger.info(
        "Generated %s digest: %d opportunities, %d pending approvals",
        period, len(period_opportunities), len(pending_approvals),
    )

    return report
