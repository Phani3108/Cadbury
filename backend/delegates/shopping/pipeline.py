"""
Shopping Delegate Pipeline — watch prices, detect deals, alert on drops.

Pipeline: Watch → Compare → Alert → Recommend → Act
"""
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

from memory.graph import save_watch_item, list_watch_items, get_watch_item, save_event, save_approval
from memory.models import (
    WatchItem,
    DelegateEvent,
    EventType,
    ApprovalItem,
)
from runtime.event_bus import publish_event
from runtime.tracker import tracked_pipeline

logger = logging.getLogger(__name__)

DELEGATE_ID = "shopping"


@dataclass
class ShoppingContext:
    items_checked: list[WatchItem] = field(default_factory=list)
    price_drops: list[dict] = field(default_factory=list)
    deals: list[dict] = field(default_factory=list)
    events_emitted: list[DelegateEvent] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))


class ShoppingPipeline:
    def __init__(self, graph=None, event_bus=None, llm_enabled: bool = False):
        self.graph = graph
        self.event_bus = event_bus
        self.llm_enabled = llm_enabled

    @tracked_pipeline("shopping")
    async def run(self, price_updates: dict[str, float] | None = None) -> ShoppingContext:
        """
        Run the shopping pipeline.

        Args:
            price_updates: Optional dict of {item_id: new_price} for items being tracked.
        """
        ctx = ShoppingContext()
        try:
            await self._stage_1_watch(ctx, price_updates or {})
            await self._stage_2_compare(ctx)
            await self._stage_3_alert(ctx)
            await self._stage_4_recommend(ctx)
            await self._stage_5_act(ctx)
        except Exception as exc:
            ctx.errors.append(f"Pipeline error: {exc}")
            logger.exception("Shopping pipeline error")
        return ctx

    async def _stage_1_watch(self, ctx: ShoppingContext, price_updates: dict[str, float]) -> None:
        """Update prices for tracked items."""
        items = await list_watch_items(status="watching")
        now = datetime.now(timezone.utc)

        for item in items:
            if item.item_id in price_updates:
                new_price = price_updates[item.item_id]
                old_price = item.current_price

                item.price_history.append({
                    "date": now.isoformat(),
                    "price": new_price,
                })
                item.current_price = new_price
                await save_watch_item(item)

                event = DelegateEvent(
                    delegate_id=DELEGATE_ID,
                    event_type=EventType.PRICE_TRACKED,
                    trace_id=ctx.trace_id,
                    summary=f"Price update: {item.name} — ${new_price:.2f}",
                    payload={"item_id": item.item_id, "name": item.name,
                             "old_price": old_price, "new_price": new_price},
                )
                await save_event(event)
                await publish_event(event)
                ctx.events_emitted.append(event)

            ctx.items_checked.append(item)

    async def _stage_2_compare(self, ctx: ShoppingContext) -> None:
        """Detect price drops by comparing current vs historical prices."""
        for item in ctx.items_checked:
            if not item.price_history or len(item.price_history) < 2:
                continue

            prices = [p["price"] for p in item.price_history]
            max_price = max(prices[:-1])  # Previous max
            current = prices[-1]

            if current < max_price * 0.9:  # 10%+ drop
                drop_pct = round((1 - current / max_price) * 100, 1)
                ctx.price_drops.append({
                    "item_id": item.item_id,
                    "name": item.name,
                    "current": current,
                    "previous_max": max_price,
                    "drop_pct": drop_pct,
                    "url": item.url,
                })

            # Check if target price reached
            if item.target_price and current <= item.target_price:
                ctx.deals.append({
                    "item_id": item.item_id,
                    "name": item.name,
                    "current": current,
                    "target": item.target_price,
                    "url": item.url,
                })

    async def _stage_3_alert(self, ctx: ShoppingContext) -> None:
        """Emit events for price drops and deals."""
        for drop in ctx.price_drops:
            event = DelegateEvent(
                delegate_id=DELEGATE_ID,
                event_type=EventType.PRICE_DROP,
                trace_id=ctx.trace_id,
                summary=f"Price drop: {drop['name']} down {drop['drop_pct']}% to ${drop['current']:.2f}",
                payload=drop,
            )
            await save_event(event)
            await publish_event(event)
            ctx.events_emitted.append(event)

        for deal in ctx.deals:
            event = DelegateEvent(
                delegate_id=DELEGATE_ID,
                event_type=EventType.DEAL_FOUND,
                trace_id=ctx.trace_id,
                summary=f"Target price reached: {deal['name']} at ${deal['current']:.2f} (target: ${deal['target']:.2f})",
                payload=deal,
            )
            await save_event(event)
            await publish_event(event)
            ctx.events_emitted.append(event)

    async def _stage_4_recommend(self, ctx: ShoppingContext) -> None:
        """Generate buy/wait recommendations based on price history."""
        for item in ctx.items_checked:
            if len(item.price_history) < 3:
                continue
            prices = [p["price"] for p in item.price_history[-10:]]
            avg = sum(prices) / len(prices)
            current = prices[-1]
            # If current is below average, it's a good time to buy
            if current < avg * 0.85:
                ctx.deals.append({
                    "item_id": item.item_id,
                    "name": item.name,
                    "current": current,
                    "avg_price": round(avg, 2),
                    "recommendation": "Buy — below 15% of historical average",
                    "url": item.url,
                })

    async def _stage_5_act(self, ctx: ShoppingContext) -> None:
        """Create approvals for purchase recommendations — never auto-buy."""
        for deal in ctx.deals:
            approval = ApprovalItem(
                delegate_id=DELEGATE_ID,
                event_id=ctx.events_emitted[-1].event_id if ctx.events_emitted else "",
                action="purchase_recommendation",
                action_label=f"Buy: {deal['name']} at ${deal['current']:.2f}",
                context_summary=deal.get("recommendation", f"Target price reached for {deal['name']}"),
                draft_content=deal.get("url", ""),
                risk_score=0.4,
                reasoning="Purchase link provided — never auto-purchases without explicit approval",
            )
            await save_approval(approval)
            event = DelegateEvent(
                delegate_id=DELEGATE_ID,
                event_type=EventType.APPROVAL_REQUESTED,
                trace_id=ctx.trace_id,
                requires_approval=True,
                summary=f"Purchase recommendation: {deal['name']}",
                payload={"approval_id": approval.approval_id, "item_id": deal["item_id"]},
            )
            await save_event(event)
            await publish_event(event)
            ctx.events_emitted.append(event)
