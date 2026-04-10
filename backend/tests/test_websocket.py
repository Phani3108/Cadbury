"""Tests for WebSocket event streaming."""
import pytest
from httpx import ASGITransport, AsyncClient
from starlette.testclient import TestClient


def test_websocket_connect_and_ping():
    """Synchronous WebSocket test using Starlette TestClient."""
    import os
    os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    from main import app

    client = TestClient(app)
    with client.websocket_connect("/v1/events/ws") as ws:
        # Should receive connected message
        data = ws.receive_json()
        assert data["type"] == "connected"

        # Send ping
        ws.send_text("ping")
        data = ws.receive_json()
        assert data["type"] == "pong"
