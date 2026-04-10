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


async def generate_cross_delegate_digest(period: str = "daily") -> DigestReport:
    """
    Generate a unified digest combining ALL active delegates.
    Includes: Recruiter, Calendar, Comms, Finance, Shopping, Learning, Health.
    """
    from memory.graph import (
        list_opportunities, list_approvals, list_events, list_decisions,
        list_comms_messages, list_transactions, list_subscriptions,
        list_watch_items, list_learning_paths, list_health_routines,
        list_health_appointments, list_calendar_events,
    )

    report = DigestReport(period=period)
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=24) if period == "daily" else now - timedelta(days=7)

    try:
        # Recruiter
        opps = await list_opportunities(500)
        period_opps = [o for o in opps if o.created_at >= cutoff]
        scored = [o for o in period_opps if o.match_score > 0]
        highest = max(scored, key=lambda o: o.match_score, default=None)

        # All approvals / decisions
        all_approvals = await list_approvals()
        pending = [a for a in all_approvals if a.status == "pending"]
        all_events = await list_events(limit=500)
        period_events = [e for e in all_events if e.timestamp >= cutoff]
        all_decisions = await list_decisions(limit=500)
        period_decisions = [d for d in all_decisions if d.timestamp >= cutoff]

        # Calendar
        cal_events = await list_calendar_events(limit=50)
        upcoming = [c for c in cal_events if c.status in ("proposed", "confirmed")]

        # Comms
        messages = await list_comms_messages(limit=200)
        period_msgs = [m for m in messages if m.created_at >= cutoff]
        spam_archived = sum(1 for m in period_msgs if m.action_taken == "archived")
        urgent_msgs = sum(1 for m in period_msgs if m.priority == "urgent")

        # Finance
        txs = await list_transactions(limit=200)
        period_txs = [t for t in txs if t.date >= cutoff]
        total_spent = sum(t.amount for t in period_txs if t.amount > 0)
        subs = await list_subscriptions(status="active")

        # Shopping
        watch_items = await list_watch_items(status="watching")

        # Learning
        paths = await list_learning_paths()

        # Health
        routines = await list_health_routines(active_only=True)
        appointments = await list_health_appointments(status="scheduled")
    except Exception as exc:
        logger.error("Cross-delegate digest error: %s", exc)
        report.summary = f"Error generating digest: {exc}"
        return report

    # Build highlights per delegate
    highlights: list[str] = []

    # Recruiter section
    if scored:
        highlights.append(f"📧 Recruiter: {len(scored)} opportunities scored")
        if highest:
            highlights.append(f"   Best match: {highest.company} ({highest.match_score:.0%})")

    # Calendar section
    if upcoming:
        highlights.append(f"📅 Calendar: {len(upcoming)} upcoming events")

    # Comms section
    if period_msgs:
        highlights.append(f"💬 Comms: {len(period_msgs)} messages triaged, {spam_archived} archived, {urgent_msgs} urgent")

    # Finance section
    if period_txs:
        highlights.append(f"💰 Finance: ${total_spent:.2f} spent, {len(subs)} active subscriptions")

    # Shopping
    if watch_items:
        highlights.append(f"🛒 Shopping: {len(watch_items)} items being watched")

    # Learning
    if paths:
        avg_progress = sum(p.progress_pct for p in paths) / len(paths) if paths else 0
        highlights.append(f"📚 Learning: {len(paths)} paths, {avg_progress:.0f}% avg progress")

    # Health
    if routines or appointments:
        highlights.append(f"🏥 Health: {len(routines)} active routines, {len(appointments)} upcoming appointments")

    if not highlights:
        highlights.append("No activity across any delegates")

    report.highlights = highlights

    # Action items (pending approvals across all delegates)
    report.action_items = [
        f"[{a.delegate_id}] {a.action_label}: {a.context_summary}"
        for a in pending[:10]
    ]

    # Stats
    time_saved = len(period_decisions) * 5.0
    report.stats = {
        "total_events": len(period_events),
        "pending_approvals": len(pending),
        "time_saved_minutes": time_saved,
        "opportunities_scored": len(scored),
        "messages_triaged": len(period_msgs),
        "amount_spent": round(total_spent, 2),
        "active_subscriptions": len(subs),
        "active_routines": len(routines),
    }

    period_label = "24 hours" if period == "daily" else "7 days"
    summary_parts = [f"Cross-delegate digest for the last {period_label}:"]
    summary_parts.extend(f"  {h}" for h in highlights)
    if pending:
        summary_parts.append(f"\n  ⚠️ {len(pending)} action(s) need your attention")
    if time_saved > 0:
        summary_parts.append(f"  ⏱️ ~{time_saved:.0f} minutes saved through automation")
    report.summary = "\n".join(summary_parts)

    return report
