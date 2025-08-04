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
        """
        Stage 2: Multi-document semantic search with conversation context.
        """
        add_span_attribute("query", context.query)
        add_span_attribute("entities", str(context.entities or []))
        
        try:
            from skills.kb_search import hybrid_search
            
            # Get conversation context
            conv_context = context.conversation_context or {}
            previous_queries = conv_context.get("previous_queries", [])
            search_history = conv_context.get("search_history", [])
            
            # Enhance query with context if this is a follow-up
            enhanced_query = context.query
            if previous_queries and len(previous_queries) > 0:
                last_query = previous_queries[-1]
                # Check if this is a follow-up question
                follow_up_indicators = ["what about", "tell me more", "and", "also", "additionally", "furthermore", "moreover", "specifically", "in detail", "elaborate"]
                is_follow_up = any(indicator in context.query.lower() for indicator in follow_up_indicators)
                
                if is_follow_up:
                    # Combine with previous query for better context
                    enhanced_query = f"{last_query} {context.query}"
                    add_span_attribute("enhanced_query", enhanced_query)
            
            # Perform search
            context.search_results = hybrid_search(enhanced_query, context.entities or [], k=10)
            
            # Merge with search history for consistency
            if search_history and len(search_history) > 0:
                # Combine current results with historical results, prioritizing recent
                all_results = context.search_results + search_history
                # Remove duplicates based on chunk_id
                seen_chunks = set()
                unique_results = []
                for result in all_results:
                    chunk_id = getattr(result, 'chunk_id', str(result))
                    if chunk_id not in seen_chunks:
                        seen_chunks.add(chunk_id)
                        unique_results.append(result)
                # Keep top 10 most relevant results
                context.search_results = unique_results[:10]
            
            add_span_attribute("search_results_count", len(context.search_results))
            add_span_attribute("conversation_context_used", bool(conv_context))
            
        except Exception as e:
            print(f"Search error: {e}")
            context.search_results = []
            add_span_attribute("search_error", str(e))
        return context

    @trace_span("coherence_stage")
    async def _coherence_stage(self, context: PipelineContext) -> PipelineContext:
        """
        Stage 3: Filter off-topic chunks.
        """
        add_span_attribute("input_chunks", len(context.search_results or []))
        
        if context.search_results:
            context.search_results = coherence_filter(context.search_results, context.query)
            add_span_attribute("filtered_chunks", len(context.search_results))
        return context

    @trace_span("compress_stage")
    async def _compress_stage(self, context: PipelineContext) -> PipelineContext:
        """
        Stage 4: Compress chunks to token limit.
        """
        add_span_attribute("input_chunks", len(context.search_results or []))
        
        if context.search_results:
            context.compressed_content = compress(context.search_results, context.query)
            add_span_attribute("compressed_length", len(context.compressed_content))
        else:
            context.compressed_content = ""
            add_span_attribute("compressed_length", 0)
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
        """
        Stage 6: Generate response using ReAct planner.
        """
        add_span_attribute("model", context.selected_model)
        add_span_attribute("query", context.query)
        
        try:
            from llm.planner import react
            
            context.draft_json = await react(
                context.selected_model,
                context.query,
                context.compressed_content or "",
                context.search_results or [],
                context.conversation_context
            )
            add_span_attribute("has_summary", bool(context.draft_json.get("summary")))
            add_span_attribute("has_actions", bool(context.draft_json.get("actions")))
        except Exception as e:
            print(f"Planner error: {e}")
            context.draft_json = {
                "summary": "Unable to process query",
                "insights": [],
                "discussion": [],
                "actions": [],
                "ramki_quote": "",
                "followups": ["Please try again"],
                "sources": []
            }
            add_span_attribute("planner_error", str(e))
        return context

    @trace_span("verifier_stage")
    async def _verifier_stage(self, context: PipelineContext) -> PipelineContext:
        """
        Stage 7: Verify response against truth policy.
        """
        add_span_attribute("has_draft", bool(context.draft_json))
        
        try:
            from llm.verifier import check
            context.verification_result = await check(
                context.draft_json,
                context.search_results or []
            )
            add_span_attribute("verification_valid", context.verification_result.get("valid", False))
            
            # If verification fails, set safe_fail flag
            if not context.verification_result.get("valid", False):
                if context.draft_json:
                    context.draft_json["safe_fail"] = True
                    
        except Exception as e:
            # Log verification error and set safe_fail
            print(f"Verification failed: {e}")
            if context.draft_json:
                context.draft_json["safe_fail"] = True
            context.verification_result = {"valid": False, "reason": str(e)}
            
        return context

    @trace_span("formatter_stage")
    async def _formatter_stage(self, context: PipelineContext) -> PipelineContext:
        """
        Stage 8: Format response for user.
        """
        add_span_attribute("intent", context.intent)
        add_span_attribute("has_draft", bool(context.draft_json))
        
        from .formatter import render
        context.formatted_response = render(
            context.intent or "INSIGHT",
            context.draft_json
        )
        add_span_attribute("response_length", len(context.formatted_response or ""))
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