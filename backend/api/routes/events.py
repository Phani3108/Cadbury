import asyncio
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from memory.graph import list_events
from runtime.event_bus import subscribe, add_ws_client, remove_ws_client

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
                    item = await asyncio.wait_for(queue.get(), timeout=30.0)

                    # Typed SSE events (e.g. approval.new, approval.resolved)
                    if "__sse_type__" in item:
                        sse_type = item["__sse_type__"]
                        data = json.dumps(item["__data__"])
                        yield f"event: {sse_type}\ndata: {data}\n\n"
                        continue

                    # Regular DelegateEvent — filter by delegate if requested
                    if delegate_id and item.get("delegate_id") != delegate_id:
                        continue
                    data = json.dumps(item)
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


@router.websocket("/ws")
async def websocket_events(websocket: WebSocket):
    """WebSocket endpoint — real-time delegate events."""
    await websocket.accept()
    token = add_ws_client(websocket)
    try:
        await websocket.send_json({"type": "connected", "data": {}})
        while True:
            # Keep connection alive; client can send pings or commands
            data = await websocket.receive_text()
            # Echo back as acknowledgement
            if data == "ping":
                await websocket.send_json({"type": "pong", "data": {}})
    except WebSocketDisconnect:
        pass
    finally:
        remove_ws_client(token)
