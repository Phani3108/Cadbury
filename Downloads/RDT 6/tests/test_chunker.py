import pytest
from ingest.md_chunker import chunk

def test_chunk_basic():
    """Test basic chunking functionality."""
    md_text = """
# Meeting Summary

Ramki: We need to focus on the Optum project.
Abhilash: I agree, the timeline is tight.

## Action Items
- Review the architecture
- Schedule follow-up meeting
"""
    
    chunks = chunk(md_text)
    assert len(chunks) > 0
    
    # Check that we have chunks with proper structure
    for chunk in chunks:
        assert hasattr(chunk, 'chunk_id')
        assert hasattr(chunk, 'doc_id')
        assert hasattr(chunk, 'text')
        assert hasattr(chunk, 'speaker')
        assert hasattr(chunk, 'entities')
        assert hasattr(chunk, 'date')

def test_chunk_speaker_detection():
    """Test speaker detection in chunks."""
    md_text = """
Ramki: The microservices architecture needs review.
Abhilash: I'll prepare the documentation.
Ramki: Good, let's schedule it for next week.
"""
    
    chunks = chunk(md_text)
    
    # Should detect speakers
    speakers = [chunk.speaker for chunk in chunks if chunk.speaker]
    assert 'Ramki' in speakers
    assert 'Abhilash' in speakers

def test_chunk_date_extraction():
    """Test date extraction from file names."""
    # This would be tested with actual file processing
    pass

def test_chunk_token_limits():
    """Test that chunks stay within token limits."""
    md_text = "This is a test document. " * 100  # Create long text
    
    chunks = chunk(md_text)
    
    for chunk in chunks:
        # Check that chunks are reasonable size (not too long)
        assert len(chunk.text.split()) <= 350  # ~300 tokens ±50 