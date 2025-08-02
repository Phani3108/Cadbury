from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
import asyncio
import json
import time
from .pipeline import run_pipeline
from .auth import get_current_user, create_jwt_token
from .sse_router import stream_with_verification

app = FastAPI(title="Digital Twin API", version="1.0.0")

class QueryRequest(BaseModel):
    query: str
    user_id: Optional[str] = "default"
    session_id: Optional[str] = "default"

class QueryResponse(BaseModel):
    response: str
    model_used: str
    processing_time: float

class StreamResponse(BaseModel):
    query_id: str
    parent_query_id: Optional[str] = None

@app.post("/chat", response_model=QueryResponse)
async def chat(request: QueryRequest, user: Dict[str, Any] = Depends(get_current_user)):
    """Process a user query through the Digital Twin pipeline."""
    try:
        # Create a simple user context
        user_ctx = type('UserContext', (), {
            'user_id': user.get('user_id', request.user_id),
            'session_id': request.session_id
        })()
        
        # Run the pipeline
        response = await run_pipeline(request.query, user_ctx)
        
        return QueryResponse(
            response=response,
            model_used="digital_twin",  # We'll enhance this later
            processing_time=0.0  # We'll add timing later
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "mode": "development"}

@app.get("/config")
async def get_config():
    """Get current configuration (for debugging)."""
    from digital_twin.utils.config import is_development, is_production
    return {
        "mode": "development" if is_development() else "production",
        "development": is_development(),
        "production": is_production()
    }

@app.post("/stream")
async def stream_chat(request: QueryRequest):
    """Stream chat response with Server-Sent Events and verification."""
    
    async def generate_stream():
        try:
            # Create user context
            user_ctx = type('UserContext', (), {
                'user_id': request.user_id,
                'session_id': request.session_id
            })()
            
            # Use SSE router with verification
            async for message in stream_with_verification(request.query, user_ctx):
                yield message
                
        except Exception as e:
            error = {
                'type': 'error',
                'message': str(e),
                'query_id': f"query_{int(time.time())}"
            }
            yield f"data: {json.dumps(error)}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream"
        }
    )

@app.post("/feedback")
async def submit_feedback(feedback: Dict[str, Any]):
    """Submit user feedback for a query."""
    # TODO: Implement feedback storage to Cosmos DB
    return {"status": "received", "feedback_id": f"fb_{int(time.time())}"}

@app.post("/api/confirm_slot")
async def confirm_slot(slot_data: Dict[str, Any]):
    """Confirm a calendar slot selection."""
    try:
        slot_time = slot_data.get("time")
        duration = slot_data.get("duration", 30)
        topic = slot_data.get("topic", "Meeting")
        attendees = slot_data.get("attendees", [])
        priority = slot_data.get("priority", "P3")
        
        # Validate required fields
        if not slot_time:
            raise HTTPException(status_code=400, detail="Slot time is required")
        
        # Create calendar event using Graph API
        try:
            from skills.calendar import create_calendar_event
            event_id = await create_calendar_event(
                subject=f"[{priority}] {topic}",
                start_time=slot_time,
                duration_minutes=duration,
                attendees=attendees
            )
            
            return {
                "status": "confirmed",
                "message": f"Meeting scheduled: {topic} on {slot_time}",
                "event_id": event_id,
                "priority": priority
            }
            
        except Exception as calendar_error:
            # Fallback to email notification
            from skills.calendar import send_meeting_request_email
            await send_meeting_request_email(
                subject=f"[{priority}] Meeting Request: {topic}",
                start_time=slot_time,
                duration_minutes=duration,
                attendees=attendees
            )
            
            return {
                "status": "pending",
                "message": f"Meeting request sent to EA for {topic}",
                "priority": priority
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 