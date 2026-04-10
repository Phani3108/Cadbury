"""
Context Compaction — summarize old conversation context to fit within LLM token limits.

When a delegate's conversation history exceeds the token budget, this module:
1. Checkpoints the current state (recoverable)
2. Summarizes older messages into a compact summary
3. Truncates to 80% of the context window
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Model context limits (in tokens, approximate)
MODEL_CONTEXT_LIMITS = {
    "gpt-4o-mini": 128_000,
    "gpt-4o": 128_000,
}

# Target: use 80% of context window, leave 20% for new input
COMPACTION_RATIO = 0.80

# Approximate tokens per character (for estimation)
CHARS_PER_TOKEN = 4


def estimate_tokens(text: str) -> int:
    """Rough token count estimate."""
    return len(text) // CHARS_PER_TOKEN


def should_compact(messages: list[dict], model: str = "gpt-4o-mini") -> bool:
    """Check if message history exceeds compaction threshold."""
    limit = MODEL_CONTEXT_LIMITS.get(model, 128_000)
    threshold = int(limit * COMPACTION_RATIO)
    total = sum(estimate_tokens(m.get("content", "")) for m in messages)
    return total > threshold


def checkpoint_messages(messages: list[dict]) -> dict:
    """Create a checkpoint of the current message state (for recovery)."""
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "message_count": len(messages),
        "messages": messages.copy(),
    }


async def compact_messages(
    messages: list[dict],
    model: str = "gpt-4o-mini",
    delegate_id: str = "",
) -> list[dict]:
    """
    Compact conversation history by summarizing older messages.

    Strategy:
    1. Keep the system prompt (first message) intact
    2. Keep the last N messages intact (recent context)
    3. Summarize everything in between into one summary message

    Returns the compacted message list.
    """
    if len(messages) <= 4:
        return messages  # Nothing to compact

    limit = MODEL_CONTEXT_LIMITS.get(model, 128_000)
    target_tokens = int(limit * COMPACTION_RATIO)

    # Split: system prompt | middle (to summarize) | recent (keep)
    system_msg = messages[0] if messages[0].get("role") == "system" else None
    start_idx = 1 if system_msg else 0

    # Keep the last 3 messages intact
    keep_recent = 3
    if len(messages) - start_idx <= keep_recent:
        return messages

    middle = messages[start_idx:-keep_recent]
    recent = messages[-keep_recent:]

    if not middle:
        return messages

    # Summarize the middle section
    middle_text = "\n".join(
        f"[{m.get('role', 'unknown')}]: {m.get('content', '')[:200]}"
        for m in middle
    )

    try:
        from skills.llm_client import chat
        summary = await chat(
            messages=[
                {"role": "system", "content": "Summarize this conversation history into a concise paragraph. Preserve key decisions, facts, and outcomes. Be brief."},
                {"role": "user", "content": middle_text[:8000]},
            ],
            tier="cheap",
            delegate_id=delegate_id,
        )
    except Exception:
        # Fallback: truncate instead of summarize
        logger.warning("Compaction LLM call failed, using truncation fallback")
        summary = f"[Previous {len(middle)} messages summarized: conversation covered various topics]"

    # Rebuild message list
    compacted = []
    if system_msg:
        compacted.append(system_msg)

    compacted.append({
        "role": "assistant",
        "content": f"[Context summary from {len(middle)} earlier messages]: {summary}",
    })

    compacted.extend(recent)

    logger.info(
        "Compacted %d messages to %d (removed %d, kept %d recent)",
        len(messages), len(compacted), len(middle), keep_recent,
    )

    return compacted
