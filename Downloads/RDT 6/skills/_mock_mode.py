import os
from typing import List, Dict, Any
from digital_twin.utils.config import is_mock_tools

MOCK = is_mock_tools()

async def calendar_find_free_slot(*args, **kwargs):
    """Mock calendar function for development."""
    if MOCK:
        return [
            {
                "start": "2025-08-05T09:00:00Z",
                "end": "2025-08-05T09:30:00Z",
                "confidence": "high"
            },
            {
                "start": "2025-08-05T14:00:00Z", 
                "end": "2025-08-05T14:30:00Z",
                "confidence": "medium"
            }
        ]
    from skills.calendar import find_free_slot
    return await find_free_slot(*args, **kwargs)

async def jira_create(*args, **kwargs):
    """Mock Jira function for development."""
    if MOCK:
        return "MOCK-123"
    from skills.jira import create
    return await create(*args, **kwargs)

async def jira_status(*args, **kwargs):
    """Mock Jira status function for development."""
    if MOCK:
        return {
            "key": "MOCK-123",
            "fields": {
                "status": {"name": "In Progress"},
                "summary": "Mock ticket for development"
            }
        }
    from skills.jira import status
    return await status(*args, **kwargs)

async def jira_status_search(*args, **kwargs):
    """Mock Jira status search function for development."""
    if MOCK:
        return [
            {
                "id": "MOCK-123",
                "summary": "Mock Optum blocker ticket",
                "owner": "John Doe",
                "priority": "High",
                "status": "In Progress"
            },
            {
                "id": "MOCK-456", 
                "summary": "Mock Optum integration issue",
                "owner": "Jane Smith",
                "priority": "Medium",
                "status": "To Do"
            }
        ]
    from skills.jira import status_search
    return await status_search(*args, **kwargs) 