"""
FastAPI backend for CTO Twin
"""
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import os
import sys
import logging
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import Semantic Kernel components
from kernel.planners.react_planner import ReActPlanner
from kernel.skills.jira_skill import JiraSkill
from kernel.skills.outlook_skill import OutlookSkill
from kernel.skills.sharepoint_skill import SharePointSkill
from kernel.skills.search_skill import SearchSkill
from tools.graph_connector import GraphConnector
from memory.memory_manager import MemoryManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="CTO Twin API",
    description="API for CTO Twin - AI-powered assistant for technical leadership",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
try:
    # These would be properly initialized with actual credentials in production
    graph_connector = GraphConnector()
    memory_manager = MemoryManager()
    planner = ReActPlanner()
    
    # Initialize skills
    jira_skill = JiraSkill(graph_connector)
    outlook_skill = OutlookSkill(graph_connector)
    sharepoint_skill = SharePointSkill(graph_connector)
    search_skill = SearchSkill(memory_manager)
    
    logger.info("All components initialized successfully")
except Exception as e:
    logger.error(f"Error initializing components: {str(e)}")
    # In production, you might want to fail fast if components can't be initialized
    # For development, we'll continue with None values

# Request/Response models
class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    user_id: str

class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    thinking: Optional[str] = None
    timestamp: datetime = datetime.now()

class SearchRequest(BaseModel):
    query: str
    filters: Optional[Dict[str, Any]] = None
    top_k: int = 5

class SearchResponse(BaseModel):
    results: List[Dict[str, Any]]
    query: str
    timestamp: datetime = datetime.now()

class TicketRequest(BaseModel):
    title: str
    description: str
    project_key: str
    issue_type: str = "Task"
    priority: Optional[str] = None
    assignee: Optional[str] = None

class TicketResponse(BaseModel):
    ticket_id: str
    ticket_url: str
    status: str
    timestamp: datetime = datetime.now()

class AnalyticsRequest(BaseModel):
    metric: str
    timeframe: str
    filters: Optional[Dict[str, Any]] = None

class AnalyticsResponse(BaseModel):
    data: List[Dict[str, Any]]
    metric: str
    timeframe: str
    timestamp: datetime = datetime.now()

# Routes
@app.get("/")
def read_root():
    """Root endpoint"""
    return {"message": "Welcome to CTO Twin API", "status": "operational"}

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "components": {
            "graph_connector": graph_connector is not None,
            "memory_manager": memory_manager is not None,
            "planner": planner is not None,
            "jira_skill": jira_skill is not None,
            "outlook_skill": outlook_skill is not None,
            "sharepoint_skill": sharepoint_skill is not None,
            "search_skill": search_skill is not None,
        },
        "timestamp": datetime.now()
    }

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Chat endpoint for conversational interactions"""
    try:
        logger.info(f"Chat request received: {request.message[:50]}...")
        
        # In a real implementation, this would use the ReAct planner
        # to process the message and generate a response
        response = "This is a placeholder response. In production, this would use the Semantic Kernel with ReAct planning."
        conversation_id = request.conversation_id or "new_conversation_id"
        
        return ChatResponse(
            response=response,
            conversation_id=conversation_id,
            thinking="Thinking process would be shown here"
        )
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search", response_model=SearchResponse)
async def search_endpoint(request: SearchRequest):
    """Search endpoint for querying knowledge base"""
    try:
        logger.info(f"Search request received: {request.query}")
        
        # In a real implementation, this would use the search skill
        # to query Azure AI Search
        results = [
            {"title": "Sample document 1", "content": "This is a sample document", "score": 0.95},
            {"title": "Sample document 2", "content": "Another sample document", "score": 0.85},
        ]
        
        return SearchResponse(
            results=results,
            query=request.query
        )
    except Exception as e:
        logger.error(f"Error in search endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ticket", response_model=TicketResponse)
async def ticket_endpoint(request: TicketRequest):
    """Ticket endpoint for creating Jira tickets"""
    try:
        logger.info(f"Ticket request received: {request.title}")
        
        # In a real implementation, this would use the Jira skill
        # to create a ticket via Microsoft Graph connector
        ticket_id = "PROJ-123"
        ticket_url = f"https://your-jira-instance.atlassian.net/browse/{ticket_id}"
        
        return TicketResponse(
            ticket_id=ticket_id,
            ticket_url=ticket_url,
            status="Created"
        )
    except Exception as e:
        logger.error(f"Error in ticket endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analytics", response_model=AnalyticsResponse)
async def analytics_endpoint(request: AnalyticsRequest):
    """Analytics endpoint for retrieving metrics"""
    try:
        logger.info(f"Analytics request received: {request.metric} for {request.timeframe}")
        
        # In a real implementation, this would query various data sources
        # to compile analytics
        data = [
            {"date": "2025-07-01", "value": 42},
            {"date": "2025-07-02", "value": 47},
            {"date": "2025-07-03", "value": 53},
            {"date": "2025-07-04", "value": 59},
            {"date": "2025-07-05", "value": 65},
            {"date": "2025-07-06", "value": 71},
            {"date": "2025-07-07", "value": 68},
        ]
        
        return AnalyticsResponse(
            data=data,
            metric=request.metric,
            timeframe=request.timeframe
        )
    except Exception as e:
        logger.error(f"Error in analytics endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
