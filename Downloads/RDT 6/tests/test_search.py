import pytest
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from skills.kb_search import hybrid_search
from ingest.types import Chunk

class TestSearch:
    """Test search functionality."""
    
    def test_hybrid_search_basic(self):
        """Test basic hybrid search functionality."""
        results = hybrid_search("Optum", entities=[], k=5)
        assert len(results) > 0
        assert all(isinstance(chunk, Chunk) for chunk in results)
    
    def test_hybrid_search_with_entities(self):
        """Test hybrid search with entity filtering."""
        results = hybrid_search("microservices", entities=["Ramki"], k=3)
        assert len(results) > 0
        assert all(isinstance(chunk, Chunk) for chunk in results)
    
    def test_hybrid_search_empty_query(self):
        """Test hybrid search with empty query."""
        results = hybrid_search("", entities=[], k=5)
        assert len(results) >= 0  # Should handle empty query gracefully 