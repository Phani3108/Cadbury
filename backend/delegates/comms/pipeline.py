"""
Comms Delegate Pipeline — triage messages across all channels.

Pipeline: Ingest → Classify → Prioritize → Route → Draft → Act
"""
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

from memory.graph import save_comms_message, save_event, save_approval, log_decision
from memory.models import (
    CommsMessage,
    DelegateEvent,
    EventType,
    ApprovalItem,
    DecisionLog,
    MessagePriority,
    MessageCategory,
)
from runtime.event_bus import publish_event

logger = logging.getLogger(__name__)

DELEGATE_ID = "comms"


@dataclass
class CommsContext:
    messages_ingested: list[CommsMessage] = field(default_factory=list)
    messages_classified: list[CommsMessage] = field(default_factory=list)
    messages_routed: list[CommsMessage] = field(default_factory=list)
    drafts_created: list[CommsMessage] = field(default_factory=list)
    events_emitted: list[DelegateEvent] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))


# ─── Sender importance scoring ────────────────────────────────────────────────

IMPORTANCE_KEYWORDS = {
    "urgent": 1.0, "asap": 1.0, "emergency": 1.0, "deadline": 0.8,
    "important": 0.7, "action required": 0.8, "follow up": 0.5,
    "fyi": 0.2, "newsletter": 0.1, "unsubscribe": 0.05,
}

SPAM_SIGNALS = [
    "unsubscribe", "click here", "limited time", "act now",
    "congratulations", "you've won", "free gift", "no cost",
]


def _classify_message(msg: CommsMessage) -> CommsMessage:
    """Deterministic classification based on content signals."""
    text = f"{msg.subject} {msg.body}".lower()

    # Spam detection
    spam_hits = sum(1 for s in SPAM_SIGNALS if s in text)
    if spam_hits >= 2:
        msg.category = MessageCategory.SPAM
        msg.priority = MessagePriority.SPAM
        return msg

    # Newsletter detection
    if "unsubscribe" in text and spam_hits < 2:
        msg.category = MessageCategory.NEWSLETTER
        msg.priority = MessagePriority.LOW
        return msg

    # Urgency detection
    urgency_score = 0.0
    for keyword, weight in IMPORTANCE_KEYWORDS.items():
        if keyword in text:
            urgency_score = max(urgency_score, weight)

    if urgency_score >= 0.8:
        msg.priority = MessagePriority.URGENT
        msg.category = MessageCategory.URGENT
    elif urgency_score >= 0.5:
        msg.priority = MessagePriority.HIGH
        msg.category = MessageCategory.WORK
    elif urgency_score >= 0.2:
        msg.priority = MessagePriority.NORMAL
        msg.category = MessageCategory.WORK
    else:
        msg.priority = MessagePriority.NORMAL
        msg.category = MessageCategory.PERSONAL

    return msg


def _route_message(msg: CommsMessage) -> str:
    """Decide routing action based on priority."""
    if msg.priority == MessagePriority.SPAM:
        return "archive"
    if msg.priority == MessagePriority.LOW:
        return "batch_digest"
    if msg.priority in (MessagePriority.URGENT, MessagePriority.HIGH):
        return "surface_and_draft"
    return "surface"


class CommsPipeline:
    def __init__(self, graph=None, event_bus=None, llm_enabled: bool = False):
        self.graph = graph
        self.event_bus = event_bus
        self.llm_enabled = llm_enabled

    async def run(self, incoming_messages: list[CommsMessage]) -> CommsContext:
        ctx = CommsContext()
        try:
            await self._stage_1_ingest(ctx, incoming_messages)
            await self._stage_2_classify(ctx)
            await self._stage_3_prioritize(ctx)
            await self._stage_4_route(ctx)
            await self._stage_5_draft(ctx)
            await self._stage_6_act(ctx)
        except Exception as exc:
            ctx.errors.append(f"Pipeline error: {exc}")
            logger.exception("Comms pipeline error")
        return ctx

    async def _stage_1_ingest(self, ctx: CommsContext, messages: list[CommsMessage]) -> None:
        for msg in messages:
            await save_comms_message(msg)
            event = DelegateEvent(
                delegate_id=DELEGATE_ID,
                event_type=EventType.MESSAGE_RECEIVED,
                trace_id=ctx.trace_id,
                summary=f"Message from {msg.sender_name or msg.sender} via {msg.channel}",
                payload={"message_id": msg.message_id, "channel": msg.channel, "sender": msg.sender},
            )
            await save_event(event)
            await publish_event(event)
            ctx.events_emitted.append(event)
            ctx.messages_ingested.append(msg)

    async def _stage_2_classify(self, ctx: CommsContext) -> None:
        for msg in ctx.messages_ingested:
            msg = _classify_message(msg)
            await save_comms_message(msg)
            event = DelegateEvent(
                delegate_id=DELEGATE_ID,
                event_type=EventType.MESSAGE_CLASSIFIED,
                trace_id=ctx.trace_id,
                summary=f"Classified as {msg.category} / {msg.priority}",
                payload={"message_id": msg.message_id, "category": msg.category, "priority": msg.priority},
            )
            await save_event(event)
            await publish_event(event)
            ctx.events_emitted.append(event)
            ctx.messages_classified.append(msg)

    async def _stage_3_prioritize(self, ctx: CommsContext) -> None:
        # Sort by priority weight
        priority_order = {
            MessagePriority.URGENT: 0,
            MessagePriority.HIGH: 1,
            MessagePriority.NORMAL: 2,
            MessagePriority.LOW: 3,
            MessagePriority.SPAM: 4,
        }
        ctx.messages_classified.sort(key=lambda m: priority_order.get(m.priority, 3))

    async def _stage_4_route(self, ctx: CommsContext) -> None:
        for msg in ctx.messages_classified:
            action = _route_message(msg)
            msg.action_taken = action
            await save_comms_message(msg)
            event = DelegateEvent(
                delegate_id=DELEGATE_ID,
                event_type=EventType.MESSAGE_ROUTED,
                trace_id=ctx.trace_id,
                summary=f"Routed: {action} for {msg.sender_name or msg.sender}",
                payload={"message_id": msg.message_id, "action": action},
            )
            await save_event(event)
            await publish_event(event)
            ctx.events_emitted.append(event)
            ctx.messages_routed.append(msg)

    async def _stage_5_draft(self, ctx: CommsContext) -> None:
        for msg in ctx.messages_routed:
            if msg.action_taken != "surface_and_draft":
                continue

            if self.llm_enabled:
                from skills.llm_client import chat
                draft = await chat(
                    messages=[
                        {"role": "system", "content": "Draft a concise, professional reply to this message. Keep it under 3 sentences."},
                        {"role": "user", "content": f"From: {msg.sender_name}\nSubject: {msg.subject}\n\n{msg.body}"},
                    ],
                    delegate_id=DELEGATE_ID,
                )
                msg.reply_draft = draft
            else:
                msg.reply_draft = f"Thank you for your message regarding '{msg.subject}'. I'll review and get back to you shortly."

            await save_comms_message(msg)
            event = DelegateEvent(
                delegate_id=DELEGATE_ID,
                event_type=EventType.MESSAGE_DRAFTED,
                trace_id=ctx.trace_id,
                summary=f"Draft reply created for {msg.sender_name or msg.sender}",
                payload={"message_id": msg.message_id},
            )
            await save_event(event)
            await publish_event(event)
            ctx.events_emitted.append(event)
            ctx.drafts_created.append(msg)

    async def _stage_6_act(self, ctx: CommsContext) -> None:
        for msg in ctx.messages_routed:
            if msg.action_taken == "archive":
                # Auto-archive spam
                msg.action_taken = "archived"
                await save_comms_message(msg)
                await log_decision(DecisionLog(
                    delegate_id=DELEGATE_ID,
                    event_id=ctx.events_emitted[-1].event_id if ctx.events_emitted else "",
                    action_taken="auto_archived:spam",
                    reasoning=f"Auto-archived spam from {msg.sender}",
                    human_approved=None,
                ))
                event = DelegateEvent(
                    delegate_id=DELEGATE_ID,
                    event_type=EventType.MESSAGE_ARCHIVED,
                    trace_id=ctx.trace_id,
                    summary=f"Auto-archived spam from {msg.sender}",
                    payload={"message_id": msg.message_id},
                )
                await save_event(event)
                await publish_event(event)
                ctx.events_emitted.append(event)

            elif msg.action_taken == "surface_and_draft" and msg.reply_draft:
                # Create approval for drafts
                approval = ApprovalItem(
                    delegate_id=DELEGATE_ID,
                    event_id=ctx.events_emitted[-1].event_id if ctx.events_emitted else "",
                    action="send_reply",
                    action_label=f"Reply to {msg.sender_name or msg.sender}",
                    context_summary=f"{msg.channel}: {msg.subject or msg.body[:80]}",
                    draft_content=msg.reply_draft,
                    risk_score=0.3,
                    reasoning=f"Priority: {msg.priority}, drafted reply for review",
                )
                await save_approval(approval)
                event = DelegateEvent(
                    delegate_id=DELEGATE_ID,
                    event_type=EventType.APPROVAL_REQUESTED,
                    trace_id=ctx.trace_id,
                    requires_approval=True,
                    summary=f"Approval needed: reply to {msg.sender_name or msg.sender}",
                    payload={"approval_id": approval.approval_id, "message_id": msg.message_id},
                )
                await save_event(event)
                await publish_event(event)
                ctx.events_emitted.append(event)
