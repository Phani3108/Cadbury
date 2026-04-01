"""Tiered LLM client — cheap model for extraction, heavy model for drafting."""
from __future__ import annotations

import json
from typing import Any

from openai import AsyncOpenAI

from config.settings import get_settings

_client: AsyncOpenAI | None = None


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
    model = settings.OPENAI_MODEL_HEAVY if tier == "heavy" else settings.OPENAI_MODEL_CHEAP
    client = _get_client()
    response = await client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.2,
    )
    return response.choices[0].message.content or ""


async def extract_json(system_prompt: str, user_content: str) -> dict[str, Any]:
    """Extract structured JSON from text using tool-calling for reliable parsing."""
    settings = get_settings()
    client = _get_client()
    response = await client.chat.completions.create(
        model=settings.OPENAI_MODEL_CHEAP,
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
    return args.get("result", {})
