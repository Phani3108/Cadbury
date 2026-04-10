"""Agent chat — per-delegate embedded chat sessions."""

import uuid
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from memory.graph import (
    create_chat_session,
    list_chat_sessions,
    list_chat_messages,
    add_chat_message,
)

router = APIRouter(prefix="/v1/chat", tags=["chat"])


class ChatMessageIn(BaseModel):
    content: str


@router.get("/sessions")
async def get_sessions(delegate_id: str | None = None, limit: int = 50):
    return await list_chat_sessions(delegate_id=delegate_id, limit=limit)


@router.post("/sessions")
async def new_session(delegate_id: str):
    session_id = str(uuid.uuid4())
    return await create_chat_session(session_id, delegate_id)


@router.get("/sessions/{session_id}/messages")
async def get_messages(session_id: str, limit: int = 200):
    return await list_chat_messages(session_id, limit=limit)


@router.post("/sessions/{session_id}/messages")
async def send_message(session_id: str, body: ChatMessageIn):
    """Send a user message and get an assistant response."""
    # Save user message
    user_msg = await add_chat_message(
        msg_id=str(uuid.uuid4()),
        session_id=session_id,
        role="user",
        content=body.content,
    )

    # Generate assistant response  (placeholder — will wire to LLM later)
    assistant_reply = f"I received your message. (Chat LLM integration pending.)"

    assistant_msg = await add_chat_message(
        msg_id=str(uuid.uuid4()),
        session_id=session_id,
        role="assistant",
        content=assistant_reply,
    )

    return {"user_message": user_msg, "assistant_message": assistant_msg}
