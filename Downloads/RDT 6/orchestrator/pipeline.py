"""
Async pipeline orchestrator for the Digital Twin system.
"""

import asyncio
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import logging
import time
from functools import wraps

def get_logger(name):
    return logging.getLogger(name)

def log_execution_time(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        result = await func(*args, **kwargs)
        end_time = time.time()
        logging.getLogger("pipeline").info(f"{func.__name__} took {end_time - start_time:.2f}s")
        return result
    return wrapper
# Import proper utilities
from digital_twin.utils.coherence import coherence_filter
from digital_twin.utils.compress import compress
from digital_twin.observability.tracing import trace_span, add_span_attribute


@dataclass
class PipelineContext:
    """Context object passed through the pipeline stages."""
    query: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    conversation_context: Optional[Dict[str, Any]] = None
    intent: Optional[str] = None
    entities: Optional[List[str]] = None
    search_results: Optional[List[Dict[str, Any]]] = None
    coherent_content: Optional[str] = None
    compressed_content: Optional[str] = None
    plan: Optional[Dict[str, Any]] = None
    verified_response: Optional[str] = None
    final_response: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class DigitalTwinPipeline:
    """
    Main pipeline orchestrator with immutable stages:
    intent → hybrid_search → coherence → compress → planner → verifier → format
    """
    
    def __init__(self):
        self.logger = get_logger("pipeline")
        
    @log_execution_time
    async def process_query(self, query: str, user_id: Optional[str] = None, 
                          session_id: Optional[str] = None, conversation_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process a user query through the complete pipeline.
        
        Args:
            query: User query string
            user_id: Optional user identifier
            session_id: Optional session identifier
            conversation_context: Optional conversation context
            
        Returns:
            Dictionary containing the final response and metadata
        """
        # Initialize context
        context = PipelineContext(
            query=query,
            user_id=user_id,
            session_id=session_id,
            conversation_context=conversation_context or {}
        )
        
        try:
            # Execute pipeline stages in order
            context = await self._intent_stage(context)
            context = await self._hybrid_search_stage(context)
            context = await self._coherence_stage(context)
            context = await self._compress_stage(context)
            context = await self._router_stage(context)
            context = await self._planner_stage(context)
            context = await self._verifier_stage(context)
            context = await self._formatter_stage(context)
            
            return {
                "response": context.formatted_response or context.final_response or "Buddy, I'm having trouble processing that right now. Can you try rephrasing your question?",
                "metadata": context.metadata or {},
                "success": True,
                "search_results": context.search_results
            }
            
        except Exception as e:
            self.logger.error(f"Pipeline failed: {e}")
            return {
                "response": "I apologize, but I encountered an error processing your request. Please try again.",
                "metadata": {"error": str(e)},
                "success": False
            }
    
    @trace_span("intent_stage")
    async def _intent_stage(self, context: PipelineContext) -> PipelineContext:
        """
        Stage 1: Intent recognition and entity extraction.
        """
        add_span_attribute("query", context.query)
        
        # Simple intent classification
        query_lower = context.query.lower()
        if "optum" in query_lower:
            context.intent = "specific_topic"
            context.entities = ["Optum"]
        elif "meet" in query_lower or "schedule" in query_lower:
            context.intent = "meeting_scheduling"
            context.entities = []
        else:
            context.intent = "general"
            context.entities = []
        
        add_span_attribute("intent", context.intent)
        add_span_attribute("entities", str(context.entities))
        return context
    
    @trace_span("hybrid_search_stage")
    async def _hybrid_search_stage(self, context: PipelineContext) -> PipelineContext:
        """Hybrid search stage using vector and keyword search."""
        try:
            from skills.kb_search import hybrid_search
            
            # Get conversation context for enhanced queries
            conv_context = context.conversation_context or {}
            previous_queries = conv_context.get('previous_queries', [])
            search_history = conv_context.get('search_history', [])
            
            # Enhance query with context if this is a follow-up
            enhanced_query = context.query
            if previous_queries:
                # Check for follow-up indicators
                follow_up_indicators = ['what about', 'and', 'also', 'how about', 'tell me more', 'what else']
                is_follow_up = any(indicator in context.query.lower() for indicator in follow_up_indicators)
                
                if is_follow_up:
                    # Combine with previous query for better context
                    enhanced_query = f"{previous_queries[-1]} {context.query}"
            
            # Perform search with new two-phase semantic search
            search_results = hybrid_search(
                query=enhanced_query,
                entities=context.entities or [],
                k=10,
                recency_days=270  # Truth Policy compliance
            )
            
            # Merge with search history for consistency
            all_results = search_results + search_history
            unique_results = []
            seen_ids = set()
            
            for result in all_results:
                if result.chunk_id not in seen_ids:
                    unique_results.append(result)
                    seen_ids.add(result.chunk_id)
            
            # Keep top 10 results
            context.search_results = unique_results[:10]
            
            # Store search debug info in span attributes
            search_debug = {
                "vector_hits": len(search_results),
                "keyword_hits": len([r for r in search_results if hasattr(r, 'score')]),
                "rerank_latency_ms": 0,  # Will be updated if reranker is enabled
                "enhanced_query": enhanced_query,
                "original_query": context.query,
                "is_follow_up": len(previous_queries) > 0
            }
            
            # Add search debug to span attributes
            from digital_twin.observability.tracing import add_span_attribute
            for key, value in search_debug.items():
                add_span_attribute(key, value)
            
            self.logger.info(f"Search found {len(context.search_results)} results")
            
        except Exception as e:
            self.logger.error(f"Search stage failed: {e}")
            context.search_results = []
        
        return context

    @trace_span("coherence_stage")
    async def _coherence_stage(self, context: PipelineContext) -> PipelineContext:
        """Coherence filtering stage (optional)."""
        try:
            # Check if coherence filtering is enabled
            import os
            if os.getenv("COHERENCE_FILTER_ENABLED", "false").lower() != "true":
                self.logger.info("Coherence filtering disabled, skipping stage")
                context.coherent_content = context.search_results
                return context
            
            # Apply coherence filter
            if context.search_results:
                context.coherent_content = coherence_filter(context.search_results)
                add_span_attribute("input_chunks", len(context.search_results))
                add_span_attribute("filtered_chunks", len(context.coherent_content))
            else:
                context.coherent_content = []
                
        except Exception as e:
            self.logger.error(f"Coherence stage failed: {e}")
            context.coherent_content = context.search_results or []
        
        return context

    @trace_span("compress_stage")
    async def _compress_stage(self, context: PipelineContext) -> PipelineContext:
        """Content compression stage using Chain-of-Density."""
        try:
            # Use coherent_content if available, otherwise fall back to search_results
            input_content = context.coherent_content or context.search_results or []
            
            if input_content:
                # Compress the content using Chain-of-Density
                context.compressed_content = compress(input_content)
                add_span_attribute("input_chunks", len(input_content))
                add_span_attribute("compressed_length", len(context.compressed_content))
                self.logger.info(f"Compressed {len(input_content)} chunks to {len(context.compressed_content)} characters")
            else:
                context.compressed_content = ""
                add_span_attribute("input_chunks", 0)
                add_span_attribute("compressed_length", 0)
                
        except Exception as e:
            self.logger.error(f"Compression stage failed: {e}")
            context.compressed_content = ""
        
        return context

    @trace_span("router_stage")
    async def _router_stage(self, context: PipelineContext) -> PipelineContext:
        """
        Stage 5: Select appropriate model.
        """
        add_span_attribute("intent", context.intent)
        add_span_attribute("context_length", len(context.compressed_content or ""))
        
        try:
            from .router import pick
            context.selected_model = pick(context.intent, len(context.compressed_content or ""))
            add_span_attribute("selected_model", context.selected_model)
        except Exception as e:
            print(f"Router error: {e}")
            context.selected_model = "MODEL_GPT35"  # Default to cheap model
            add_span_attribute("router_error", str(e))
        return context

    @trace_span("planner_stage")
    async def _planner_stage(self, context: PipelineContext) -> PipelineContext:
        """Planning stage using ReAct pattern."""
        try:
            from llm.planner import react
            
            # Get conversation context for enhanced planning
            conv_context = context.conversation_context or {}
            previous_queries = conv_context.get('previous_queries', [])
            previous_responses = conv_context.get('previous_responses', [])
            
            # Create enhanced query with context
            enhanced_query = context.query
            if previous_queries:
                enhanced_query = f"Previous context: {previous_queries[-1]}. Current query: {context.query}"
            
            # Call planner with conversation context
            result = await react(
                model_key="MODEL_GPT4",
                query=enhanced_query,
                context=context.compressed_content or "",
                search_results=context.search_results or [],
                conversation_context=conv_context
            )
            
            context.plan = result
            add_span_attribute("model", result.get("model", "unknown"))
            add_span_attribute("query", context.query)
            add_span_attribute("has_summary", "summary" in result)
            add_span_attribute("has_actions", "actions" in result)
            
        except Exception as e:
            self.logger.error(f"Planning stage failed: {e}")
            context.plan = {"error": str(e)}
        
        return context

    @trace_span("verifier_stage")
    async def _verifier_stage(self, context: PipelineContext) -> PipelineContext:
        """Verification stage using Truth Policy."""
        try:
            from llm.verifier import check
            
            if context.plan and "error" not in context.plan:
                # Verify the plan against Truth Policy
                verification_result = await check(
                    draft=context.plan,
                    chunks=context.search_results or []
                )
                
                context.verified_response = verification_result
                add_span_attribute("has_draft", True)
                add_span_attribute("verification_valid", verification_result.get("valid", False))
            else:
                context.verified_response = {"valid": False, "reason": "no_plan"}
                add_span_attribute("has_draft", False)
                add_span_attribute("verification_valid", False)
                
        except Exception as e:
            self.logger.error(f"Verification stage failed: {e}")
            context.verified_response = {"valid": False, "reason": f"error: {e}"}
        
        return context

    @trace_span("formatter_stage")
    async def _formatter_stage(self, context: PipelineContext) -> PipelineContext:
        """Formatting stage for final response."""
        try:
            from orchestrator.formatter import render
            
            # Determine intent for formatting
            intent = context.intent or "general"
            
            # Check if we have a valid plan and verification
            if (context.plan and "error" not in context.plan and 
                context.verified_response and context.verified_response.get("valid", False)):
                
                # Format the response
                formatted_response = render(
                    intent=intent,
                    draft_json=context.plan,
                    search_results=context.search_results or []
                )
                
                context.formatted_response = formatted_response
                add_span_attribute("intent", intent)
                add_span_attribute("has_draft", True)
                add_span_attribute("response_length", len(formatted_response))
                
            else:
                # Handle error case
                error_reason = "unknown"
                if context.plan and "error" in context.plan:
                    error_reason = context.plan["error"]
                elif context.verified_response:
                    error_reason = context.verified_response.get("reason", "verification_failed")
                
                context.formatted_response = f"Sorry, I encountered an error: {error_reason}. Please try again."
                add_span_attribute("intent", intent)
                add_span_attribute("has_draft", False)
                add_span_attribute("response_length", len(context.formatted_response))
                
        except Exception as e:
            self.logger.error(f"Formatting stage failed: {e}")
            context.formatted_response = "Sorry, I encountered an error. Please try again."
        
        return context

# TODO(cursor): implement async run_pipeline(query:str, user_ctx)->dict
"""
Stage order (immutable):
1. intent, entities = classify(query)
2. chunks = kb_search.hybrid_search(query, entities, k=40)
3. chunks = coherence_filter(chunks)                # drop off-topic
4. context = compress(chunks, limit=1500_tokens)
5. model = router.pick(intent, context_len)
6. draft_json = planner.react(model, query, context, chunks)
7. verdict = verifier.check(draft_json, chunks)
8. if not verdict["valid"]: return safe_fail()
9. formatted_md = formatter.render(intent, draft_json)
10. save_context_bundle(user_ctx, query, entities, draft_json)
11. return formatted_md
"""


# Global pipeline instance
pipeline = DigitalTwinPipeline()

async def run_pipeline(query: str, user_ctx) -> str:
    """
    Main pipeline entry point.
    
    Args:
        query: User query string
        user_ctx: User context object
        
    Returns:
        Formatted response string
    """
    try:
        # Create a simple user context if needed
        if not hasattr(user_ctx, 'user_id'):
            user_ctx.user_id = getattr(user_ctx, 'user_id', 'default_user')
        if not hasattr(user_ctx, 'session_id'):
            user_ctx.session_id = getattr(user_ctx, 'session_id', 'default_session')
        
        # Get conversation context from user_ctx
        conversation_context = getattr(user_ctx, 'conversation_context', {})
        
        # Run the pipeline
        result = await pipeline.process_query(
            query=query,
            user_id=user_ctx.user_id,
            session_id=user_ctx.session_id,
            conversation_context=conversation_context
        )
        
        if result.get("success", False):
            return result["response"]
        else:
            return "Buddy, I'm having trouble processing that right now. Can you try rephrasing your question?"
            
    except Exception as e:
        logging.error(f"Pipeline error: {e}")
        return "Buddy, I encountered an error. Please try again." 