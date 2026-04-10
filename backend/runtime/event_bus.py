"""
In-memory pub/sub event bus for SSE + WebSocket streaming.
Subscribers are asyncio Queues; events are dicts (serialized DelegateEvent).
"""

from __future__ import annotations

import asyncio
import json
import uuid
from typing import TYPE_CHECKING

from fastapi import WebSocket

if TYPE_CHECKING:
    from memory.models import DelegateEvent

_subscribers: dict[str, asyncio.Queue] = {}
_ws_clients: dict[str, WebSocket] = {}


def subscribe(queue: asyncio.Queue) -> str:
    token = str(uuid.uuid4())
    _subscribers[token] = queue
    return token


def unsubscribe(token: str) -> None:
    _subscribers.pop(token, None)


def add_ws_client(ws: WebSocket) -> str:
    token = str(uuid.uuid4())
    _ws_clients[token] = ws
    return token


def remove_ws_client(token: str) -> None:
    _ws_clients.pop(token, None)


async def _broadcast_ws(payload: dict) -> None:
    """Send JSON payload to all connected WebSocket clients."""
    dead = []
    for token, ws in _ws_clients.items():
        try:
            await ws.send_json(payload)
        except Exception:
            dead.append(token)
    for token in dead:
        remove_ws_client(token)


async def publish_event(event: "DelegateEvent") -> None:
    """Broadcast event to all SSE + WebSocket subscribers and dispatch cross-delegate actions."""
    payload = event.model_dump(mode="json")

    # SSE subscribers
    dead = []
    for token, queue in _subscribers.items():
        try:
            queue.put_nowait(payload)
        except asyncio.QueueFull:
            dead.append(token)
    for token in dead:
        unsubscribe(token)

    # WebSocket subscribers
    await _broadcast_ws({"type": "delegate.event", "data": payload})

    # Cross-delegate coordination (fire-and-forget)
    try:
        from runtime.coordinator import dispatch_cross_delegate_event
        asyncio.create_task(dispatch_cross_delegate_event(event))
    except Exception:
        pass


async def publish_typed_event(sse_type: str, data: dict) -> None:
    """Broadcast a typed SSE event (e.g. 'approval.new') to all subscribers."""
    # SSE
    envelope = {"__sse_type__": sse_type, "__data__": data}
    dead = []
    for token, queue in _subscribers.items():
        try:
            queue.put_nowait(envelope)
        except asyncio.QueueFull:
            dead.append(token)
    for token in dead:
        unsubscribe(token)

    # WebSocket
    await _broadcast_ws({"type": sse_type, "data": data})


class _EventBusSingleton:
    """Class wrapper so the pipeline can call bus.publish_event(event)."""
    async def publish_event(self, event: "DelegateEvent") -> None:
        await publish_event(event)

    async def publish_typed_event(self, sse_type: str, data: dict) -> None:
        await publish_typed_event(sse_type, data)

    def subscribe(self, queue: asyncio.Queue) -> str:
        return subscribe(queue)

    def unsubscribe(self, token: str) -> None:
        unsubscribe(token)

    def add_ws_client(self, ws: WebSocket) -> str:
        return add_ws_client(ws)

    def remove_ws_client(self, token: str) -> None:
        remove_ws_client(token)


_bus_instance = _EventBusSingleton()


def get_event_bus() -> _EventBusSingleton:
    return _bus_instance
