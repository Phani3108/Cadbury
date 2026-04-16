"""Speech-to-text via Groq Whisper (whisper-large-v3).

The Groq SDK is synchronous; we wrap it in `asyncio.to_thread` so it doesn't
block the FastAPI event loop. Empty audio or empty transcripts return one of
three rotating silence responses — taken from Rose's conversational-grace
playbook.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Final

from config.settings import get_settings
from .circuit_breaker import CircuitBreaker

logger = logging.getLogger(__name__)

# Rotated client-side so the user never hears the same "I'm here" twice in a row.
SILENCE_RESPONSES: Final[list[str]] = [
    "I'm here — take your time.",
    "Still listening. Go ahead whenever.",
    "Mm-hm — I'm with you.",
]

_breaker = CircuitBreaker("groq_stt", failure_threshold=5, reset_seconds=60.0)


class STTUnavailableError(Exception):
    """STT cannot be called (missing key or circuit open)."""


async def transcribe(audio_bytes: bytes, filename: str = "audio.webm") -> str:
    """Return the transcript of an audio blob. Returns '' on empty/silent input."""
    settings = get_settings()
    groq_key = getattr(settings, "groq_api_key", "") or ""
    if not groq_key:
        raise STTUnavailableError(
            "GROQ_API_KEY is not set. Set it in Settings → AI Engine to enable voice."
        )

    if not audio_bytes or len(audio_bytes) < 1024:
        # <1KB is almost certainly silence or click-through.
        return ""

    try:
        from groq import Groq  # type: ignore
    except ImportError as e:  # pragma: no cover
        raise STTUnavailableError(f"groq package not installed: {e}") from e

    def _call() -> str:
        client = Groq(api_key=groq_key)
        response = client.audio.transcriptions.create(
            model="whisper-large-v3",
            file=(filename, audio_bytes),
        )
        return (response.text or "").strip()

    async def _await_transcript() -> str:
        return await asyncio.to_thread(_call)

    try:
        return await _breaker.call(_await_transcript())
    except Exception as e:
        logger.warning("STT failure: %s", e)
        raise
