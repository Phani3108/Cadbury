"""
Multi-level semantic search system for the Digital Twin.
"""

import time
from typing import List, Dict, Any, Optional, Tuple
from sentence_transformers import SentenceTransformer
import numpy as np
from .utils.logger import get_logger, log_search_performance, LoggerMixin
from .utils.config import get_settings


class SemanticSearch(LoggerMixin):
    """
    Multi-level semantic search system with different search strategies.
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.logger = get_logger("semantic_search")
        
        # Initialize sentence transformer model
        self.model = SentenceTransformer(self.settings.semantic_search_model)
        
        # Search strategies
        self.search_strategies = {
            "basic": self._basic_semantic_search,
            "advanced": self._advanced_semantic_search,
            "enhanced": self._enhanced_semantic_search,
            "adaptive": self._adaptive_semantic_search
        }
    
    def search(
        self, 
        query: str, 
        knowledge_base: List[Dict[str, Any]], 
        strategy: str = "adaptive",
        max_results: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic search using the specified strategy.
        
        Args:
            query: User query
            knowledge_base: List of KB entries
            strategy: Search strategy to use
            max_results: Maximum number of results to return
            
        Returns:
            List of relevant KB entries with scores
        """
        start_time = time.time()
        
        if not knowledge_base:
            self.logger.warning("Empty knowledge base provided")
            return []
        
        # Choose search strategy
        if strategy not in self.search_strategies:
            self.logger.warning(f"Unknown strategy '{strategy}', using adaptive")
            strategy = "adaptive"
        
        # Perform search
        search_func = self.search_strategies[strategy]
        results = search_func(query, knowledge_base, max_results)
        
        # Log performance
        execution_time = time.time() - start_time
        log_search_performance(strategy, len(results), execution_time)
        
        self.logger.info(f"Search completed: {len(results)} results in {execution_time:.2f}s")
        
        return results
    
    def _basic_semantic_search(
        self, 
        query: str, 
        knowledge_base: List[Dict[str, Any]], 
        max_results: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Basic semantic search using cosine similarity.
        
        Args:
            query: User query
            knowledge_base: List of KB entries
            max_results: Maximum number of results
            
        Returns:
            List of relevant entries with scores
        """
        # Encode query
        query_embedding = self.model.encode([query])[0]
        
        # Encode all KB entries
        kb_texts = [entry.get('content', '') for entry in knowledge_base]
        kb_embeddings = self.model.encode(kb_texts)
        
        # Calculate similarities
        similarities = []
        for i, kb_embedding in enumerate(kb_embeddings):
            similarity = np.dot(query_embedding, kb_embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(kb_embedding)
            )
            similarities.append((similarity, i))
        
        # Sort by similarity
        similarities.sort(reverse=True)
        
        # Filter by threshold and get results
        max_results = max_results or self.settings.max_search_results
        results = []
        
        for similarity, idx in similarities:
            if similarity >= self.settings.similarity_threshold:
                entry = knowledge_base[idx].copy()
                entry['similarity_score'] = float(similarity)
                entry['search_strategy'] = 'basic'
                results.append(entry)
                
                if len(results) >= max_results:
                    break
        
        return results
    
    def _advanced_semantic_search(
        self, 
        query: str, 
        knowledge_base: List[Dict[str, Any]], 
        max_results: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Advanced semantic search with query expansion and filtering.
        
        Args:
            query: User query
            knowledge_base: List of KB entries
            max_results: Maximum number of results
            
        Returns:
            List of relevant entries with scores
        """
        # Expand query with related terms
        expanded_query = self._expand_query(query)
        
        # Perform basic search with expanded query
        basic_results = self._basic_semantic_search(expanded_query, knowledge_base, max_results)
        
        # Apply additional filtering based on metadata
        filtered_results = self._apply_metadata_filtering(basic_results, query)
        
        # Re-rank based on content relevance
        reranked_results = self._rerank_by_content_relevance(filtered_results, query)
        
        return reranked_results
    
    def _enhanced_semantic_search(
        self, 
        query: str, 
        knowledge_base: List[Dict[str, Any]], 
        max_results: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Enhanced semantic search with multi-query approach.
        
        Args:
            query: User query
            knowledge_base: List of KB entries
            max_results: Maximum number of results
            
        Returns:
            List of relevant entries with scores
        """
        # Generate multiple query variations
        query_variations = self._generate_query_variations(query)
        
        # Search with each variation
        all_results = []
        for variation in query_variations:
            results = self._basic_semantic_search(variation, knowledge_base, max_results)
            all_results.extend(results)
        
        # Merge and deduplicate results
        merged_results = self._merge_search_results(all_results)
        
        # Apply topic-based clustering
        clustered_results = self._apply_topic_clustering(merged_results)
        
        return clustered_results[:max_results or self.settings.max_search_results]
    
    def _adaptive_semantic_search(
        self, 
        query: str, 
        knowledge_base: List[Dict[str, Any]], 
        max_results: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Adaptive semantic search that chooses the best strategy based on query type.
        
        Args:
            query: User query
            knowledge_base: List of KB entries
            max_results: Maximum number of results
            
        Returns:
            List of relevant entries with scores
        """
        # Analyze query type
        query_type = self._analyze_query_type(query)
        
        # Choose strategy based on query type
        if query_type == "specific_person":
            strategy = "enhanced"
        elif query_type == "action_items":
            strategy = "advanced"
        elif query_type == "meeting_scheduling":
            strategy = "basic"
        else:
            strategy = "enhanced"
        
        self.logger.info(f"Adaptive search: query type '{query_type}' -> strategy '{strategy}'")
        
        # Perform search with chosen strategy
        search_func = self.search_strategies[strategy]
        results = search_func(query, knowledge_base, max_results)
        
        # Add query type information
        for result in results:
            result['query_type'] = query_type
            result['search_strategy'] = f"adaptive_{strategy}"
        
        return results
    
    def _expand_query(self, query: str) -> str:
        """Expand query with related terms."""
        # Simple query expansion based on common patterns
        expansions = {
            "ramki": ["ramki", "cto", "chief technology officer"],
            "meeting": ["meeting", "call", "discussion", "conversation"],
            "action": ["action", "task", "todo", "item"],
            "technical": ["technical", "technology", "architecture", "system"],
            "budget": ["budget", "cost", "financial", "money"],
            "team": ["team", "people", "staff", "members"]
        }
        
        expanded_terms = []
        query_lower = query.lower()
        
        for term, related_terms in expansions.items():
            if term in query_lower:
                expanded_terms.extend(related_terms)
        
        if expanded_terms:
            return f"{query} {' '.join(expanded_terms)}"
        
        return query
    
    def _apply_metadata_filtering(self, results: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """Apply metadata-based filtering to search results."""
        filtered_results = []
        
        for result in results:
            # Check if result has relevant metadata
            metadata = result.get('metadata', {})
            
            # Filter based on speaker if query mentions specific person
            if 'ramki' in query.lower():
                speaker = metadata.get('speaker', '').lower()
                if 'ramki' in speaker or 'cto' in speaker:
                    result['metadata_score'] = 1.0
                else:
                    result['metadata_score'] = 0.5
            else:
                result['metadata_score'] = 1.0
            
            # Adjust similarity score based on metadata
            result['adjusted_score'] = result['similarity_score'] * result['metadata_score']
            filtered_results.append(result)
        
        # Re-sort by adjusted score
        filtered_results.sort(key=lambda x: x['adjusted_score'], reverse=True)
        
        return filtered_results
    
    def _rerank_by_content_relevance(self, results: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """Re-rank results based on content relevance."""
        for result in results:
            content = result.get('content', '').lower()
            query_terms = query.lower().split()
            
            # Calculate term frequency
            term_matches = sum(1 for term in query_terms if term in content)
            relevance_score = term_matches / len(query_terms) if query_terms else 0
            
            # Combine with similarity score
            result['final_score'] = (result['adjusted_score'] + relevance_score) / 2
        
        # Re-sort by final score
        results.sort(key=lambda x: x['final_score'], reverse=True)
        
        return results
    
    def _generate_query_variations(self, query: str) -> List[str]:
        """Generate variations of the query for enhanced search."""
        variations = [query]
        
        # Add variations based on common patterns
        if 'ramki' in query.lower():
            variations.extend([
                query.replace('ramki', 'CTO'),
                query.replace('ramki', 'chief technology officer'),
                query.replace('ramki', 'our CTO')
            ])
        
        if 'meeting' in query.lower():
            variations.extend([
                query.replace('meeting', 'call'),
                query.replace('meeting', 'discussion'),
                query.replace('meeting', 'conversation')
            ])
        
        if 'action' in query.lower():
            variations.extend([
                query.replace('action', 'task'),
                query.replace('action', 'todo'),
                query.replace('action', 'item')
            ])
        
        return list(set(variations))  # Remove duplicates
    
    def _merge_search_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Merge and deduplicate search results."""
        seen_ids = set()
        merged_results = []
        
        for result in results:
            result_id = result.get('id', hash(result.get('content', '')))
            
            if result_id not in seen_ids:
                seen_ids.add(result_id)
                merged_results.append(result)
        
        return merged_results
    
    def _apply_topic_clustering(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply topic-based clustering to results."""
        # Simple clustering based on content similarity
        clusters = []
        processed = set()
        
        for i, result in enumerate(results):
            if i in processed:
                continue
            
            cluster = [result]
            processed.add(i)
            
            # Find similar results
            for j, other_result in enumerate(results[i+1:], i+1):
                if j in processed:
                    continue
                
                # Calculate similarity between results
                similarity = self._calculate_content_similarity(
                    result.get('content', ''),
                    other_result.get('content', '')
                )
                
                if similarity > 0.8:  # High similarity threshold for clustering
                    cluster.append(other_result)
                    processed.add(j)
            
            clusters.append(cluster)
        
        # Return top result from each cluster
        clustered_results = []
        for cluster in clusters:
            if cluster:
                # Take the highest scoring result from each cluster
                best_result = max(cluster, key=lambda x: x.get('final_score', x.get('similarity_score', 0)))
                clustered_results.append(best_result)
        
        return clustered_results
    
    def _calculate_content_similarity(self, content1: str, content2: str) -> float:
        """Calculate similarity between two content pieces."""
        if not content1 or not content2:
            return 0.0
        
        # Simple word overlap similarity
        words1 = set(content1.lower().split())
        words2 = set(content2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def _analyze_query_type(self, query: str) -> str:
        """Analyze query type to determine search strategy."""
        query_lower = query.lower()
        
        # Check for specific patterns
        if any(word in query_lower for word in ['ramki', 'cto', 'chief']):
            return "specific_person"
        elif any(word in query_lower for word in ['action', 'task', 'todo', 'item']):
            return "action_items"
        elif any(word in query_lower for word in ['meeting', 'schedule', 'book', 'call']):
            return "meeting_scheduling"
        elif any(word in query_lower for word in ['technical', 'architecture', 'system', 'code']):
            return "technical"
        elif any(word in query_lower for word in ['insight', 'analysis', 'discussion']):
            return "insights"
        else:
            return "general"
    
    def get_search_statistics(self) -> Dict[str, Any]:
        """Get search performance statistics."""
        return {
            "model": self.settings.semantic_search_model,
            "similarity_threshold": self.settings.similarity_threshold,
            "max_results": self.settings.max_search_results,
            "strategies": list(self.search_strategies.keys())
        } 