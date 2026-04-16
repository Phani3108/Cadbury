"""Voice API — transcribe, synthesize, and end-to-end voice chat.

Mirrors Rose's voice endpoint shape: every response carries a per-stage
`PipelineTimings` block so the client can show latency breakdowns. Synthesized
audio is served from an in-process dict and auto-expires after one hour.
"""
from __future__ import annotations

import logging
import random
import time
import uuid
from dataclasses import asdict, dataclass, field
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, Response, UploadFile
from pydantic import BaseModel

from config.settings import get_settings
from memory.graph import (
    add_chat_message,
    list_chat_messages,
    list_chat_sessions,
    list_memories,
    get_career_goals,
)
from skills.llm_client import chat as llm_chat, BudgetExceededError
from skills.speech import (
    SILENCE_RESPONSES,
    CircuitOpenError,
    synthesize,
    transcribe,
)
from api.routes.chat import _system_prompt, MAX_HISTORY_TURNS

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/v1/voice", tags=["voice"])


# ─── In-memory audio store (auto-expiring) ────────────────────────────────────

@dataclass
class _AudioEntry:
    audio: bytes
    content_type: str = "audio/mpeg"
    created_at: float = field(default_factory=time.monotonic)


_AUDIO_TTL_SECONDS = 3600
_audio_store: dict[str, _AudioEntry] = {}


def _put_audio(audio: bytes, content_type: str = "audio/mpeg") -> str:
    audio_id = str(uuid.uuid4())
    _audio_store[audio_id] = _AudioEntry(audio=audio, content_type=content_type)
    _sweep()
    return audio_id


def _sweep() -> None:
    now = time.monotonic()
    stale = [k for k, v in _audio_store.items() if now - v.created_at > _AUDIO_TTL_SECONDS]
    for k in stale:
        _audio_store.pop(k, None)


# ─── Schemas ──────────────────────────────────────────────────────────────────

class TranscribeResponse(BaseModel):
    text: str
    stt_ms: float
    request_id: str


class SynthesizeIn(BaseModel):
    text: str


class SynthesizeResponse(BaseModel):
    audio_url: Optional[str]
    tts_ms: Optional[float]
    cached: bool
    request_id: str


@dataclass
class PipelineTimings:
    stt_ms: Optional[float] = None
    workflow_ms: Optional[float] = None
    tts_ms: Optional[float] = None
    total_ms: Optional[float] = None


class VoiceChatResponse(BaseModel):
    request_id: str
    session_id: str
    transcript: str
    reply: str
    audio_url: Optional[str]
    is_silence: bool
    timings: dict


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _validate_audio(data: bytes) -> None:
    settings = get_settings()
    max_bytes = max(1, settings.stt_max_audio_mb) * 1024 * 1024
    if len(data) == 0:
        raise HTTPException(status_code=400, detail="Empty audio payload")
    if len(data) > max_bytes:
        raise HTTPException(status_code=413, detail=f"Audio exceeds {settings.stt_max_audio_mb}MB limit")


async def _llm_reply(delegate_id: str, session_id: str, user_text: str) -> str:
    # Persist user turn before LLM call so it isn't lost on failure.
    await add_chat_message(
        msg_id=str(uuid.uuid4()),
        session_id=session_id,
        role="user",
        content=user_text,
    )

    try:
        memories = await list_memories()
    except Exception:
        memories = []
    try:
        goals = await get_career_goals()
    except Exception:
        goals = None

    history = await list_chat_messages(session_id, limit=MAX_HISTORY_TURNS * 2)
    messages: list[dict] = [
        {"role": "system", "content": _system_prompt(delegate_id, memories, goals)}
    ]
    for row in history[-MAX_HISTORY_TURNS * 2 :]:
        messages.append({"role": row.get("role", "user"), "content": row.get("content", "")})

    try:
        reply = await llm_chat(messages, tier="cheap", delegate_id=delegate_id)
    except BudgetExceededError as e:
        reply = f"(Delegate budget exceeded — {e}.)"
    except Exception as e:
        logger.exception("LLM call failed during voice chat")
        reply = f"(Assistant unavailable: {type(e).__name__}.)"

    await add_chat_message(
        msg_id=str(uuid.uuid4()),
        session_id=session_id,
        role="assistant",
        content=reply,
    )
    return reply


# ─── Routes ───────────────────────────────────────────────────────────────────

@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe_audio(file: UploadFile = File(...)):
    data = await file.read()
    _validate_audio(data)

    t0 = time.monotonic()
    try:
        text = await transcribe(data, filename=file.filename or "audio.webm")
    except CircuitOpenError:
        raise HTTPException(status_code=503, detail="Speech-to-text temporarily unavailable (circuit open)")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"STT failed: {e}")
    stt_ms = (time.monotonic() - t0) * 1000.0

    return TranscribeResponse(text=text, stt_ms=round(stt_ms, 1), request_id=str(uuid.uuid4()))


@router.post("/synthesize", response_model=SynthesizeResponse)
async def synthesize_text(body: SynthesizeIn):
    t0 = time.monotonic()
    audio = await synthesize(body.text)
    tts_ms = (time.monotonic() - t0) * 1000.0

    if audio is None:
        return SynthesizeResponse(
            audio_url=None,
            tts_ms=None,
            cached=False,
            request_id=str(uuid.uuid4()),
        )

    audio_id = _put_audio(audio)
    return SynthesizeResponse(
        audio_url=f"/v1/voice/audio/{audio_id}",
        tts_ms=round(tts_ms, 1),
        cached=tts_ms < 50,  # heuristic — cache returns near-instant
        request_id=str(uuid.uuid4()),
    )


@router.get("/audio/{audio_id}")
async def get_audio(audio_id: str):
    _sweep()
    entry = _audio_store.get(audio_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="Audio expired or not found")
    return Response(content=entry.audio, media_type=entry.content_type)


@router.post("/chat", response_model=VoiceChatResponse)
async def voice_chat(
    session_id: str = Form(...),
    file: UploadFile = File(...),
):
    """End-to-end voice turn: audio → STT → LLM → TTS."""
    sessions = await list_chat_sessions(limit=500)
    session = next((s for s in sessions if s["id"] == session_id), None)
    if session is None:
        raise HTTPException(status_code=404, detail="Chat session not found")
    delegate_id = session["delegate_id"]

    request_id = str(uuid.uuid4())
    data = await file.read()
    _validate_audio(data)

    timings = PipelineTimings()
    pipeline_t0 = time.monotonic()

    # ── STT ──
    t0 = time.monotonic()
    try:
        transcript = await transcribe(data, filename=file.filename or "audio.webm")
    except CircuitOpenError:
        raise HTTPException(status_code=503, detail="Speech-to-text temporarily unavailable")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"STT failed: {e}")
    timings.stt_ms = round((time.monotonic() - t0) * 1000.0, 1)

    # Silence handling — rotating response, skip LLM
    is_silence = not transcript
    if is_silence:
        reply = random.choice(SILENCE_RESPONSES)
    else:
        t0 = time.monotonic()
        reply = await _llm_reply(delegate_id, session_id, transcript)
        timings.workflow_ms = round((time.monotonic() - t0) * 1000.0, 1)

    # ── TTS ──
    t0 = time.monotonic()
    audio = await synthesize(reply)
    timings.tts_ms = round((time.monotonic() - t0) * 1000.0, 1) if audio else None

    audio_url = None
    if audio is not None:
        audio_url = f"/v1/voice/audio/{_put_audio(audio)}"

    timings.total_ms = round((time.monotonic() - pipeline_t0) * 1000.0, 1)

    return VoiceChatResponse(
        request_id=request_id,
        session_id=session_id,
        transcript=transcript,
        reply=reply,
        audio_url=audio_url,
        is_silence=is_silence,
        timings=asdict(timings),
    )
