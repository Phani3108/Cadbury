"""
Unit tests for compression utilities.
"""
import pytest
from digital_twin.utils.compress import compress, estimate_tokens
from ingest.types import Chunk

def test_compress_basic():
    """Test basic compression."""
    chunks = [
        Chunk(chunk_id="1", doc_id="doc1", text="Ramki discussed Optum project architecture"),
        Chunk(chunk_id="2", doc_id="doc1", text="The microservices migration is progressing well"),
        Chunk(chunk_id="3", doc_id="doc1", text="We need to focus on security compliance"),
    ]

    result = compress(chunks, "What did Ramki say about Optum?")
    assert isinstance(result, str)
    assert len(result) > 0

def test_compress_empty():
    """Test compression with empty input."""
    result = compress([], "test query")
    assert result == ""

def test_compress_short_text():
    """Test compression with already short text."""
    chunks = [
        Chunk(chunk_id="1", doc_id="doc1", text="Short text"),
    ]

    result = compress(chunks, "test query", limit_tokens=100)
    assert "Short text" in result

def test_estimate_tokens():
    """Test token estimation."""
    text = "This is a test sentence with multiple words."
    tokens = estimate_tokens(text)
    assert isinstance(tokens, int)
    assert tokens > 0

def test_compress_with_speakers():
    """Test compression with speaker information."""
    chunks = [
        Chunk(chunk_id="1", doc_id="doc1", text="The project is going well", speaker="Ramki"),
        Chunk(chunk_id="2", doc_id="doc1", text="We need to focus on security", speaker="Abhilash"),
    ]

    result = compress(chunks, "What was discussed?")
    assert "Ramki:" in result or "Abhilash:" in result 