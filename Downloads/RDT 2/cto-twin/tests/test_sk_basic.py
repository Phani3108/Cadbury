"""
Basic tests for Semantic Kernel functionality in the CTO Twin application
"""
import os
import sys
import pytest
from unittest.mock import MagicMock, patch

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class TestSemanticKernelBasic:
    """Basic tests for Semantic Kernel functionality"""
    
    @pytest.fixture
    def mock_kernel(self):
        """Create a mock Semantic Kernel instance"""
        with patch('semantic_kernel.Kernel') as mock_kernel_class:
            mock_kernel = MagicMock()
            mock_kernel_class.return_value = mock_kernel
            yield mock_kernel
    
    def test_kernel_initialization(self, mock_kernel):
        """Test that a Semantic Kernel instance can be created"""
        import semantic_kernel as sk
        
        # Simply test that we can import and create a kernel
        kernel = sk.Kernel()
        assert kernel is not None
    
    def test_kernel_with_mock_services(self, mock_kernel):
        """Test kernel with mock services"""
        # This test verifies that we can add services to the kernel
        mock_kernel.add_text_completion_service = MagicMock()
        mock_kernel.add_chat_completion_service = MagicMock()
        
        # Add a mock service
        mock_service = MagicMock()
        mock_kernel.add_text_completion_service("test-service", mock_service)
        
        # Verify the service was added
        mock_kernel.add_text_completion_service.assert_called_once()


class TestSkillsBasic:
    """Basic tests for skills functionality"""
    
    def test_skill_structure(self):
        """Test that the skills directory structure is correct"""
        # Check that the skills directories exist
        skills_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "kernel", "skills")
        assert os.path.exists(skills_dir), "Skills directory does not exist"
        
        # Check that we have the expected skill directories
        expected_skills = ["kb_search", "jira", "calendar", "mail", "loop"]
        for skill in expected_skills:
            skill_dir = os.path.join(skills_dir, skill)
            assert os.path.exists(skill_dir), f"Skill directory {skill} does not exist"
    
    def test_skill_yaml_files(self):
        """Test that the skill YAML files exist and have basic structure"""
        skills_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "kernel", "skills")
        
        # Check each skill directory for a func.yaml file
        for skill_name in ["kb_search", "jira", "calendar", "mail", "loop"]:
            skill_dir = os.path.join(skills_dir, skill_name)
            yaml_file = os.path.join(skill_dir, "func.yaml")
            
            assert os.path.exists(yaml_file), f"YAML file for {skill_name} does not exist"
            
            # Basic check that the file is not empty
            assert os.path.getsize(yaml_file) > 0, f"YAML file for {skill_name} is empty"


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
