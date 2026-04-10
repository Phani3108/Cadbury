"""API routes for Comms delegate."""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from memory.graph import list_comms_messages, save_comms_message
from memory.models import CommsMessage, MessageChannel

router = APIRouter(prefix="/v1/comms", tags=["comms"])


class IncomingMessage(BaseModel):
    channel: str = "email"
    sender: str
    sender_name: str = ""
    subject: str = ""
    body: str = ""


@router.get("/messages")
async def get_messages(channel: str | None = None, limit: int = 50):
    return await list_comms_messages(channel=channel, limit=limit)


@router.post("/ingest")
async def ingest_message(msg: IncomingMessage):
    """Manually ingest a message for processing."""
    from delegates.comms.pipeline import CommsPipeline
    from config.settings import settings

    comms_msg = CommsMessage(
        channel=MessageChannel(msg.channel),
        sender=msg.sender,
        sender_name=msg.sender_name,
        subject=msg.subject,
        body=msg.body,
    )
    pipeline = CommsPipeline(llm_enabled=bool(settings.openai_api_key))
    ctx = await pipeline.run([comms_msg])
    return {
        "ingested": len(ctx.messages_ingested),
        "classified": len(ctx.messages_classified),
        "drafts": len(ctx.drafts_created),
        "errors": ctx.errors,
    }
