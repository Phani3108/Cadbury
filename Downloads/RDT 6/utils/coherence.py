# utils/coherence.py
from typing import List
from ingest.types import Chunk

def coherence_filter(chunks: List[Chunk], thresh: float = 0.4) -> List[Chunk]:
    """
    Mock coherence filter for testing.
    In production, this would use sentence transformers for semantic similarity.
    """
    if len(chunks) < 3:
        return chunks
    
    # Simple mock implementation - return first 5 chunks
    return chunks[:5] 