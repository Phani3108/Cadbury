"""Tests for pipeline runs, search, and chat APIs."""
import pytest


@pytest.mark.asyncio
async def test_pipeline_runs_list_empty(client):
    resp = await client.get("/v1/pipeline-runs")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_pipeline_runs_get_404(client):
    resp = await client.get("/v1/pipeline-runs/nonexistent")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_search_requires_query(client):
    resp = await client.get("/v1/search?q=a")
    assert resp.status_code == 200
    assert resp.json() == []  # too short


@pytest.mark.asyncio
async def test_search_returns_results(client):
    resp = await client.get("/v1/search?q=test+query")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_chat_session_lifecycle(client):
    # Create session
    resp = await client.post("/v1/chat/sessions?delegate_id=recruiter")
    assert resp.status_code == 200
    session = resp.json()
    assert session["delegate_id"] == "recruiter"
    session_id = session["id"]

    # List sessions
    resp = await client.get("/v1/chat/sessions?delegate_id=recruiter")
    assert resp.status_code == 200
    sessions = resp.json()
    assert len(sessions) >= 1

    # Send message
    resp = await client.post(
        f"/v1/chat/sessions/{session_id}/messages",
        json={"content": "Hello!"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["user_message"]["role"] == "user"
    assert data["assistant_message"]["role"] == "assistant"

    # List messages
    resp = await client.get(f"/v1/chat/sessions/{session_id}/messages")
    assert resp.status_code == 200
    msgs = resp.json()
    assert len(msgs) == 2
