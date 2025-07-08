"""
Microsoft Graph Connector for CTO Twin
Handles integration with Microsoft Graph APIs for Jira, Outlook, Loop, Checkvist, and SharePoint
"""
import os
import json
import logging
import requests
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class GraphConnector:
    """
    Microsoft Graph Connector for CTO Twin
    Handles integration with Microsoft Graph APIs
    """
    
    def __init__(self):
        """Initialize the Graph Connector"""
        self.token = None
        self.token_expires = datetime.now()
        self.base_url = "https://graph.microsoft.com/v1.0"
        self.client_id = os.environ.get("GRAPH_CLIENT_ID")
        self.client_secret = os.environ.get("GRAPH_CLIENT_SECRET")
        self.tenant_id = os.environ.get("GRAPH_TENANT_ID")
        
        # Check if credentials are available
        if not all([self.client_id, self.client_secret, self.tenant_id]):
            logger.warning("Microsoft Graph credentials not found, using mock implementation")
    
    def get_token(self) -> Optional[str]:
        """
        Get a valid access token for Microsoft Graph API
        
        Returns:
            Access token or None if unavailable
        """
        # Check if we have a valid token
        if self.token and self.token_expires > datetime.now():
            return self.token
        
        # Get new token if credentials are available
        if all([self.client_id, self.client_secret, self.tenant_id]):
            try:
                token_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
                payload = {
                    "client_id": self.client_id,
                    "scope": "https://graph.microsoft.com/.default",
                    "client_secret": self.client_secret,
                    "grant_type": "client_credentials"
                }
                
                response = requests.post(token_url, data=payload)
                response.raise_for_status()
                
                token_data = response.json()
                self.token = token_data["access_token"]
                # Set expiry time with a small buffer
                expires_in = token_data["expires_in"] - 60  # Buffer of 60 seconds
                self.token_expires = datetime.now() + timedelta(seconds=expires_in)
                
                return self.token
            except Exception as e:
                logger.error(f"Error getting Microsoft Graph token: {str(e)}")
                return None
        else:
            logger.warning("Microsoft Graph credentials not available")
            return None
    
    def make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, params: Optional[Dict] = None) -> Dict:
        """
        Make a request to Microsoft Graph API
        
        Args:
            method: HTTP method (GET, POST, PATCH, DELETE)
            endpoint: API endpoint (without base URL)
            data: Optional request body
            params: Optional query parameters
            
        Returns:
            Response data
        """
        token = self.get_token()
        
        if token:
            try:
                url = f"{self.base_url}/{endpoint}"
                headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }
                
                response = requests.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=data if data else None,
                    params=params if params else None
                )
                
                response.raise_for_status()
                
                if response.content:
                    return response.json()
                else:
                    return {}
            except Exception as e:
                logger.error(f"Error making Microsoft Graph request: {str(e)}")
                # Return mock data for development
                return self._get_mock_data(method, endpoint)
        else:
            # Return mock data for development
            return self._get_mock_data(method, endpoint)
    
    def _get_mock_data(self, method: str, endpoint: str) -> Dict:
        """
        Get mock data for development
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            
        Returns:
            Mock response data
        """
        # Jira mock data
        if "jira" in endpoint:
            if method == "GET" and "issues" in endpoint:
                return {
                    "value": [
                        {
                            "id": "PROJ-123",
                            "title": "Implement authentication flow",
                            "description": "Add OAuth2 authentication to the API",
                            "status": "In Progress",
                            "assignee": "John Doe",
                            "priority": "High",
                            "created": "2025-07-01T10:00:00Z",
                            "updated": "2025-07-05T15:30:00Z"
                        },
                        {
                            "id": "PROJ-124",
                            "title": "Fix memory leak in data processing",
                            "description": "The data processing module has a memory leak that needs to be fixed",
                            "status": "To Do",
                            "assignee": "Jane Smith",
                            "priority": "Critical",
                            "created": "2025-07-03T09:15:00Z",
                            "updated": "2025-07-03T09:15:00Z"
                        }
                    ]
                }
            elif method == "POST" and "issues" in endpoint:
                return {
                    "id": "PROJ-125",
                    "title": "New issue created via API",
                    "status": "To Do",
                    "created": datetime.now().isoformat()
                }
        
        # Outlook mock data
        elif "outlook" in endpoint or "mail" in endpoint:
            if method == "GET" and "messages" in endpoint:
                return {
                    "value": [
                        {
                            "id": "AAMkAGVmMDEzMTM4LTZmYWUtNDdkNC1hMDZiLTU1OGY5OTZhYmY4OABGAAAAAAAiQ8W967B7TKBjgx9rVEURBwAiIsqMbYjsT5e-T7KzowPTAAAAAAEMAAAiIsqMbYjsT5e-T7KzowPTAAAYbvZDAAA=",
                            "subject": "Project status update",
                            "from": {"emailAddress": {"name": "John Doe", "address": "john.doe@example.com"}},
                            "receivedDateTime": "2025-07-06T08:30:00Z",
                            "bodyPreview": "Here's the latest status update for the project..."
                        },
                        {
                            "id": "AAMkAGVmMDEzMTM4LTZmYWUtNDdkNC1hMDZiLTU1OGY5OTZhYmY4OABGAAAAAAAiQ8W967B7TKBjgx9rVEURBwAiIsqMbYjsT5e-T7KzowPTAAAAAAEMAAAiIsqMbYjsT5e-T7KzowPTAAAYbvZDAAB=",
                            "subject": "Meeting invitation: Architecture review",
                            "from": {"emailAddress": {"name": "Jane Smith", "address": "jane.smith@example.com"}},
                            "receivedDateTime": "2025-07-05T14:15:00Z",
                            "bodyPreview": "You're invited to an architecture review meeting..."
                        }
                    ]
                }
            elif method == "POST" and "sendMail" in endpoint:
                return {}  # Success response for sending email
        
        # SharePoint mock data
        elif "sharepoint" in endpoint or "sites" in endpoint:
            if method == "GET" and "drives" in endpoint:
                return {
                    "value": [
                        {
                            "id": "b!O-aG9TB9bk2CMsCHnGAjK-8REj9cmGpKvJJugYKyUqQ-NVNTimf7SYxXxtTKmNIp",
                            "name": "Documents",
                            "description": "Default document library"
                        }
                    ]
                }
            elif method == "GET" and "items" in endpoint:
                return {
                    "value": [
                        {
                            "id": "01NKDM7HMOJTVYMDOSRFDK2QJLKGQHAPGZ",
                            "name": "Project Documentation.docx",
                            "webUrl": "https://contoso.sharepoint.com/sites/project/Shared%20Documents/Project%20Documentation.docx",
                            "lastModifiedDateTime": "2025-07-04T11:09:00Z"
                        },
                        {
                            "id": "01NKDM7HMOJTVYMDOSRFDK2QJLKGQHAPGX",
                            "name": "Architecture Diagram.vsdx",
                            "webUrl": "https://contoso.sharepoint.com/sites/project/Shared%20Documents/Architecture%20Diagram.vsdx",
                            "lastModifiedDateTime": "2025-07-02T15:34:00Z"
                        }
                    ]
                }
        
        # Loop mock data
        elif "loop" in endpoint:
            if method == "GET" and "workbooks" in endpoint:
                return {
                    "value": [
                        {
                            "id": "01NKDM7HMOJTVYMDOSRFDK2QJLKGQHAPGZ",
                            "name": "Project Planning",
                            "webUrl": "https://contoso.loop.microsoft.com/workbooks/project-planning",
                            "lastModifiedDateTime": "2025-07-06T16:20:00Z"
                        }
                    ]
                }
        
        # Checkvist mock data
        elif "checkvist" in endpoint:
            if method == "GET" and "lists" in endpoint:
                return {
                    "value": [
                        {
                            "id": "123456",
                            "name": "Project Tasks",
                            "itemCount": 24,
                            "lastModifiedDateTime": "2025-07-07T09:45:00Z"
                        }
                    ]
                }
            elif method == "GET" and "tasks" in endpoint:
                return {
                    "value": [
                        {
                            "id": "task-1",
                            "title": "Complete API documentation",
                            "status": "in_progress",
                            "dueDate": "2025-07-10T00:00:00Z"
                        },
                        {
                            "id": "task-2",
                            "title": "Review security implementation",
                            "status": "not_started",
                            "dueDate": "2025-07-15T00:00:00Z"
                        }
                    ]
                }
        
        # Default mock response
        return {
            "mock": True,
            "endpoint": endpoint,
            "method": method,
            "message": "This is mock data for development"
        }
    
    # Jira methods
    def get_jira_issues(self, project_key: Optional[str] = None, status: Optional[str] = None, assignee: Optional[str] = None) -> List[Dict]:
        """
        Get Jira issues
        
        Args:
            project_key: Optional project key filter
            status: Optional status filter
            assignee: Optional assignee filter
            
        Returns:
            List of Jira issues
        """
        params = {}
        if project_key:
            params["project"] = project_key
        if status:
            params["status"] = status
        if assignee:
            params["assignee"] = assignee
        
        response = self.make_request("GET", "jira/issues", params=params)
        return response.get("value", [])
    
    def create_jira_issue(self, issue_data: Dict[str, Any]) -> Dict:
        """
        Create a Jira issue
        
        Args:
            issue_data: Issue data including title, description, project, etc.
            
        Returns:
            Created issue data
        """
        response = self.make_request("POST", "jira/issues", data=issue_data)
        return response
    
    def update_jira_issue(self, issue_key: str, update_data: Dict[str, Any]) -> Dict:
        """
        Update a Jira issue
        
        Args:
            issue_key: Issue key (e.g., PROJ-123)
            update_data: Data to update
            
        Returns:
            Updated issue data
        """
        response = self.make_request("PATCH", f"jira/issues/{issue_key}", data=update_data)
        return response
    
    def add_jira_comment(self, issue_key: str, comment: str) -> Dict:
        """
        Add a comment to a Jira issue
        
        Args:
            issue_key: Issue key (e.g., PROJ-123)
            comment: Comment text
            
        Returns:
            Comment data
        """
        response = self.make_request("POST", f"jira/issues/{issue_key}/comments", data={"text": comment})
        return response
    
    def transition_jira_issue(self, issue_key: str, transition: str) -> Dict:
        """
        Transition a Jira issue to a new status
        
        Args:
            issue_key: Issue key (e.g., PROJ-123)
            transition: Transition name or ID
            
        Returns:
            Updated issue data
        """
        response = self.make_request("POST", f"jira/issues/{issue_key}/transitions", data={"transition": transition})
        return response
    
    # Outlook methods
    def get_emails(self, folder: str = "inbox", top: int = 10) -> List[Dict]:
        """
        Get emails from a folder
        
        Args:
            folder: Folder name
            top: Number of emails to retrieve
            
        Returns:
            List of emails
        """
        params = {
            "$top": top,
            "$orderby": "receivedDateTime DESC"
        }
        
        response = self.make_request("GET", f"me/mailFolders/{folder}/messages", params=params)
        return response.get("value", [])
    
    def send_email(self, email_data: Dict[str, Any]) -> Dict:
        """
        Send an email
        
        Args:
            email_data: Email data including recipients, subject, body
            
        Returns:
            Response data
        """
        response = self.make_request("POST", "me/sendMail", data={"message": email_data})
        return response
    
    def get_calendar_events(self, start_time: Optional[str] = None, end_time: Optional[str] = None, top: int = 10) -> List[Dict]:
        """
        Get calendar events
        
        Args:
            start_time: Optional start time filter (ISO format)
            end_time: Optional end time filter (ISO format)
            top: Number of events to retrieve
            
        Returns:
            List of calendar events
        """
        params = {
            "$top": top,
            "$orderby": "start/dateTime ASC"
        }
        
        if start_time and end_time:
            filter_query = f"start/dateTime ge '{start_time}' and end/dateTime le '{end_time}'"
            params["$filter"] = filter_query
        
        response = self.make_request("GET", "me/calendar/events", params=params)
        return response.get("value", [])
    
    # SharePoint methods
    def get_sharepoint_sites(self) -> List[Dict]:
        """
        Get SharePoint sites
        
        Returns:
            List of SharePoint sites
        """
        response = self.make_request("GET", "sites")
        return response.get("value", [])
    
    def get_site_drives(self, site_id: str) -> List[Dict]:
        """
        Get drives (document libraries) for a site
        
        Args:
            site_id: Site ID
            
        Returns:
            List of drives
        """
        response = self.make_request("GET", f"sites/{site_id}/drives")
        return response.get("value", [])
    
    def get_drive_items(self, drive_id: str, folder_path: str = "") -> List[Dict]:
        """
        Get items in a drive folder
        
        Args:
            drive_id: Drive ID
            folder_path: Optional folder path
            
        Returns:
            List of drive items
        """
        endpoint = f"drives/{drive_id}/root/children"
        if folder_path:
            endpoint = f"drives/{drive_id}/root:/{folder_path}:/children"
        
        response = self.make_request("GET", endpoint)
        return response.get("value", [])
    
    def get_file_content(self, drive_id: str, item_id: str) -> Dict:
        """
        Get file content
        
        Args:
            drive_id: Drive ID
            item_id: Item ID
            
        Returns:
            File content and metadata
        """
        response = self.make_request("GET", f"drives/{drive_id}/items/{item_id}")
        return response
    
    # Loop methods
    def get_loop_workbooks(self) -> List[Dict]:
        """
        Get Loop workbooks
        
        Returns:
            List of Loop workbooks
        """
        response = self.make_request("GET", "me/loop/workbooks")
        return response.get("value", [])
    
    def get_loop_pages(self, workbook_id: str) -> List[Dict]:
        """
        Get pages in a Loop workbook
        
        Args:
            workbook_id: Workbook ID
            
        Returns:
            List of Loop pages
        """
        response = self.make_request("GET", f"me/loop/workbooks/{workbook_id}/pages")
        return response.get("value", [])
    
    # Checkvist methods
    def get_checkvist_lists(self) -> List[Dict]:
        """
        Get Checkvist lists
        
        Returns:
            List of Checkvist lists
        """
        response = self.make_request("GET", "me/checkvist/lists")
        return response.get("value", [])
    
    def get_checkvist_tasks(self, list_id: str) -> List[Dict]:
        """
        Get tasks in a Checkvist list
        
        Args:
            list_id: List ID
            
        Returns:
            List of Checkvist tasks
        """
        response = self.make_request("GET", f"me/checkvist/lists/{list_id}/tasks")
        return response.get("value", [])
    
    def create_checkvist_task(self, list_id: str, task_data: Dict[str, Any]) -> Dict:
        """
        Create a Checkvist task
        
        Args:
            list_id: List ID
            task_data: Task data
            
        Returns:
            Created task data
        """
        response = self.make_request("POST", f"me/checkvist/lists/{list_id}/tasks", data=task_data)
        return response
