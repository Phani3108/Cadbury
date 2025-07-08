"""
Tests for Semantic Kernel components in the CTO Twin application
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

# Import Semantic Kernel 1.34.0 specific modules
import semantic_kernel as sk
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion, AzureTextEmbedding
from semantic_kernel.connectors.memory.azure_ai_search import AzureAISearchMemoryStore


class TestReActPlanner:
    """Tests for the ReActPlanner class"""
    
    @pytest.fixture
    def mock_kernel(self):
        """Create a mock Semantic Kernel instance"""
        with patch('semantic_kernel.Kernel') as mock_kernel_class:
            mock_kernel = MagicMock()
            mock_kernel_class.return_value = mock_kernel
            yield mock_kernel
    
    @pytest.fixture
    def planner(self, mock_kernel):
        """Create a ReActPlanner instance with a mock kernel"""
        with patch.dict(os.environ, {
            "AZURE_OPENAI_DEPLOYMENT_NAME": "gpt-4",
            "AZURE_OPENAI_ENDPOINT": "https://mock-endpoint.openai.azure.com/",
            "AZURE_OPENAI_API_KEY": "mock-api-key"
        }):
            # Patch the Kernel class to return our mock
            with patch('semantic_kernel.Kernel', return_value=mock_kernel):
                planner = ReActPlanner()
                return planner
    
    def test_initialization(self, planner):
        """Test that the planner initializes correctly"""
        assert planner.max_iterations == 10
        assert isinstance(planner.history, list)
        assert len(planner.history) == 0
    
    def test_generate_plan(self, planner, mock_kernel):
        """Test plan generation"""
        # Mock the kernel's planning function
        mock_plan_result = MagicMock()
        mock_plan_result.result = json.dumps({
            "thinking": "Analyzing the request",
            "plan": ["Step 1: Check Jira for existing tickets", "Step 2: Create a new ticket"],
            "actions": ["Use JiraSkill to search for tickets", "Use JiraSkill to create a ticket"]
        })
        mock_kernel.invoke_semantic_function.return_value = mock_plan_result
        
        # Call the generate_plan method
        result = planner.generate_plan("Create a new Jira ticket for the bug in the login page")
        
        # Verify the result
        assert "thinking" in result
        assert "plan" in result
        assert isinstance(result["plan"], list)
        assert len(result["plan"]) == 2
        assert "actions" in result
        assert isinstance(result["actions"], list)
        assert len(result["actions"]) == 2
    
    def test_execute_plan(self, planner):
        """Test plan execution"""
        # Mock the plan
        plan = {
            "thinking": "Analyzing the request",
            "plan": ["Step 1: Check Jira for existing tickets", "Step 2: Create a new ticket"],
            "actions": ["Use JiraSkill to search for tickets", "Use JiraSkill to create a ticket"]
        }
        
        # Mock the execute_step method
        planner.execute_step = MagicMock()
        planner.execute_step.side_effect = [
            {"status": "success", "result": "Found 0 tickets matching the criteria"},
            {"status": "success", "result": "Created ticket PROJ-123"}
        ]
        
        # Call the execute_plan method
        result = planner.execute_plan(plan)
        
        # Verify the result
        assert result["status"] == "success"
        assert len(result["steps"]) == 2
        assert result["steps"][0]["status"] == "success"
        assert result["steps"][1]["status"] == "success"
        assert "Created ticket PROJ-123" in result["steps"][1]["result"]
    
    def test_reflect_on_execution(self, planner, mock_kernel):
        """Test reflection on execution"""
        # Mock the execution result
        execution_result = {
            "status": "success",
            "steps": [
                {"step": "Step 1: Check Jira for existing tickets", "status": "success", "result": "Found 0 tickets matching the criteria"},
                {"step": "Step 2: Create a new ticket", "status": "success", "result": "Created ticket PROJ-123"}
            ]
        }
        
        # Mock the kernel's reflection function
        mock_reflection_result = MagicMock()
        mock_reflection_result.result = json.dumps({
            "reflection": "The plan was executed successfully. A new Jira ticket PROJ-123 was created.",
            "next_steps": ["Inform the user about the new ticket", "Suggest adding more details to the ticket"]
        })
        mock_kernel.invoke_semantic_function.return_value = mock_reflection_result
        
        # Call the reflect_on_execution method
        result = planner.reflect_on_execution(execution_result)
        
        # Verify the result
        assert "reflection" in result
        assert "next_steps" in result
        assert isinstance(result["next_steps"], list)
        assert len(result["next_steps"]) == 2


class TestJiraSkill:
    """Tests for the JiraSkill class"""
    
    @pytest.fixture
    def mock_graph_connector(self):
        """Create a mock Graph connector"""
        return MagicMock()
    
    @pytest.fixture
    def jira_skill(self, mock_graph_connector):
        """Create a JiraSkill instance with a mock Graph connector"""
        return JiraSkill(mock_graph_connector)
    
    def test_initialization(self, jira_skill, mock_graph_connector):
        """Test that the skill initializes correctly"""
        assert jira_skill.graph_connector == mock_graph_connector
    
    def test_get_issues(self, jira_skill):
        """Test getting issues"""
        # Call the get_issues method
        issues = jira_skill.get_issues("PROJ")
        
        # Verify the result
        assert isinstance(issues, list)
        assert len(issues) == 3
        assert issues[0]["key"] == "PROJ-1"
        assert issues[1]["key"] == "PROJ-2"
        assert issues[2]["key"] == "PROJ-3"
    
    def test_create_issue(self, jira_skill):
        """Test creating an issue"""
        # Call the create_issue method
        issue = jira_skill.create_issue(
            project_key="PROJ",
            summary="Test issue",
            description="This is a test issue",
            issue_type="Bug",
            priority="High",
            assignee="John Doe"
        )
        
        # Verify the result
        assert issue["key"] == "PROJ-123"
        assert issue["summary"] == "Test issue"
        assert issue["description"] == "This is a test issue"
        assert issue["issue_type"] == "Bug"
        assert issue["priority"] == "High"
        assert issue["assignee"] == "John Doe"


class TestOutlookSkill:
    """Tests for the OutlookSkill class"""
    
    @pytest.fixture
    def mock_graph_connector(self):
        """Create a mock Graph connector"""
        return MagicMock()
    
    @pytest.fixture
    def outlook_skill(self, mock_graph_connector):
        """Create an OutlookSkill instance with a mock Graph connector"""
        return OutlookSkill(mock_graph_connector)
    
    def test_initialization(self, outlook_skill, mock_graph_connector):
        """Test that the skill initializes correctly"""
        assert outlook_skill.graph_connector == mock_graph_connector
    
    def test_get_emails(self, outlook_skill):
        """Test getting emails"""
        # Call the get_emails method
        emails = outlook_skill.get_emails()
        
        # Verify the result
        assert isinstance(emails, list)
        assert len(emails) == 3
        assert "subject" in emails[0]
        assert "from" in emails[0]
        assert "receivedDateTime" in emails[0]
    
    def test_send_email(self, outlook_skill):
        """Test sending an email"""
        # Call the send_email method
        result = outlook_skill.send_email(
            to_recipients=["recipient@example.com"],
            subject="Test email",
            body="<p>This is a test email</p>",
            cc_recipients=["cc@example.com"],
            importance="high"
        )
        
        # Verify the result
        assert result["subject"] == "Test email"
        assert "recipient@example.com" in result["toRecipients"]
        assert "cc@example.com" in result["ccRecipients"]
        assert result["importance"] == "high"
        assert result["status"] == "sent"


class TestSharePointSkill:
    """Tests for the SharePointSkill class"""
    
    @pytest.fixture
    def mock_graph_connector(self):
        """Create a mock Graph connector"""
        return MagicMock()
    
    @pytest.fixture
    def sharepoint_skill(self, mock_graph_connector):
        """Create a SharePointSkill instance with a mock Graph connector"""
        return SharePointSkill(mock_graph_connector)
    
    def test_initialization(self, sharepoint_skill, mock_graph_connector):
        """Test that the skill initializes correctly"""
        assert sharepoint_skill.graph_connector == mock_graph_connector
    
    def test_get_sites(self, sharepoint_skill):
        """Test getting SharePoint sites"""
        # Call the get_sites method
        sites = sharepoint_skill.get_sites()
        
        # Verify the result
        assert isinstance(sites, list)
        assert len(sites) == 3
        assert sites[0]["displayName"] == "CTO Twin Project"
        assert sites[1]["displayName"] == "Engineering Team"
        assert sites[2]["displayName"] == "Product Documentation"
    
    def test_get_documents(self, sharepoint_skill):
        """Test getting documents"""
        # Call the get_documents method
        documents = sharepoint_skill.get_documents("site-id-1")
        
        # Verify the result
        assert isinstance(documents, list)
        assert len(documents) == 3
        assert documents[0]["name"] == "Architecture Overview.docx"
        assert documents[1]["name"] == "Project Plan.xlsx"
        assert documents[2]["name"] == "Technical Specifications.pdf"


class TestSearchSkill:
    """Tests for the SearchSkill class"""
    
    @pytest.fixture
    def mock_memory_manager(self):
        """Create a mock memory manager"""
        return MagicMock()
    
    @pytest.fixture
    def search_skill(self, mock_memory_manager):
        """Create a SearchSkill instance with a mock memory manager"""
        return SearchSkill(mock_memory_manager)
    
    def test_initialization(self, search_skill, mock_memory_manager):
        """Test that the skill initializes correctly"""
        assert search_skill.memory_manager == mock_memory_manager
    
    def test_semantic_search(self, search_skill):
        """Test semantic search"""
        # Call the semantic_search method
        results = search_skill.semantic_search("semantic kernel integration")
        
        # Verify the result
        assert isinstance(results, list)
        assert len(results) == 5
        assert results[0]["score"] > 0.9  # High relevance score
        assert "title" in results[0]
        assert "content" in results[0]
        assert "source" in results[0]
    
    def test_keyword_search(self, search_skill):
        """Test keyword search"""
        # Call the keyword_search method
        results = search_skill.keyword_search("semantic kernel integration")
        
        # Verify the result
        assert isinstance(results, list)
        assert len(results) == 3
        assert results[0]["score"] > 0.9  # High relevance score
        assert "title" in results[0]
        assert "content" in results[0]
        assert "source" in results[0]
    
    def test_hybrid_search(self, search_skill):
        """Test hybrid search"""
        # Mock the semantic_search and keyword_search methods
        search_skill.semantic_search = MagicMock(return_value=[
            {"id": "result-1", "title": "Result 1", "score": 0.95},
            {"id": "result-2", "title": "Result 2", "score": 0.90}
        ])
        search_skill.keyword_search = MagicMock(return_value=[
            {"id": "result-3", "title": "Result 3", "score": 0.92},
            {"id": "result-1", "title": "Result 1", "score": 0.88}  # Duplicate ID
        ])
        
        # Call the hybrid_search method
        results = search_skill.hybrid_search("test query")
        
        # Verify the result
        assert isinstance(results, list)
        assert len(results) == 3  # Deduplicated
        assert results[0]["id"] == "result-1"
        assert results[1]["id"] == "result-2"
        assert results[2]["id"] == "result-3"
