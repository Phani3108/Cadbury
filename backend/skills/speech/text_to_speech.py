"""Text-to-speech via ElevenLabs.

Keeps an in-memory SHA256-keyed cache so repeated synthesis of the same text
(e.g. re-listening to a digest) is free. Graceful fallback: if the API key is
missing or the call fails, `synthesize` returns None and callers fall back to
text-only.
"""
from __future__ import annotations

import asyncio
import hashlib
import logging
import time
from dataclasses import dataclass, field
from typing import Optional

from config.settings import get_settings
from .circuit_breaker import CircuitBreaker

logger = logging.getLogger(__name__)


_breaker = CircuitBreaker("elevenlabs_tts", failure_threshold=5, reset_seconds=60.0)


@dataclass
class _CacheEntry:
    audio: bytes
    stored_at: float = field(default_factory=time.monotonic)


_cache: dict[str, _CacheEntry] = {}
_cache_hits: int = 0
_cache_misses: int = 0


def _cache_key(text: str, voice_id: str) -> str:
    return hashlib.sha256(f"{voice_id}:{text}".encode()).hexdigest()


def cache_stats() -> dict:
    return {
        "size": len(_cache),
        "hits": _cache_hits,
        "misses": _cache_misses,
    }


async def synthesize(text: str) -> Optional[bytes]:
    """Return mp3 bytes for `text`, or None if TTS is unavailable."""
    global _cache_hits, _cache_misses
    text = (text or "").strip()
    if not text:
        return None

    settings = get_settings()
    api_key = getattr(settings, "elevenlabs_api_key", "") or ""
    if not api_key:
        logger.debug("TTS skipped — no ELEVENLABS_API_KEY")
        return None

    voice_id = getattr(settings, "elevenlabs_voice_id", "") or "21m00Tcm4TlvDq8ikWAM"
    ttl = int(getattr(settings, "tts_cache_ttl_seconds", 86_400) or 86_400)

    key = _cache_key(text, voice_id)
    entry = _cache.get(key)
    now = time.monotonic()
    if entry and (now - entry.stored_at) < ttl:
        _cache_hits += 1
        return entry.audio

    _cache_misses += 1

    try:
        from elevenlabs.client import ElevenLabs  # type: ignore
    except ImportError as e:  # pragma: no cover
        logger.warning("elevenlabs package not installed: %s", e)
        return None

    def _call() -> bytes:
        client = ElevenLabs(api_key=api_key)
        stream = client.text_to_speech.convert(
            voice_id=voice_id,
            model_id="eleven_turbo_v2_5",
            text=text,
            output_format="mp3_44100_128",
        )
        return b"".join(chunk for chunk in stream if chunk)

    async def _await_audio() -> bytes:
        return await asyncio.to_thread(_call)

    try:
        audio = await _breaker.call(_await_audio())
    except Exception as e:
        logger.warning("TTS failure: %s", e)
        return None

    _cache[key] = _CacheEntry(audio=audio)
    return audio
