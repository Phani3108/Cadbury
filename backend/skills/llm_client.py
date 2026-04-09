"""Tiered LLM client — cheap model for extraction, heavy model for drafting.

Includes token usage tracking for cost visibility. Every call logs tokens used
and accumulates per-session totals accessible via get_usage_stats().
"""
from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any

from openai import AsyncOpenAI

from config.settings import get_settings

logger = logging.getLogger(__name__)

_client: AsyncOpenAI | None = None


# ─── Usage Tracking ──────────────────────────────────────────────────────────

@dataclass
class _UsageStats:
    """Accumulated LLM usage since process start."""
    total_calls: int = 0
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    total_tokens: int = 0
    calls_by_tier: dict[str, int] = field(default_factory=lambda: {"cheap": 0, "heavy": 0})
    tokens_by_tier: dict[str, int] = field(default_factory=lambda: {"cheap": 0, "heavy": 0})


_usage = _UsageStats()


def get_usage_stats() -> dict:
    """Return current LLM usage statistics."""
    return {
        "total_calls": _usage.total_calls,
        "total_prompt_tokens": _usage.total_prompt_tokens,
        "total_completion_tokens": _usage.total_completion_tokens,
        "total_tokens": _usage.total_tokens,
        "calls_by_tier": dict(_usage.calls_by_tier),
        "tokens_by_tier": dict(_usage.tokens_by_tier),
    }


def _track_usage(response, tier: str) -> None:
    """Record token usage from an API response."""
    usage = getattr(response, "usage", None)
    if usage is None:
        return
    _usage.total_calls += 1
    _usage.total_prompt_tokens += usage.prompt_tokens
    _usage.total_completion_tokens += usage.completion_tokens
    _usage.total_tokens += usage.total_tokens
    _usage.calls_by_tier[tier] = _usage.calls_by_tier.get(tier, 0) + 1
    _usage.tokens_by_tier[tier] = _usage.tokens_by_tier.get(tier, 0) + usage.total_tokens
    logger.info(
        "LLM call [%s]: %d prompt + %d completion = %d tokens",
        tier, usage.prompt_tokens, usage.completion_tokens, usage.total_tokens,
    )


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        settings = get_settings()
        if not settings.openai_api_key:
            raise ValueError(
                "OPENAI_API_KEY is not set. Set it in backend/.env to enable LLM features."
            )
        _client = AsyncOpenAI(api_key=settings.openai_api_key)
    return _client


async def chat(messages: list[dict], tier: str = "cheap") -> str:
    """Send a chat completion request. tier='cheap' or 'heavy'."""
    settings = get_settings()
    model = settings.openai_model_heavy if tier == "heavy" else settings.openai_model_cheap
    client = _get_client()
    response = await client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.2,
    )
    _track_usage(response, tier)
    return response.choices[0].message.content or ""


async def extract_json(system_prompt: str, user_content: str) -> dict[str, Any]:
    """Extract structured JSON from text using tool-calling for reliable parsing."""
    settings = get_settings()
    client = _get_client()
    response = await client.chat.completions.create(
        model=settings.openai_model_cheap,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        tools=[{
            "type": "function",
            "function": {
                "name": "extract_data",
                "description": "Extract structured data from the input",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "result": {
                            "type": "object",
                            "description": "The extracted data as a JSON object",
                        }
                    },
                    "required": ["result"],
                },
            },
        }],
        tool_choice={"type": "function", "function": {"name": "extract_data"}},
        temperature=0.0,
    )
    tool_call = response.choices[0].message.tool_calls[0]
    args = json.loads(tool_call.function.arguments)
    _track_usage(response, "cheap")
    return args.get("result", {})
