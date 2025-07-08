"""
Integration tests for Semantic Kernel components in the CTO Twin application
"""
import os
import sys
import pytest
from unittest.mock import MagicMock, patch
import json

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the components to test
from kernel.planners.react_planner import ReActPlanner
from kernel.skills.jira_skill import JiraSkill
from kernel.skills.outlook_skill import OutlookSkill
from kernel.skills.sharepoint_skill import SharePointSkill
from kernel.skills.search_skill import SearchSkill
from tools.graph_connector import GraphConnector


class TestSemanticKernelIntegration:
    """Integration tests for Semantic Kernel components"""
    
    @pytest.fixture
    def mock_env_vars(self):
        """Set up mock environment variables for testing"""
        with patch.dict(os.environ, {
            "AZURE_OPENAI_DEPLOYMENT_NAME": "mock-deployment",
            "AZURE_OPENAI_COMPLETION_DEPLOYMENT": "mock-completion",
            "AZURE_OPENAI_ENDPOINT": "https://mock-endpoint.openai.azure.com/",
            "AZURE_OPENAI_API_KEY": "mock-api-key",
            "GRAPH_CLIENT_ID": "mock-client-id",
            "GRAPH_CLIENT_SECRET": "mock-client-secret",
            "GRAPH_TENANT_ID": "mock-tenant-id"
        }):
            yield
    
    @pytest.fixture
    def react_planner(self, mock_env_vars):
        """Create a ReActPlanner instance with mocked dependencies"""
        with patch('semantic_kernel.kernel.Kernel') as mock_kernel:
            # Mock the kernel and its methods
            mock_kernel_instance = MagicMock()
            mock_kernel.return_value = mock_kernel_instance
            
            # Mock the service registration
            mock_kernel_instance.add_service = MagicMock()
            mock_kernel_instance.add_chat_service = MagicMock()
            mock_kernel_instance.add_text_completion_service = MagicMock()
            
            # Mock the function registration
            mock_kernel_instance.create_function = MagicMock()
            mock_kernel_instance.register_function = MagicMock()
            
            # Create the planner
            planner = ReActPlanner()
            
            return planner
    
    @pytest.fixture
    def graph_connector(self, mock_env_vars):
        """Create a GraphConnector instance"""
        return GraphConnector()
    
    @pytest.fixture
    def jira_skill(self, graph_connector):
        """Create a JiraSkill instance"""
        return JiraSkill(graph_connector)
    
    @pytest.fixture
    def outlook_skill(self, graph_connector):
        """Create an OutlookSkill instance"""
        return OutlookSkill(graph_connector)
    
    @pytest.fixture
    def sharepoint_skill(self, graph_connector):
        """Create a SharePointSkill instance"""
        return SharePointSkill(graph_connector)
    
    @pytest.fixture
    def search_skill(self):
        """Create a SearchSkill instance"""
        with patch('memory.memory_manager.MemoryManager') as mock_memory_manager:
            # Mock the memory manager
            mock_memory_manager_instance = MagicMock()
            mock_memory_manager.return_value = mock_memory_manager_instance
            
            # Create the skill
            skill = SearchSkill()
            
            return skill
    
    def test_react_planner_initialization(self, react_planner):
        """Test that the ReActPlanner initializes correctly"""
        assert react_planner is not None
        assert react_planner.kernel is not None
        assert hasattr(react_planner, 'register_skill')
        assert hasattr(react_planner, 'plan')
        assert hasattr(react_planner, 'execute')
        assert hasattr(react_planner, 'reflect')
    
    @patch('semantic_kernel.planning.sequential_planner.SequentialPlanner')
    @patch('semantic_kernel.planning.stepwise_planner.StepwisePlanner')
    def test_react_planner_plan_generation(self, mock_stepwise_planner, mock_sequential_planner, react_planner):
        """Test plan generation with the ReActPlanner"""
        # Mock the planners
        mock_stepwise_planner_instance = MagicMock()
        mock_stepwise_planner.return_value = mock_stepwise_planner_instance
        mock_sequential_planner_instance = MagicMock()
        mock_sequential_planner.return_value = mock_sequential_planner_instance
        
        # Mock the plan result
        mock_plan = MagicMock()
        mock_plan.result = "Mock plan result"
        mock_stepwise_planner_instance.create_plan.return_value = mock_plan
        
        # Generate a plan
        goal = "Create a summary of recent Jira issues"
        plan = react_planner.plan(goal)
        
        # Verify the result
        assert plan is not None
        assert plan.result == "Mock plan result"
        mock_stepwise_planner_instance.create_plan.assert_called_once()
    
    @patch('semantic_kernel.planning.sequential_planner.SequentialPlanner')
    @patch('semantic_kernel.planning.stepwise_planner.StepwisePlanner')
    def test_react_planner_plan_execution(self, mock_stepwise_planner, mock_sequential_planner, react_planner):
        """Test plan execution with the ReActPlanner"""
        # Mock the planners
        mock_stepwise_planner_instance = MagicMock()
        mock_stepwise_planner.return_value = mock_stepwise_planner_instance
        mock_sequential_planner_instance = MagicMock()
        mock_sequential_planner.return_value = mock_sequential_planner_instance
        
        # Mock the plan result
        mock_plan = MagicMock()
        mock_plan.result = "Mock plan result"
        mock_plan.invoke.return_value = "Mock execution result"
        mock_stepwise_planner_instance.create_plan.return_value = mock_plan
        
        # Generate and execute a plan
        goal = "Create a summary of recent Jira issues"
        result = react_planner.execute(goal)
        
        # Verify the result
        assert result is not None
        assert "Mock execution result" in result
        mock_plan.invoke.assert_called_once()
    
    def test_react_planner_skill_registration(self, react_planner, jira_skill):
        """Test skill registration with the ReActPlanner"""
        # Register the skill
        react_planner.register_skill(jira_skill, "jira")
        
        # Verify the skill was registered
        react_planner.kernel.import_skill.assert_called_once()
    
    def test_react_planner_reflection(self, react_planner):
        """Test the reflection capability of the ReActPlanner"""
        # Mock the kernel's text completion
        mock_function = MagicMock()
        mock_function.invoke.return_value = "Mock reflection result"
        react_planner.kernel.create_function_from_prompt.return_value = mock_function
        
        # Generate a reflection
        plan_result = "Mock plan execution result"
        reflection = react_planner.reflect(plan_result)
        
        # Verify the result
        assert reflection is not None
        assert "Mock reflection result" in reflection
        mock_function.invoke.assert_called_once()
    
    def test_jira_skill_get_issues(self, jira_skill, graph_connector):
        """Test the JiraSkill's get_issues method"""
        # Mock the GraphConnector's get_jira_issues method
        mock_issues = [
            {"id": "PROJ-123", "title": "Test issue", "status": "In Progress"}
        ]
        graph_connector.get_jira_issues = MagicMock(return_value=mock_issues)
        
        # Call the method
        result = jira_skill.get_issues("PROJ", "In Progress", "John Doe")
        
        # Verify the result
        assert result is not None
        assert isinstance(result, str)
        assert "PROJ-123" in result
        assert "Test issue" in result
        graph_connector.get_jira_issues.assert_called_once_with("PROJ", "In Progress", "John Doe")
    
    def test_jira_skill_create_issue(self, jira_skill, graph_connector):
        """Test the JiraSkill's create_issue method"""
        # Mock the GraphConnector's create_jira_issue method
        mock_result = {"id": "PROJ-123", "title": "Test issue", "status": "To Do"}
        graph_connector.create_jira_issue = MagicMock(return_value=mock_result)
        
        # Call the method
        issue_data = {
            "title": "Test issue",
            "description": "This is a test issue",
            "project": "PROJ"
        }
        result = jira_skill.create_issue(json.dumps(issue_data))
        
        # Verify the result
        assert result is not None
        assert isinstance(result, str)
        assert "PROJ-123" in result
        graph_connector.create_jira_issue.assert_called_once()
    
    def test_outlook_skill_get_emails(self, outlook_skill, graph_connector):
        """Test the OutlookSkill's get_emails method"""
        # Mock the GraphConnector's get_emails method
        mock_emails = [
            {
                "id": "email-1",
                "subject": "Test email",
                "from": {"emailAddress": {"name": "John Doe", "address": "john.doe@example.com"}}
            }
        ]
        graph_connector.get_emails = MagicMock(return_value=mock_emails)
        
        # Call the method
        result = outlook_skill.get_emails("inbox", 5)
        
        # Verify the result
        assert result is not None
        assert isinstance(result, str)
        assert "Test email" in result
        assert "John Doe" in result
        graph_connector.get_emails.assert_called_once_with("inbox", 5)
    
    def test_outlook_skill_send_email(self, outlook_skill, graph_connector):
        """Test the OutlookSkill's send_email method"""
        # Mock the GraphConnector's send_email method
        mock_result = {"id": "email-1", "status": "sent"}
        graph_connector.send_email = MagicMock(return_value=mock_result)
        
        # Call the method
        email_data = {
            "subject": "Test email",
            "body": "This is a test email",
            "to": ["recipient@example.com"]
        }
        result = outlook_skill.send_email(json.dumps(email_data))
        
        # Verify the result
        assert result is not None
        assert isinstance(result, str)
        assert "sent" in result.lower()
        graph_connector.send_email.assert_called_once()
    
    def test_sharepoint_skill_get_sites(self, sharepoint_skill, graph_connector):
        """Test the SharePointSkill's get_sites method"""
        # Mock the GraphConnector's get_sharepoint_sites method
        mock_sites = [
            {
                "id": "site-1",
                "displayName": "CTO Twin Project",
                "webUrl": "https://contoso.sharepoint.com/sites/cto-twin"
            }
        ]
        graph_connector.get_sharepoint_sites = MagicMock(return_value=mock_sites)
        
        # Call the method
        result = sharepoint_skill.get_sites()
        
        # Verify the result
        assert result is not None
        assert isinstance(result, str)
        assert "CTO Twin Project" in result
        graph_connector.get_sharepoint_sites.assert_called_once()
    
    def test_sharepoint_skill_get_documents(self, sharepoint_skill, graph_connector):
        """Test the SharePointSkill's get_documents method"""
        # Mock the GraphConnector's get_drive_items method
        mock_items = [
            {
                "id": "item-1",
                "name": "Document.docx",
                "webUrl": "https://contoso.sharepoint.com/sites/cto-twin/Shared%20Documents/Document.docx"
            }
        ]
        graph_connector.get_drive_items = MagicMock(return_value=mock_items)
        
        # Call the method
        result = sharepoint_skill.get_documents("drive-1", "Documents")
        
        # Verify the result
        assert result is not None
        assert isinstance(result, str)
        assert "Document.docx" in result
        graph_connector.get_drive_items.assert_called_once_with("drive-1", "Documents")
    
    def test_search_skill_semantic_search(self, search_skill):
        """Test the SearchSkill's semantic_search method"""
        # Mock the memory manager's search method
        mock_results = [
            {"id": "doc-1", "content": "This is a test document", "score": 0.95},
            {"id": "doc-2", "content": "Another test document", "score": 0.85}
        ]
        search_skill.memory_manager.semantic_search = MagicMock(return_value=mock_results)
        
        # Call the method
        result = search_skill.semantic_search("test query", 5)
        
        # Verify the result
        assert result is not None
        assert isinstance(result, str)
        assert "test document" in result
        search_skill.memory_manager.semantic_search.assert_called_once_with("test query", 5)
    
    def test_search_skill_keyword_search(self, search_skill):
        """Test the SearchSkill's keyword_search method"""
        # Mock the memory manager's search method
        mock_results = [
            {"id": "doc-1", "content": "This is a test document", "score": 0.95},
            {"id": "doc-2", "content": "Another test document", "score": 0.85}
        ]
        search_skill.memory_manager.keyword_search = MagicMock(return_value=mock_results)
        
        # Call the method
        result = search_skill.keyword_search("test", 5)
        
        # Verify the result
        assert result is not None
        assert isinstance(result, str)
        assert "test document" in result
        search_skill.memory_manager.keyword_search.assert_called_once_with("test", 5)
    
    def test_search_skill_hybrid_search(self, search_skill):
        """Test the SearchSkill's hybrid_search method"""
        # Mock the memory manager's search method
        mock_results = [
            {"id": "doc-1", "content": "This is a test document", "score": 0.95},
            {"id": "doc-2", "content": "Another test document", "score": 0.85}
        ]
        search_skill.memory_manager.hybrid_search = MagicMock(return_value=mock_results)
        
        # Call the method
        result = search_skill.hybrid_search("test query", 5)
        
        # Verify the result
        assert result is not None
        assert isinstance(result, str)
        assert "test document" in result
        search_skill.memory_manager.hybrid_search.assert_called_once_with("test query", 5)
