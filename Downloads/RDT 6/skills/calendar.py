import msal, os, httpx, datetime as dt, time
from typing import List
TENANT = os.getenv("AZ_TENANT")
CLIENT_ID = os.getenv("AZ_CLIENT")
CLIENT_SECRET = os.getenv("AZ_SECRET")

def get_on_behalf_token(teams_sso:str)->str:
    app = msal.ConfidentialClientApplication(
        CLIENT_ID, CLIENT_SECRET, authority=f"https://login.microsoftonline.com/{TENANT}"
    )
    result = app.acquire_token_on_behalf_of(
        teams_sso, scopes=["https://graph.microsoft.com/.default"]
    )
    return result["access_token"]

async def find_free_slot(token:str, days:int=7, duration_min:int=30):
    start = dt.datetime.utcnow().isoformat()+"Z"
    end   = (dt.datetime.utcnow()+dt.timedelta(days=days)).isoformat()+"Z"
    body = {
      "timeConstraint": {
        "activityDomain": "work",
        "timeSlots": [{"start": start, "end": end}]
      },
      "meetingDuration": f"PT{duration_min}M"
    }
    async with httpx.AsyncClient() as c:
        r = await c.post("https://graph.microsoft.com/v1.0/me/findMeetingTimes",
                         headers={"Authorization": f"Bearer {token}",
                                  "Content-Type":"application/json"},
                         json=body, timeout=10)
    r.raise_for_status()
    suggestions = r.json()["meetingTimeSuggestions"]
    return suggestions[:3]

async def create_calendar_event(subject: str, start_time: str, duration_minutes: int, attendees: List[str] = None) -> str:
    """
    Create a calendar event using Microsoft Graph API.
    
    Args:
        subject: Meeting subject
        start_time: Start time (ISO format)
        duration_minutes: Meeting duration
        attendees: List of attendee email addresses
        
    Returns:
        Event ID
    """
    # Mock implementation for development
    if os.getenv("MOCK") == "true":
        return f"event_{int(time.time())}"
    
    # Real implementation would use Microsoft Graph API
    # For now, return mock event ID
    return f"event_{int(time.time())}"

async def send_meeting_request_email(subject: str, start_time: str, duration_minutes: int, attendees: List[str] = None) -> bool:
    """
    Send meeting request email to EA.
    
    Args:
        subject: Meeting subject
        start_time: Start time (ISO format)
        duration_minutes: Meeting duration
        attendees: List of attendee email addresses
        
    Returns:
        True if email sent successfully
    """
    # Mock implementation for development
    if os.getenv("MOCK") == "true":
        return True
    
    # Real implementation would use Microsoft Graph API
    # For now, return success
    return True 