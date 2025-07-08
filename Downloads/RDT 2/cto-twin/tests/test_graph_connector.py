"""
Tests for the GraphConnector class in the CTO Twin application
"""
import os
import sys
import pytest
from unittest.mock import MagicMock, patch
import json
import requests
from datetime import datetime, timedelta

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the component to test
from tools.graph_connector import GraphConnector


class TestGraphConnector:
    """Tests for the GraphConnector class"""
    
    @pytest.fixture
    def graph_connector(self):
        """Create a GraphConnector instance"""
        with patch.dict(os.environ, {
            "GRAPH_CLIENT_ID": "mock-client-id",
            "GRAPH_CLIENT_SECRET": "mock-client-secret",
            "GRAPH_TENANT_ID": "mock-tenant-id"
        }):
            return GraphConnector()
    
    def test_initialization(self, graph_connector):
        """Test that the connector initializes correctly"""
        assert graph_connector.client_id == "mock-client-id"
        assert graph_connector.client_secret == "mock-client-secret"
        assert graph_connector.tenant_id == "mock-tenant-id"
        assert graph_connector.base_url == "https://graph.microsoft.com/v1.0"
        assert graph_connector.token is None
        assert graph_connector.token_expires <= datetime.now()
    
    @patch('requests.post')
    def test_get_token(self, mock_post, graph_connector):
        """Test getting an access token"""
        # Mock the response from the token endpoint
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "access_token": "mock-access-token",
            "expires_in": 3600
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        # Call the get_token method
        token = graph_connector.get_token()
        
        # Verify the result
        assert token == "mock-access-token"
        assert graph_connector.token == "mock-access-token"
        assert graph_connector.token_expires > datetime.now()
        
        # Verify the request
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert args[0] == f"https://login.microsoftonline.com/{graph_connector.tenant_id}/oauth2/v2.0/token"
        assert kwargs["data"]["client_id"] == graph_connector.client_id
        assert kwargs["data"]["client_secret"] == graph_connector.client_secret
        assert kwargs["data"]["scope"] == "https://graph.microsoft.com/.default"
        assert kwargs["data"]["grant_type"] == "client_credentials"
    
    @patch('requests.post')
    def test_get_token_error(self, mock_post, graph_connector):
        """Test error handling when getting a token"""
        # Mock the response to raise an exception
        mock_post.side_effect = requests.exceptions.RequestException("Mock error")
        
        # Call the get_token method
        token = graph_connector.get_token()
        
        # Verify the result
        assert token is None
    
    @patch('requests.request')
    def test_make_request(self, mock_request, graph_connector):
        """Test making a request to the Graph API"""
        # Mock the get_token method
        graph_connector.get_token = MagicMock(return_value="mock-access-token")
        
        # Mock the response from the API
        mock_response = MagicMock()
        mock_response.json.return_value = {"value": ["item1", "item2"]}
        mock_response.raise_for_status = MagicMock()
        mock_response.content = b'{"value": ["item1", "item2"]}'
        mock_request.return_value = mock_response
        
        # Call the make_request method
        result = graph_connector.make_request("GET", "users")
        
        # Verify the result
        assert result == {"value": ["item1", "item2"]}
        
        # Verify the request
        mock_request.assert_called_once()
        args, kwargs = mock_request.call_args
        assert kwargs["method"] == "GET"
        assert kwargs["url"] == f"{graph_connector.base_url}/users"
        assert kwargs["headers"]["Authorization"] == "Bearer mock-access-token"
        assert kwargs["headers"]["Content-Type"] == "application/json"
    
    @patch('requests.request')
    def test_make_request_error(self, mock_request, graph_connector):
        """Test error handling when making a request"""
        # Mock the get_token method
        graph_connector.get_token = MagicMock(return_value="mock-access-token")
        
        # Mock the response to raise an exception
        mock_request.side_effect = requests.exceptions.RequestException("Mock error")
        
        # Call the make_request method
        result = graph_connector.make_request("GET", "users")
        
        # Verify that we get mock data
        assert "mock" in result
        assert result["mock"] is True
        assert result["endpoint"] == "users"
        assert result["method"] == "GET"
    
    def test_make_request_no_token(self, graph_connector):
        """Test making a request without a token"""
        # Mock the get_token method to return None
        graph_connector.get_token = MagicMock(return_value=None)
        
        # Call the make_request method
        result = graph_connector.make_request("GET", "users")
        
        # Verify that we get mock data
        assert "mock" in result
        assert result["mock"] is True
        assert result["endpoint"] == "users"
        assert result["method"] == "GET"
    
    def test_get_jira_issues(self, graph_connector):
        """Test getting Jira issues"""
        # Mock the make_request method
        mock_response = {
            "value": [
                {
                    "id": "PROJ-123",
                    "title": "Test issue",
                    "status": "In Progress"
                }
            ]
        }
        graph_connector.make_request = MagicMock(return_value=mock_response)
        
        # Call the get_jira_issues method
        issues = graph_connector.get_jira_issues("PROJ", "In Progress", "John Doe")
        
        # Verify the result
        assert issues == mock_response["value"]
        
        # Verify the request
        graph_connector.make_request.assert_called_once_with(
            "GET", 
            "jira/issues", 
            params={"project": "PROJ", "status": "In Progress", "assignee": "John Doe"}
        )
    
    def test_create_jira_issue(self, graph_connector):
        """Test creating a Jira issue"""
        # Mock the make_request method
        mock_response = {
            "id": "PROJ-123",
            "title": "Test issue",
            "status": "To Do"
        }
        graph_connector.make_request = MagicMock(return_value=mock_response)
        
        # Call the create_jira_issue method
        issue_data = {
            "title": "Test issue",
            "description": "This is a test issue",
            "project": "PROJ"
        }
        result = graph_connector.create_jira_issue(issue_data)
        
        # Verify the result
        assert result == mock_response
        
        # Verify the request
        graph_connector.make_request.assert_called_once_with(
            "POST", 
            "jira/issues", 
            data=issue_data
        )
    
    def test_get_emails(self, graph_connector):
        """Test getting emails"""
        # Mock the make_request method
        mock_response = {
            "value": [
                {
                    "id": "email-1",
                    "subject": "Test email",
                    "from": {"emailAddress": {"name": "John Doe", "address": "john.doe@example.com"}}
                }
            ]
        }
        graph_connector.make_request = MagicMock(return_value=mock_response)
        
        # Call the get_emails method
        emails = graph_connector.get_emails("inbox", 5)
        
        # Verify the result
        assert emails == mock_response["value"]
        
        # Verify the request
        graph_connector.make_request.assert_called_once_with(
            "GET", 
            "me/mailFolders/inbox/messages", 
            params={"$top": 5, "$orderby": "receivedDateTime DESC"}
        )
    
    def test_send_email(self, graph_connector):
        """Test sending an email"""
        # Mock the make_request method
        mock_response = {}
        graph_connector.make_request = MagicMock(return_value=mock_response)
        
        # Call the send_email method
        email_data = {
            "subject": "Test email",
            "body": {"content": "This is a test email", "contentType": "html"},
            "toRecipients": [{"emailAddress": {"address": "recipient@example.com"}}]
        }
        result = graph_connector.send_email(email_data)
        
        # Verify the result
        assert result == mock_response
        
        # Verify the request
        graph_connector.make_request.assert_called_once_with(
            "POST", 
            "me/sendMail", 
            data={"message": email_data}
        )
    
    def test_get_sharepoint_sites(self, graph_connector):
        """Test getting SharePoint sites"""
        # Mock the make_request method
        mock_response = {
            "value": [
                {
                    "id": "site-1",
                    "displayName": "CTO Twin Project",
                    "webUrl": "https://contoso.sharepoint.com/sites/cto-twin"
                }
            ]
        }
        graph_connector.make_request = MagicMock(return_value=mock_response)
        
        # Call the get_sharepoint_sites method
        sites = graph_connector.get_sharepoint_sites()
        
        # Verify the result
        assert sites == mock_response["value"]
        
        # Verify the request
        graph_connector.make_request.assert_called_once_with("GET", "sites")
    
    def test_get_drive_items(self, graph_connector):
        """Test getting drive items"""
        # Mock the make_request method
        mock_response = {
            "value": [
                {
                    "id": "item-1",
                    "name": "Document.docx",
                    "webUrl": "https://contoso.sharepoint.com/sites/cto-twin/Shared%20Documents/Document.docx"
                }
            ]
        }
        graph_connector.make_request = MagicMock(return_value=mock_response)
        
        # Call the get_drive_items method
        items = graph_connector.get_drive_items("drive-1", "Documents")
        
        # Verify the result
        assert items == mock_response["value"]
        
        # Verify the request
        graph_connector.make_request.assert_called_once_with(
            "GET", 
            "drives/drive-1/root:/Documents:/children"
        )
    
    def test_get_loop_workbooks(self, graph_connector):
        """Test getting Loop workbooks"""
        # Mock the make_request method
        mock_response = {
            "value": [
                {
                    "id": "workbook-1",
                    "name": "Project Planning",
                    "webUrl": "https://contoso.loop.microsoft.com/workbooks/project-planning"
                }
            ]
        }
        graph_connector.make_request = MagicMock(return_value=mock_response)
        
        # Call the get_loop_workbooks method
        workbooks = graph_connector.get_loop_workbooks()
        
        # Verify the result
        assert workbooks == mock_response["value"]
        
        # Verify the request
        graph_connector.make_request.assert_called_once_with("GET", "me/loop/workbooks")
    
    def test_get_checkvist_tasks(self, graph_connector):
        """Test getting Checkvist tasks"""
        # Mock the make_request method
        mock_response = {
            "value": [
                {
                    "id": "task-1",
                    "title": "Complete API documentation",
                    "status": "in_progress"
                }
            ]
        }
        graph_connector.make_request = MagicMock(return_value=mock_response)
        
        # Call the get_checkvist_tasks method
        tasks = graph_connector.get_checkvist_tasks("list-1")
        
        # Verify the result
        assert tasks == mock_response["value"]
        
        # Verify the request
        graph_connector.make_request.assert_called_once_with("GET", "me/checkvist/lists/list-1/tasks")
