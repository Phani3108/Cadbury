import pytest
import asyncio
from llm.verifier import check
from ingest.types import Chunk

class DummyCtx:
    pass

@pytest.mark.asyncio
async def test_verifier_valid_response():
    """Test verifier with valid, grounded response."""
    draft = {
        "summary": "Ramki discussed Optum project architecture",
        "insights": ["Microservices migration is progressing well"],
        "discussion": ["Security compliance needs attention"],
        "actions": [{"text": "Complete API documentation", "owner": "Team", "priority": 1, "due": "2025-01-15"}],
        "ramki_quote": "We need to focus on security compliance",
        "followups": ["What are the next milestones?"],
        "sources": ["Source-1", "Source-2"]
    }
    
    chunks = [
        Chunk(chunk_id="1", doc_id="doc1", text="Ramki discussed Optum project architecture and microservices migration"),
        Chunk(chunk_id="2", doc_id="doc1", text="Security compliance needs attention in the project"),
        Chunk(chunk_id="3", doc_id="doc1", text="We need to focus on security compliance")
    ]
    
    result = await check(draft, chunks)
    assert result["valid"] == True

@pytest.mark.asyncio
async def test_verifier_false_claim():
    """Test verifier rejects ungrounded claims."""
    draft = {
        "summary": "Ramki promised 10X revenue increase",
        "insights": ["Revenue will grow 1000%"],
        "discussion": ["This is a guaranteed outcome"],
        "actions": [],
        "ramki_quote": "I guarantee 10X revenue",
        "followups": [],
        "sources": []
    }
    
    chunks = [
        Chunk(chunk_id="1", doc_id="doc1", text="Ramki discussed project challenges"),
        Chunk(chunk_id="2", doc_id="doc1", text="We need to focus on execution")
    ]
    
    result = await check(draft, chunks)
    assert result["valid"] == False
    assert "missing" in result["reason"].lower() or "invalid" in result["reason"].lower()

@pytest.mark.asyncio
async def test_verifier_old_sources():
    """Test verifier rejects claims from old sources (>270 days)."""
    draft = {
        "summary": "Ramki discussed old topic",
        "insights": ["This is from old discussion"],
        "discussion": ["Old information"],
        "actions": [],
        "ramki_quote": "Old quote",
        "followups": [],
        "sources": ["Source-1"]
    }
    
    chunks = [
        Chunk(chunk_id="1", doc_id="doc1", text="Old discussion content")
    ]
    
    result = await check(draft, chunks)
    assert result["valid"] == False
    assert "old" in result["reason"].lower() or "invalid" in result["reason"].lower() 