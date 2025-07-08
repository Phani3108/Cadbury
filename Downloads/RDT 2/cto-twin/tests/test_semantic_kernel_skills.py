"""
Tests for Semantic Kernel skills in the CTO Twin application
"""
import os
import sys
import pytest
from unittest.mock import MagicMock, patch
import json
import semantic_kernel as sk

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the components to test
from kernel.semantic_kernel_setup import setup_kernel, register_native_skills, AzureAISearchMemory
from tools.graph_connector import GraphConnector

# Import Semantic Kernel 1.34.0 specific modules
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion, AzureTextEmbedding
from semantic_kernel.connectors.memory.azure_ai_search import AzureAISearchMemoryStore


class TestSemanticKernelSetup:
    """Tests for the Semantic Kernel setup functionality"""
    
    @pytest.fixture
    def mock_env_vars(self):
        """Set up mock environment variables"""
        env_vars = {
            "AZURE_OPENAI_DEPLOYMENT_NAME": "gpt-4o",
            "AZURE_OPENAI_ENDPOINT": "https://mock-endpoint.openai.azure.com/",
            "AZURE_OPENAI_API_KEY": "mock-api-key",
            "AZURE_SEARCH_ENDPOINT": "https://mock-search.search.windows.net",
            "AZURE_SEARCH_KEY": "mock-search-key",
            "AZURE_OPENAI_EMBEDDING_DEPLOYMENT": "text-embedding-ada-002"
        }
        with patch.dict(os.environ, env_vars):
            yield env_vars
    
    @pytest.fixture
    def mock_kernel(self):
        """Create a mock Semantic Kernel instance"""
        with patch('semantic_kernel.Kernel') as mock_kernel_class:
            mock_kernel = MagicMock()
            mock_kernel_class.return_value = mock_kernel
            yield mock_kernel
    
    @pytest.fixture
    def mock_chat_service(self):
        """Create a mock chat service"""
        with patch('semantic_kernel.connectors.ai.open_ai.AzureChatCompletion') as mock_service:
            mock_instance = MagicMock()
            mock_service.return_value = mock_instance
            yield mock_instance
    
    @pytest.fixture
    def mock_memory_store(self):
        """Create a mock memory store"""
        with patch('semantic_kernel.connectors.memory.azure_ai_search.AzureAISearchMemoryStore') as mock_store:
            mock_instance = MagicMock()
            mock_store.return_value = mock_instance
            yield mock_instance
    
    @pytest.fixture
    def mock_embedding_service(self):
        """Create a mock embedding service"""
        with patch('semantic_kernel.connectors.ai.open_ai.AzureTextEmbedding') as mock_service:
            mock_instance = MagicMock()
            mock_service.return_value = mock_instance
            yield mock_instance
    
    def test_setup_kernel(self, mock_env_vars, mock_kernel, mock_chat_service):
        """Test that the kernel is set up correctly"""
        with patch('os.path.exists', return_value=True):
            kernel = setup_kernel()
            assert kernel is not None
            # Verify chat service was added
            mock_kernel.add_text_completion_service.assert_called_once_with("gpt4o", mock_chat_service)
            # Verify skills were imported
            mock_kernel.import_plugins_from_directory.assert_called_once()
            mock_kernel.import_plugins_from_directory.assert_called()
    
    def test_azure_ai_search_memory(self, mock_env_vars, mock_memory_store, mock_embedding_generator):
        """Test that the Azure AI Search memory is initialized correctly"""
        memory = AzureAISearchMemory("test-index")
        assert memory.index_name == "test-index"
        assert memory.endpoint == mock_env_vars["AZURE_SEARCH_ENDPOINT"]
        assert memory.key == mock_env_vars["AZURE_SEARCH_KEY"]
        assert memory.memory_store is not None
        assert memory.embedding_generator is not None
    
    def test_register_native_skills(self, mock_kernel):
        """Test that native skills are registered correctly"""
        with patch('tools.graph_connector.GraphConnector') as mock_graph_connector_class:
            mock_graph_connector = MagicMock()
            mock_graph_connector_class.return_value = mock_graph_connector
            
            with patch('kernel.skills.jira_skill.JiraSkill') as mock_jira_skill_class, \
                 patch('kernel.skills.outlook_skill.OutlookSkill') as mock_outlook_skill_class, \
                 patch('kernel.skills.sharepoint_skill.SharePointSkill') as mock_sharepoint_skill_class, \
                 patch('kernel.skills.search_skill.SearchSkill') as mock_search_skill_class:
                
                mock_jira_skill = MagicMock()
                mock_outlook_skill = MagicMock()
                mock_sharepoint_skill = MagicMock()
                mock_search_skill = MagicMock()
                
                mock_jira_skill_class.return_value = mock_jira_skill
                mock_outlook_skill_class.return_value = mock_outlook_skill
                mock_sharepoint_skill_class.return_value = mock_sharepoint_skill
                mock_search_skill_class.return_value = mock_search_skill
                
                kernel = register_native_skills(mock_kernel)
                
                # Verify skills were imported
                mock_kernel.add_plugin.assert_any_call(mock_jira_skill, "jira")
                mock_kernel.add_plugin.assert_any_call(mock_outlook_skill, "outlook")
                mock_kernel.add_plugin.assert_any_call(mock_sharepoint_skill, "sharepoint")
                mock_kernel.add_plugin.assert_any_call(mock_search_skill, "search")


class TestSemanticSkills:
    """Tests for the Semantic Kernel skills"""
    
    @pytest.fixture
    def mock_kernel(self):
        """Create a mock Semantic Kernel instance"""
        mock_kernel = MagicMock()
        
        # Mock the plugins collection
        mock_kernel.plugins = {}
        mock_kernel.plugins["kb_search"] = MagicMock()
        mock_kernel.plugins["jira"] = MagicMock()
        mock_kernel.plugins["calendar"] = MagicMock()
        mock_kernel.plugins["mail"] = MagicMock()
        mock_kernel.plugins["loop"] = MagicMock()
        
        # Mock function responses
        mock_kernel.plugins["kb_search"].vector_query = MagicMock(return_value="Mock search results")
        mock_kernel.plugins["jira"].create = MagicMock(return_value="JIRA-123")
        mock_kernel.plugins["jira"].get_status = MagicMock(return_value="In Progress")
        mock_kernel.plugins["calendar"].find_slot = MagicMock(return_value="2025-07-08 14:00-15:00")
        mock_kernel.plugins["calendar"].send_invite = MagicMock(return_value="Meeting invitation sent")
        mock_kernel.plugins["mail"].send_to_ea = MagicMock(return_value="Email sent to Rukmani")
        mock_kernel.plugins["loop"].append_page = MagicMock(return_value="Content appended to Loop page")
        
        return mock_kernel
    
    def test_kb_search_skill(self, mock_kernel):
        """Test the kb_search skill"""
        result = mock_kernel.plugins["kb_search"].vector_query("test query", k=3)
        assert result == "Mock search results"
        mock_kernel.plugins["kb_search"].vector_query.assert_called_once_with("test query", k=3)
    
    def test_jira_skill(self, mock_kernel):
        """Test the jira skill"""
        # Test create
        create_result = mock_kernel.plugins["jira"].create(
            title="Test ticket",
            description="Test description",
            project="TEST",
            type="Task",
            priority="Medium"
        )
        assert create_result == "JIRA-123"
        mock_kernel.plugins["jira"].create.assert_called_once()
        
        # Test get_status
        status_result = mock_kernel.plugins["jira"].get_status("JIRA-123")
        assert status_result == "In Progress"
        mock_kernel.plugins["jira"].get_status.assert_called_once_with("JIRA-123")
    
    def test_calendar_skill(self, mock_kernel):
        """Test the calendar skill"""
        # Test find_slot
        slot_result = mock_kernel.plugins["calendar"].find_slot(
            duration=60,
            participants="user1@example.com,user2@example.com",
            start_date="2025-07-08"
        )
        assert slot_result == "2025-07-08 14:00-15:00"
        mock_kernel.plugins["calendar"].find_slot.assert_called_once()
        
        # Test send_invite
        invite_result = mock_kernel.plugins["calendar"].send_invite(
            title="Test Meeting",
            start_time="2025-07-08 14:00",
            end_time="2025-07-08 15:00",
            participants="user1@example.com,user2@example.com"
        )
        assert invite_result == "Meeting invitation sent"
        mock_kernel.plugins["calendar"].send_invite.assert_called_once()
    
    def test_mail_skill(self, mock_kernel):
        """Test the mail skill"""
        result = mock_kernel.plugins["mail"].send_to_ea(
            subject="Test Subject",
            message="Test message content"
        )
        assert result == "Email sent to Rukmani"
        mock_kernel.plugins["mail"].send_to_ea.assert_called_once()
    
    def test_loop_skill(self, mock_kernel):
        """Test the loop skill"""
        result = mock_kernel.plugins["loop"].append_page(
            page_id="page123",
            content="Test action items"
        )
        assert result == "Content appended to Loop page"
        mock_kernel.plugins["loop"].append_page.assert_called_once()


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
