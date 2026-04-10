"""
Finance Delegate Pipeline — track spending, detect subscriptions, alert anomalies.

Pipeline: Discover → Track → Alert → Recommend → Act
"""
from __future__ import annotations

import logging
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Optional

from memory.graph import (
    save_transaction,
    list_transactions,
    save_subscription,
    list_subscriptions,
    save_event,
    save_approval,
    log_decision,
)
from memory.models import (
    Transaction,
    Subscription,
    DelegateEvent,
    EventType,
    ApprovalItem,
    DecisionLog,
    TransactionCategory,
)
from runtime.event_bus import publish_event

logger = logging.getLogger(__name__)

DELEGATE_ID = "finance"

# Category detection keywords
CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "subscription": ["netflix", "spotify", "hulu", "disney", "adobe", "github", "aws", "azure",
                      "dropbox", "icloud", "google one", "youtube premium", "openai", "chatgpt"],
    "food": ["uber eats", "doordash", "grubhub", "starbucks", "mcdonald", "restaurant", "cafe"],
    "transport": ["uber", "lyft", "gas", "shell", "chevron", "parking", "transit"],
    "entertainment": ["steam", "playstation", "xbox", "twitch", "cinema", "theater"],
    "utilities": ["electric", "water", "internet", "comcast", "verizon", "at&t", "tmobile"],
    "healthcare": ["pharmacy", "cvs", "walgreens", "doctor", "dental", "hospital", "insurance"],
}


@dataclass
class FinanceContext:
    transactions_ingested: list[Transaction] = field(default_factory=list)
    recurring_detected: list[Subscription] = field(default_factory=list)
    alerts: list[dict] = field(default_factory=list)
    recommendations: list[dict] = field(default_factory=list)
    events_emitted: list[DelegateEvent] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))


def _auto_categorize(merchant: str) -> TransactionCategory:
    """Deterministic category detection from merchant name."""
    merchant_lower = merchant.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw in merchant_lower:
                return TransactionCategory(category)
    return TransactionCategory.OTHER


def _detect_recurring(transactions: list[Transaction]) -> list[dict]:
    """Find recurring charges by merchant + similar amounts."""
    by_merchant: dict[str, list[Transaction]] = defaultdict(list)
    for tx in transactions:
        by_merchant[tx.merchant.lower().strip()].append(tx)

    recurring = []
    for merchant, txs in by_merchant.items():
        if len(txs) < 2:
            continue
        # Sort by date
        txs.sort(key=lambda t: t.date)
        # Check if amounts are similar (within 10%)
        amounts = [t.amount for t in txs]
        avg_amount = sum(amounts) / len(amounts)
        if all(abs(a - avg_amount) / max(avg_amount, 0.01) < 0.1 for a in amounts):
            # Check regularity of intervals
            intervals = []
            for i in range(1, len(txs)):
                delta = (txs[i].date - txs[i - 1].date).days
                intervals.append(delta)
            if intervals:
                avg_interval = sum(intervals) / len(intervals)
                if 25 <= avg_interval <= 35:
                    recurring.append({"merchant": txs[0].merchant, "amount": avg_amount,
                                      "period_days": 30, "count": len(txs), "last": txs[-1]})
                elif 6 <= avg_interval <= 8:
                    recurring.append({"merchant": txs[0].merchant, "amount": avg_amount,
                                      "period_days": 7, "count": len(txs), "last": txs[-1]})
                elif 355 <= avg_interval <= 375:
                    recurring.append({"merchant": txs[0].merchant, "amount": avg_amount,
                                      "period_days": 365, "count": len(txs), "last": txs[-1]})
    return recurring


class FinancePipeline:
    def __init__(self, graph=None, event_bus=None, llm_enabled: bool = False):
        self.graph = graph
        self.event_bus = event_bus
        self.llm_enabled = llm_enabled

    async def run(self, new_transactions: list[Transaction] | None = None) -> FinanceContext:
        ctx = FinanceContext()
        try:
            await self._stage_1_discover(ctx, new_transactions or [])
            await self._stage_2_track(ctx)
            await self._stage_3_alert(ctx)
            await self._stage_4_recommend(ctx)
            await self._stage_5_act(ctx)
        except Exception as exc:
            ctx.errors.append(f"Pipeline error: {exc}")
            logger.exception("Finance pipeline error")
        return ctx

    async def _stage_1_discover(self, ctx: FinanceContext, new_txs: list[Transaction]) -> None:
        """Ingest and auto-categorize new transactions."""
        for tx in new_txs:
            if tx.category == TransactionCategory.OTHER:
                tx.category = _auto_categorize(tx.merchant)
            await save_transaction(tx)
            ctx.transactions_ingested.append(tx)

            event = DelegateEvent(
                delegate_id=DELEGATE_ID,
                event_type=EventType.TRANSACTION_INGESTED,
                trace_id=ctx.trace_id,
                summary=f"${tx.amount:.2f} at {tx.merchant} ({tx.category})",
                payload={"transaction_id": tx.transaction_id, "amount": tx.amount,
                         "merchant": tx.merchant, "category": tx.category},
            )
            await save_event(event)
            await publish_event(event)
            ctx.events_emitted.append(event)

    async def _stage_2_track(self, ctx: FinanceContext) -> None:
        """Detect recurring charges from full transaction history."""
        all_txs = await list_transactions(limit=500)
        existing_subs = await list_subscriptions()
        existing_merchants = {s.merchant.lower() for s in existing_subs}

        recurring = _detect_recurring(all_txs)
        for rec in recurring:
            if rec["merchant"].lower() in existing_merchants:
                continue
            sub = Subscription(
                merchant=rec["merchant"],
                amount=rec["amount"],
                period_days=rec["period_days"],
                last_charged=rec["last"].date,
                next_charge=rec["last"].date + timedelta(days=rec["period_days"]),
                status="active",
            )
            await save_subscription(sub)
            ctx.recurring_detected.append(sub)

            event = DelegateEvent(
                delegate_id=DELEGATE_ID,
                event_type=EventType.RECURRING_DETECTED,
                trace_id=ctx.trace_id,
                summary=f"Recurring: ${sub.amount:.2f}/{sub.period_days}d at {sub.merchant}",
                payload={"subscription_id": sub.subscription_id, "merchant": sub.merchant,
                         "amount": sub.amount, "period_days": sub.period_days},
            )
            await save_event(event)
            await publish_event(event)
            ctx.events_emitted.append(event)

    async def _stage_3_alert(self, ctx: FinanceContext) -> None:
        """Flag unusual charges and spending spikes."""
        all_txs = await list_transactions(limit=200)
        if not all_txs:
            return

        # Calculate spending averages
        amounts = [tx.amount for tx in all_txs]
        avg_amount = sum(amounts) / len(amounts) if amounts else 0
        max_normal = avg_amount * 3  # 3x average = alert

        for tx in ctx.transactions_ingested:
            if tx.amount > max_normal and max_normal > 0:
                alert = {
                    "type": "spending_spike",
                    "message": f"Unusual charge: ${tx.amount:.2f} at {tx.merchant} (avg: ${avg_amount:.2f})",
                    "transaction_id": tx.transaction_id,
                    "severity": "high" if tx.amount > avg_amount * 5 else "medium",
                }
                ctx.alerts.append(alert)
                event = DelegateEvent(
                    delegate_id=DELEGATE_ID,
                    event_type=EventType.SPENDING_ALERT,
                    trace_id=ctx.trace_id,
                    summary=alert["message"],
                    payload=alert,
                )
                await save_event(event)
                await publish_event(event)
                ctx.events_emitted.append(event)

    async def _stage_4_recommend(self, ctx: FinanceContext) -> None:
        """Audit subscriptions — flag potentially unused ones."""
        subs = await list_subscriptions(status="active")
        total_monthly = sum(
            s.amount * (30 / s.period_days) for s in subs if s.period_days > 0
        )

        if total_monthly > 100:
            ctx.recommendations.append({
                "type": "subscription_audit",
                "message": f"Active subscriptions total ~${total_monthly:.0f}/month across {len(subs)} services",
                "action": "Review and cancel unused subscriptions",
            })

        # Flag subscriptions that haven't been used (no related transactions in 60+ days)
        all_txs = await list_transactions(limit=500)
        now = datetime.now(timezone.utc)
        for sub in subs:
            if sub.last_charged and (now - sub.last_charged).days > 60:
                sub.usage_rating = "unused"
                await save_subscription(sub)
                ctx.recommendations.append({
                    "type": "unused_subscription",
                    "message": f"{sub.merchant}: ${sub.amount:.2f} — no charges in 60+ days",
                    "subscription_id": sub.subscription_id,
                })
                event = DelegateEvent(
                    delegate_id=DELEGATE_ID,
                    event_type=EventType.SUBSCRIPTION_FLAGGED,
                    trace_id=ctx.trace_id,
                    summary=f"Possibly unused: {sub.merchant} (${sub.amount:.2f})",
                    payload={"subscription_id": sub.subscription_id, "merchant": sub.merchant},
                )
                await save_event(event)
                await publish_event(event)
                ctx.events_emitted.append(event)

    async def _stage_5_act(self, ctx: FinanceContext) -> None:
        """Create approvals for spending alerts and cancellation recommendations."""
        for alert in ctx.alerts:
            if alert.get("severity") == "high":
                approval = ApprovalItem(
                    delegate_id=DELEGATE_ID,
                    event_id=ctx.events_emitted[-1].event_id if ctx.events_emitted else "",
                    action="review_charge",
                    action_label=f"Review: {alert['message'][:60]}",
                    context_summary=alert["message"],
                    risk_score=0.7,
                    reasoning="Unusual spending detected — review recommended",
                )
                await save_approval(approval)

        for rec in ctx.recommendations:
            if rec["type"] == "unused_subscription":
                approval = ApprovalItem(
                    delegate_id=DELEGATE_ID,
                    event_id=ctx.events_emitted[-1].event_id if ctx.events_emitted else "",
                    action="cancel_subscription",
                    action_label=f"Cancel {rec.get('message', '')[:40]}",
                    context_summary=rec["message"],
                    risk_score=0.5,
                    reasoning="Subscription appears unused — cancellation suggested",
                )
                await save_approval(approval)
