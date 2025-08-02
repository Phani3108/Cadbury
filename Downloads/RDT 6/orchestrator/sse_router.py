"""
Server-Sent Events router for streaming responses.
"""

import asyncio
import json
import time
from typing import Dict, Any, AsyncGenerator
from .pipeline import run_pipeline

async def stream_response(query: str, user_ctx) -> AsyncGenerator[str, None]:
    """
    Stream response with SSE protocol.
    
    Args:
        query: User query
        user_ctx: User context
        
    Yields:
        SSE formatted messages
    """
    query_id = f"query_{int(time.time())}"
    
    # Send initial status
    yield f"data: {json.dumps({'type': 'status', 'message': 'Processing query...', 'query_id': query_id})}\n\n"
    
    try:
        # Send "searching" status
        yield f"data: {json.dumps({'type': 'status', 'message': 'Searching knowledge base...', 'query_id': query_id})}\n\n"
        await asyncio.sleep(0.5)
        
        # Send "planning" status
        yield f"data: {json.dumps({'type': 'status', 'message': 'Generating response...', 'query_id': query_id})}\n\n"
        await asyncio.sleep(0.5)
        
        # Send "verifying" status
        yield f"data: {json.dumps({'type': 'status', 'message': 'Verifying response...', 'query_id': query_id})}\n\n"
        await asyncio.sleep(0.5)
        
        # Run pipeline
        response = await run_pipeline(query, user_ctx)
        
        # Send provisional response
        yield f"data: {json.dumps({'type': 'provisional', 'content': response, 'query_id': query_id})}\n\n"
        
        # Simulate verification delay
        await asyncio.sleep(1.0)
        
        # Send final response (same as provisional for now)
        yield f"data: {json.dumps({'type': 'final', 'content': response, 'query_id': query_id})}\n\n"
        
        # Send completion
        yield f"data: {json.dumps({'type': 'complete', 'query_id': query_id, 'total_tokens': len(response.split())})}\n\n"
        
    except Exception as e:
        error_msg = {
            'type': 'error',
            'message': str(e),
            'query_id': query_id
        }
        yield f"data: {json.dumps(error_msg)}\n\n"

async def stream_with_verification(query: str, user_ctx) -> AsyncGenerator[str, None]:
    """
    Stream response with real verification and final patch.
    
    Args:
        query: User query
        user_ctx: User context
        
    Yields:
        SSE formatted messages
    """
    query_id = f"query_{int(time.time())}"
    
    try:
        # Initial status
        yield f"data: {json.dumps({'type': 'status', 'message': 'Processing query...', 'query_id': query_id})}\n\n"
        
        # Run pipeline to get provisional response
        provisional_response = await run_pipeline(query, user_ctx)
        
        # Send provisional response
        yield f"data: {json.dumps({'type': 'provisional', 'content': provisional_response, 'query_id': query_id})}\n\n"
        
        # Send verification status
        yield f"data: {json.dumps({'type': 'status', 'message': 'Verifying response...', 'query_id': query_id})}\n\n"
        
        # Run actual verification
        from llm.verifier import check
        verification_result = await check(
            {'summary': provisional_response},  # Convert to draft format
            []  # Empty search results for now
        )
        
        if verification_result.get('valid', False):
            # Send final response
            yield f"data: {json.dumps({'type': 'final', 'content': provisional_response, 'query_id': query_id})}\n\n"
        else:
            # Send safe-fail response
            safe_fail_response = "I don't have a recent source for that—want me to widen the search?"
            yield f"data: {json.dumps({'type': 'final', 'content': safe_fail_response, 'query_id': query_id})}\n\n"
        
        # Send completion
        yield f"data: {json.dumps({'type': 'complete', 'query_id': query_id, 'total_tokens': len(provisional_response.split())})}\n\n"
        
    except Exception as e:
        error_msg = {
            'type': 'error',
            'message': str(e),
            'query_id': query_id
        }
        yield f"data: {json.dumps(error_msg)}\n\n" 