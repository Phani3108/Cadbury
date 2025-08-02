"""
Coherence filtering utilities for Digital Twin.
"""
from typing import List
from sentence_transformers import SentenceTransformer
import numpy as np
from ingest.types import Chunk

# Load model once
_model = None

def _get_model():
    """Get or load the sentence transformer model."""
    global _model
    if _model is None:
        _model = SentenceTransformer('all-MiniLM-L6-v2')
    return _model

def coherence_filter(chunks: List[Chunk], query: str = "", threshold: float = 0.4) -> List[Chunk]:
    """
    Filter chunks based on semantic coherence with query.
    
    Args:
        chunks: List of chunks to filter
        query: User query for context
        threshold: Similarity threshold (0-1)
        
    Returns:
        Filtered list of chunks
    """
    if not chunks:
        return []
    
    if len(chunks) <= 3:
        return chunks  # Keep all if small set
    
    try:
        model = _get_model()
        
        # Get embeddings for query and chunks
        query_embedding = model.encode([query]) if query else None
        chunk_texts = [chunk.text for chunk in chunks]
        chunk_embeddings = model.encode(chunk_texts)
        
        # Calculate similarities
        similarities = []
        for i, chunk_embedding in enumerate(chunk_embeddings):
            if query_embedding is not None:
                # Compare with query
                similarity = np.dot(chunk_embedding, query_embedding[0]) / (
                    np.linalg.norm(chunk_embedding) * np.linalg.norm(query_embedding[0])
                )
            else:
                # Compare with other chunks (average similarity)
                other_embeddings = [emb for j, emb in enumerate(chunk_embeddings) if j != i]
                if other_embeddings:
                    similarities_with_others = [
                        np.dot(chunk_embedding, other_emb) / (
                            np.linalg.norm(chunk_embedding) * np.linalg.norm(other_emb)
                        )
                        for other_emb in other_embeddings
                    ]
                    similarity = np.mean(similarities_with_others)
                else:
                    similarity = 1.0  # Single chunk is always coherent
            
            similarities.append(similarity)
        
        # Filter chunks above threshold
        filtered_chunks = [
            chunk for chunk, similarity in zip(chunks, similarities)
            if similarity >= threshold
        ]
        
        # Ensure we return at least some chunks
        if not filtered_chunks and chunks:
            # Return top 3 by similarity if all below threshold
            chunk_sim_pairs = list(zip(chunks, similarities))
            chunk_sim_pairs.sort(key=lambda x: x[1], reverse=True)
            filtered_chunks = [chunk for chunk, _ in chunk_sim_pairs[:3]]
        
        return filtered_chunks
        
    except Exception as e:
        print(f"⚠️  Coherence filter failed: {e}, returning original chunks")
        return chunks[:5]  # Fallback to simple limit 