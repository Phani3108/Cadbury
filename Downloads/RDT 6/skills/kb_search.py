from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import os
import numpy as np
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from ingest.kb_loader import load_knowledge_base, get_recent_chunks
from ingest.types import Chunk
from ingest.embed import get_embedding, cosine_similarity
import re

# Global KB chunks
_kb_chunks = None

def _get_azure_search_client():
    """Get Azure Search client for production."""
    try:
        from azure.search.documents import SearchClient
        from azure.core.credentials import AzureKeyCredential
        from digital_twin.utils.config import get_settings
        
        settings = get_settings()
        
        endpoint = settings.AZURE_SEARCH_ENDPOINT
        key = settings.AZURE_SEARCH_KEY
        index_name = os.getenv("AZURE_INDEX", "dt-chunks-v2")  # Use new index
        
        if not all([endpoint, key]):
            print("⚠️  Azure Search not configured, falling back to local search")
            return None
        
        credential = AzureKeyCredential(key)
        return SearchClient(endpoint=endpoint, index_name=index_name, credential=credential)
        
    except ImportError:
        print("⚠️  Azure Search SDK not available, falling back to local search")
        return None

def _load_kb_if_needed():
    """Load knowledge base chunks if not already loaded."""
    global _kb_chunks
    if _kb_chunks is None:
        print("📚 Loading knowledge base...")
        _kb_chunks = load_knowledge_base()
    return _kb_chunks

def hybrid_search(query: str, entities: List[str], k: int = 40, recency_days: int = 270) -> List[Chunk]:
    """
    Two-phase semantic search with vector recall, metadata filtering, and reranking.
    
    Args:
        query: Search query
        entities: List of entity names to filter by
        k: Number of results to return
        recency_days: Maximum age of chunks in days
        
    Returns:
        List of Chunk objects sorted by relevance score
    """
    from digital_twin.utils.config import is_local_search, is_production
    
    # Check for fallback mode
    if os.getenv("FALLBACK_KEYWORD_ONLY", "false").lower() == "true":
        print("⚠️  FALLBACK_KEYWORD_ONLY mode: Using keyword-only search")
        return _keyword_only_search(query, entities, k, recency_days)
    
    # Use local search in development mode
    if is_local_search() or not is_production():
        return _local_search(query, entities, k, recency_days)
    
    # Try Azure Search in production
    search_client = _get_azure_search_client()
    if search_client:
        try:
            return _azure_vector_search(query, entities, k, recency_days, search_client)
        except Exception as e:
            print(f"⚠️  Azure Search failed: {e}, falling back to local search")
    
    # Fallback to local search
    return _local_search(query, entities, k, recency_days)

def _keyword_only_search(query: str, entities: List[str], k: int, recency_days: int) -> List[Chunk]:
    """
    Keyword-only search for fallback mode.
    """
    all_chunks = _load_kb_if_needed()
    
    if not all_chunks:
        print("⚠️  No knowledge base chunks available")
        return []
    
    # Filter to recent chunks
    recent_chunks = get_recent_chunks(recency_days)
    
    if not recent_chunks:
        print(f"⚠️  No recent chunks available (all data >{recency_days} days old)")
        return []
    
    # Simple keyword search
    query_terms = query.lower().split()
    scored_chunks = []
    
    for chunk in recent_chunks:
        score = 0
        chunk_text = chunk.text.lower()
        
        # Term frequency scoring
        for term in query_terms:
            if term in chunk_text:
                score += chunk_text.count(term)
        
        # Entity matching bonus
        if entities:
            for entity in entities:
                if entity.lower() in chunk_text:
                    score += 10
        
        # Recency bonus
        try:
            chunk_date = datetime.strptime(chunk.date, '%Y-%m-%d')
            days_old = (datetime.now() - chunk_date).days
            recency_bonus = max(0, (recency_days - days_old) / recency_days)
            score += recency_bonus * 5
        except:
            pass
        
        if score > 0:
            scored_chunks.append((chunk, score))
    
    # Sort by score and return top k
    scored_chunks.sort(key=lambda x: x[1], reverse=True)
    results = [chunk for chunk, score in scored_chunks[:k]]
    
    print(f"🔍 Keyword-only search found {len(results)} relevant chunks for query: '{query}'")
    return results

def _azure_vector_search(query: str, entities: List[str], k: int, recency_days: int, search_client) -> List[Chunk]:
    """
    Azure Search vector search with metadata filtering and reranking.
    """
    # Phase 1: Vector Recall
    query_embedding = get_embedding(query)
    
    # Vector search with high recall
    vector_results = search_client.search(
        search_text="",  # No text search, only vector
        vector_queries=[{
            "vector": query_embedding,
            "fields": "embedding",
            "k": 100  # High recall
        }],
        top=100,
        include_total_count=True,
        select=["id", "text", "date", "meeting_date", "entities", "speaker", "topic_tags", "source_id", "doc_id"]
    )
    
    candidate_chunks = []
    for result in vector_results:
        chunk = Chunk(
            chunk_id=result["id"],
            doc_id=result.get("doc_id", "unknown"),
            text=result["text"],
            speaker=result.get("speaker"),
            entities=result.get("entities", []),
            date=result.get("date"),
            meeting_date=result.get("meeting_date"),
            topic_tags=result.get("topic_tags", [])
        )
        candidate_chunks.append(chunk)
    
    # Phase 2: Metadata Filter
    cutoff_date = datetime.utcnow() - timedelta(days=recency_days)
    filtered_chunks = []
    
    for chunk in candidate_chunks:
        # Check date filter
        try:
            if chunk.meeting_date:
                chunk_date = datetime.strptime(chunk.meeting_date, '%Y-%m-%d')
                if chunk_date < cutoff_date:
                    continue
            elif chunk.date:
                chunk_date = datetime.strptime(chunk.date, '%Y-%m-%d')
                if chunk_date < cutoff_date:
                    continue
        except:
            continue
        
        # Check entity filter
        if entities:
            chunk_entities = set(chunk.entities or [])
            chunk_topics = set(chunk.topic_tags or [])
            query_entities = set(entities)
            
            # Check if any entity matches
            if not (query_entities & chunk_entities or query_entities & chunk_topics):
                continue
        
        filtered_chunks.append(chunk)
    
    # Phase 3: Keyword/BM25 Boost
    query_terms = query.lower().split()
    scored_chunks = []
    
    for chunk in filtered_chunks:
        score = 0
        chunk_text = chunk.text.lower()
        
        # BM25-style scoring
        for term in query_terms:
            if term in chunk_text:
                score += chunk_text.count(term)
        
        # Entity matching bonus
        if entities:
            for entity in entities:
                if entity.lower() in chunk_text:
                    score += 10
        
        # Recency bonus
        try:
            if chunk.meeting_date:
                chunk_date = datetime.strptime(chunk.meeting_date, '%Y-%m-%d')
            else:
                chunk_date = datetime.strptime(chunk.date, '%Y-%m-%d')
            
            days_old = (datetime.now() - chunk_date).days
            recency_bonus = max(0, (recency_days - days_old) / recency_days)
            score += recency_bonus * 5
        except:
            pass
        
        scored_chunks.append((chunk, score))
    
    # Phase 4: Reciprocal Rank Fusion
    # Sort by vector similarity (from Azure Search ranking)
    vector_ranks = {chunk.chunk_id: i for i, (chunk, _) in enumerate(scored_chunks)}
    
    # Sort by keyword score
    scored_chunks.sort(key=lambda x: x[1], reverse=True)
    keyword_ranks = {chunk.chunk_id: i for i, (chunk, _) in enumerate(scored_chunks)}
    
    # Apply RRF
    rrf_scores = []
    for chunk, keyword_score in scored_chunks:
        vector_rank = vector_ranks.get(chunk.chunk_id, len(scored_chunks))
        keyword_rank = keyword_ranks.get(chunk.chunk_id, len(scored_chunks))
        
        # RRF formula: 1 / (k + rank)
        k = 60  # RRF parameter
        rrf_score = (1 / (k + vector_rank)) + (1 / (k + keyword_rank))
        rrf_scores.append((chunk, rrf_score))
    
    # Sort by RRF score
    rrf_scores.sort(key=lambda x: x[1], reverse=True)
    
    # Phase 5: Optional Reranker
    if os.getenv("RERANKER_ENABLED", "false").lower() == "true":
        top_chunks = [chunk for chunk, _ in rrf_scores[:40]]
        reranked_chunks = _rerank_chunks(query, top_chunks)
        final_chunks = reranked_chunks[:k]
    else:
        final_chunks = [chunk for chunk, _ in rrf_scores[:k]]
    
    print(f"🔍 Azure Search found {len(final_chunks)} relevant chunks for query: '{query}'")
    return final_chunks

def _rerank_chunks(query: str, chunks: List[Chunk]) -> List[Chunk]:
    """
    Rerank chunks using cross-encoder model.
    """
    try:
        from sentence_transformers import CrossEncoder
        model = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
        
        # Prepare pairs for cross-encoder
        pairs = [(query, chunk.text) for chunk in chunks]
        
        # Get scores
        scores = model.predict(pairs)
        
        # Sort by score
        scored_chunks = list(zip(chunks, scores))
        scored_chunks.sort(key=lambda x: x[1], reverse=True)
        
        return [chunk for chunk, _ in scored_chunks]
        
    except Exception as e:
        print(f"⚠️  Reranker failed: {e}, returning original order")
        return chunks

def _local_search(query: str, entities: List[str], k: int, recency_days: int) -> List[Chunk]:
    """Local search using vector similarity and BM25."""
    all_chunks = _load_kb_if_needed()
    
    if not all_chunks:
        print("⚠️  No knowledge base chunks available")
        return []
    
    # Filter to recent chunks
    recent_chunks = get_recent_chunks(recency_days)
    
    if not recent_chunks:
        print(f"⚠️  No recent chunks available (all data >{recency_days} days old)")
        return []
    
    # Phase 1: Vector Search
    query_embedding = get_embedding(query)
    vector_scores = []
    
    for chunk in recent_chunks:
        # Get chunk embedding (if available) or use fallback
        try:
            chunk_embedding = get_embedding(chunk.text)
            similarity = cosine_similarity(query_embedding, chunk_embedding)
            vector_scores.append((chunk, similarity))
        except:
            vector_scores.append((chunk, 0.0))
    
    # Sort by vector similarity
    vector_scores.sort(key=lambda x: x[1], reverse=True)
    top_vector_chunks = [chunk for chunk, _ in vector_scores[:100]]
    
    # Phase 2: Metadata Filter
    cutoff_date = datetime.utcnow() - timedelta(days=recency_days)
    filtered_chunks = []
    
    for chunk in top_vector_chunks:
        try:
            chunk_date = datetime.strptime(chunk.date, '%Y-%m-%d')
            if chunk_date < cutoff_date:
                continue
        except:
            continue
        
        # Entity filter
        if entities:
            chunk_entities = set(chunk.entities or [])
            query_entities = set(entities)
            if not (query_entities & chunk_entities):
                continue
        
        filtered_chunks.append(chunk)
    
    # Phase 3: Keyword/BM25 Boost
    query_terms = query.lower().split()
    scored_chunks = []
    
    for chunk in filtered_chunks:
        score = 0
        chunk_text = chunk.text.lower()
        
        # BM25-style scoring
        for term in query_terms:
            if term in chunk_text:
                score += chunk_text.count(term)
        
        # Entity matching bonus
        if entities:
            for entity in entities:
                if entity.lower() in chunk_text:
                    score += 10
        
        # Recency bonus
        try:
            chunk_date = datetime.strptime(chunk.date, '%Y-%m-%d')
            days_old = (datetime.now() - chunk_date).days
            recency_bonus = max(0, (recency_days - days_old) / recency_days)
            score += recency_bonus * 5
        except:
            pass
        
        scored_chunks.append((chunk, score))
    
    # Phase 4: RRF
    vector_ranks = {chunk.chunk_id: i for i, (chunk, _) in enumerate(vector_scores)}
    scored_chunks.sort(key=lambda x: x[1], reverse=True)
    keyword_ranks = {chunk.chunk_id: i for i, (chunk, _) in enumerate(scored_chunks)}
    
    rrf_scores = []
    for chunk, keyword_score in scored_chunks:
        vector_rank = vector_ranks.get(chunk.chunk_id, len(scored_chunks))
        keyword_rank = keyword_ranks.get(chunk.chunk_id, len(scored_chunks))
        
        k = 60
        rrf_score = (1 / (k + vector_rank)) + (1 / (k + keyword_rank))
        rrf_scores.append((chunk, rrf_score))
    
    rrf_scores.sort(key=lambda x: x[1], reverse=True)
    results = [chunk for chunk, _ in rrf_scores[:k]]
    
    print(f"🔍 Local search found {len(results)} relevant chunks for query: '{query}'")
    return results 