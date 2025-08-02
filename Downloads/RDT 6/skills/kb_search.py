from typing import List
from datetime import datetime
import os
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from ingest.kb_loader import load_knowledge_base, get_recent_chunks
from ingest.types import Chunk
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
        index_name = os.getenv("AZURE_INDEX", "digital-twin-index")
        
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

def hybrid_search(query: str, entities: List[str], k: int = 40) -> List[Chunk]:
    """
    Hybrid search combining BM25 and vector search with RRF.
    Truth Policy compliant - only returns recent chunks (≤270 days).
    
    Args:
        query: Search query
        entities: List of entity names to filter by
        k: Number of results to return
        
    Returns:
        List of Chunk objects sorted by relevance score
    """
    from digital_twin.utils.config import is_local_search, is_production
    
    # Use local search in development mode
    if is_local_search() or not is_production():
        return _local_search(query, entities, k)
    
    # Try Azure Search in production
    search_client = _get_azure_search_client()
    if search_client:
        try:
            # Build search query with filters
            search_filter = "date ge 2024-01-01"  # Truth Policy: 270-day limit
            if entities:
                entity_filter = " or ".join([f"entities/any(e: e eq '{entity}')" for entity in entities])
                search_filter += f" and ({entity_filter})"
            
            # Perform hybrid search
            results = search_client.search(
                search_text=query,
                filter=search_filter,
                top=k,
                include_total_count=True,
                select=["id", "text", "date", "entities", "speaker", "source_id"]
            )
            
            # Convert to Chunk objects
            chunks = []
            for result in results:
                chunk = Chunk(
                    chunk_id=result["id"],
                    doc_id=result.get("doc_id", "unknown"),
                    text=result["text"],
                    speaker=result.get("speaker"),
                    entities=result.get("entities", []),
                    date=result.get("date")
                )
                chunks.append(chunk)
            
            print(f"🔍 Azure Search found {len(chunks)} relevant chunks for query: '{query}'")
            return chunks
            
        except Exception as e:
            print(f"⚠️  Azure Search failed: {e}, falling back to local search")
    
    # Fallback to local search
    return _local_search(query, entities, k)

def _local_search(query: str, entities: List[str], k: int) -> List[Chunk]:
    """Local search using ChromaDB and BM25."""
    all_chunks = _load_kb_if_needed()
    
    if not all_chunks:
        print("⚠️  No knowledge base chunks available")
        return []
    
    # Filter to recent chunks (Truth Policy: 270-day limit)
    recent_chunks = get_recent_chunks(270)
    
    if not recent_chunks:
        print("⚠️  No recent chunks available (all data >270 days old)")
        return []
    
    # Simple BM25-style text search with QDF
    query_terms = query.lower().split()
    scored_chunks = []
    
    for chunk in recent_chunks:
        score = 0
        chunk_text = chunk.text.lower()
        
        # Basic term frequency scoring
        for term in query_terms:
            if term in chunk_text:
                score += chunk_text.count(term)
        
        # Entity matching bonus
        if entities:
            for entity in entities:
                if entity.lower() in chunk_text:
                    score += 10  # Bonus for entity match
        
        # Date recency bonus (newer = higher score)
        try:
            chunk_date = datetime.strptime(chunk.date, '%Y-%m-%d')
            days_old = (datetime.now() - chunk_date).days
            recency_bonus = max(0, (270 - days_old) / 270)  # Newer = higher bonus
            score += recency_bonus * 5
            
            # Query Deserved Freshness (QDF) bonus
            from digital_twin.utils.config import get_settings
            settings = get_settings()
            if settings.QDF_ENABLED:
                qdf_score = 0.3 * (2.71828 ** (-0.1 * days_old))  # Exponential decay
                score += qdf_score
        except:
            pass
        
        if score > 0:
            scored_chunks.append((chunk, score))
    
    # Sort by score and return top k
    scored_chunks.sort(key=lambda x: x[1], reverse=True)
    results = [chunk for chunk, score in scored_chunks[:k]]
    
    print(f"🔍 Local search found {len(results)} relevant chunks for query: '{query}'")
    return results 