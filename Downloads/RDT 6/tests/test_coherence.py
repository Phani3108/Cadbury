"""
Unit tests for coherence filtering.
"""
import pytest
from digital_twin.utils.coherence import coherence_filter
from ingest.types import Chunk

def test_coherence_filter_basic():
    """Test basic coherence filtering."""
    chunks = [
        Chunk(chunk_id="1", doc_id="doc1", text="Ramki discussed Optum project architecture"),
        Chunk(chunk_id="2", doc_id="doc1", text="The microservices migration is progressing well"),
        Chunk(chunk_id="3", doc_id="doc1", text="We need to focus on security compliance"),
        Chunk(chunk_id="4", doc_id="doc2", text="The weather is nice today"),  # Off-topic
        Chunk(chunk_id="5", doc_id="doc2", text="I like pizza"),  # Off-topic
    ]

    query = "What did Ramki say about Optum?"
    result = coherence_filter(chunks, query)
    
    assert len(result) >= 1
    assert len(result) <= len(chunks)
    
    # Should prioritize Optum-related chunks
    optum_chunks = [c for c in result if "Optum" in c.text]
    assert len(optum_chunks) > 0

def test_coherence_filter_small_input():
    """Test coherence filter with small input."""
    chunks = [
        Chunk(chunk_id="1", doc_id="doc1", text="Ramki discussed Optum project"),
        Chunk(chunk_id="2", doc_id="doc1", text="The architecture looks good"),
    ]

    result = coherence_filter(chunks, "test query")
    assert len(result) == len(chunks)  # Should return all for small input

def test_coherence_filter_empty():
    """Test coherence filter with empty input."""
    result = coherence_filter([], "test query")
    assert result == []

def test_coherence_filter_no_query():
    """Test coherence filter without query."""
    chunks = [
        Chunk(chunk_id="1", doc_id="doc1", text="Ramki discussed Optum project"),
        Chunk(chunk_id="2", doc_id="doc1", text="The architecture looks good"),
    ]

    result = coherence_filter(chunks, "")
    assert len(result) >= 1 