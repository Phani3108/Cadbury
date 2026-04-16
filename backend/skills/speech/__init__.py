"""Speech skills — STT (Groq Whisper) + TTS (ElevenLabs) for voice chat."""

from .speech_to_text import transcribe, SILENCE_RESPONSES
from .text_to_speech import synthesize, cache_stats
from .circuit_breaker import CircuitBreaker, CircuitOpenError

__all__ = [
    "transcribe",
    "synthesize",
    "SILENCE_RESPONSES",
    "cache_stats",
    "CircuitBreaker",
    "CircuitOpenError",
]
