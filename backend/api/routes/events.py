import asyncio
import json
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from memory.graph import list_events
from runtime.event_bus import subscribe

router = APIRouter(prefix="/v1/events", tags=["events"])


@router.get("", response_model=None)
async def get_events(delegate_id: str | None = None, limit: int = 100):
    return await list_events(delegate_id, limit)


@router.get("/stream")
async def stream_events(delegate_id: str | None = None):
    """Server-Sent Events stream of real-time delegate events."""

    queue: asyncio.Queue = asyncio.Queue(maxsize=100)
    token = subscribe(queue)

    async def generator():
        try:
            # Heartbeat + initial connection message
            yield "event: connected\ndata: {}\n\n"
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=30.0)
                    if delegate_id and event.get("delegate_id") != delegate_id:
                        continue
                    event_type = event.get("event_type", "delegate.event")
                    data = json.dumps(event)
                    yield f"event: delegate.event\ndata: {data}\n\n"
                except asyncio.TimeoutError:
                    # Send heartbeat every 30s to keep connection alive
                    yield ": heartbeat\n\n"
        finally:
            from runtime.event_bus import unsubscribe
            unsubscribe(token)

    return StreamingResponse(
        generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
