import pytest
import asyncio
import os
import sys
from unittest.mock import AsyncMock, patch

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from skills.jira import create, status, status_search
from skills._mock_mode import calendar_find_free_slot, jira_create, jira_status, jira_status_search

class TestJiraSkills:
    """Test Jira skills functionality."""
    
    @pytest.mark.asyncio
    async def test_jira_create_mock(self, monkeypatch):
        """Test Jira create with mocked HTTP client."""
        # Mock httpx.AsyncClient.post
        async def fake_post(*args, **kwargs):
            class MockResponse:
                status_code = 201
                async def json(self):
                    return {"key": "DEV-1"}
                def raise_for_status(self):
                    pass
            return MockResponse()
        
        with patch("skills.jira.httpx.AsyncClient.post", fake_post):
            key = await create("Test ticket", "Test description")
            assert key == "DEV-1"
    
    @pytest.mark.asyncio
    async def test_jira_status_mock(self, monkeypatch):
        """Test Jira status with mocked HTTP client."""
        async def fake_get(*args, **kwargs):
            class MockResponse:
                status_code = 200
                async def json(self):
                    return {
                        "key": "DEV-1",
                        "fields": {
                            "summary": "Test ticket",
                            "status": {"name": "In Progress"},
                            "assignee": {"displayName": "John Doe"}
                        }
                    }
                def raise_for_status(self):
                    pass
            return MockResponse()
        
        with patch("skills.jira.httpx.AsyncClient.get", fake_get):
            result = await status("DEV-1")
            assert result["key"] == "DEV-1"
            assert result["fields"]["summary"] == "Test ticket"
    
    @pytest.mark.asyncio
    async def test_jira_status_search_mock(self, monkeypatch):
        """Test Jira status search with mocked HTTP client."""
        async def fake_get(*args, **kwargs):
            class MockResponse:
                status_code = 200
                async def json(self):
                    return {
                        "issues": [
                            {
                                "key": "DEV-1",
                                "fields": {
                                    "summary": "Optum blocker",
                                    "assignee": {"displayName": "John Doe"},
                                    "priority": {"name": "High"},
                                    "status": {"name": "In Progress"}
                                }
                            }
                        ]
                    }
                def raise_for_status(self):
                    pass
            return MockResponse()
        
        with patch("skills.jira.httpx.AsyncClient.get", fake_get):
            results = await status_search("Optum")
            assert len(results) == 1
            assert results[0]["id"] == "DEV-1"
            assert results[0]["summary"] == "Optum blocker"

class TestMockSkills:
    """Test mock skills functionality."""
    
    @pytest.mark.asyncio
    async def test_calendar_find_free_slot_mock(self):
        """Test calendar mock function."""
        slots = await calendar_find_free_slot()
        assert len(slots) == 2
        assert all("start" in slot and "end" in slot for slot in slots)
    
    @pytest.mark.asyncio
    async def test_jira_create_mock(self):
        """Test Jira create mock function."""
        ticket = await jira_create("Test", "Description")
        assert ticket == "MOCK-123"
    
    @pytest.mark.asyncio
    async def test_jira_status_mock(self):
        """Test Jira status mock function."""
        result = await jira_status("MOCK-123")
        assert result["key"] == "MOCK-123"
        assert result["fields"]["status"]["name"] == "In Progress"
    
    @pytest.mark.asyncio
    async def test_jira_status_search_mock(self):
        """Test Jira status search mock function."""
        results = await jira_status_search("Optum")
        assert len(results) == 2
        assert all("id" in result for result in results)
        assert any("Optum" in result["summary"] for result in results)

class TestSkillsIntegration:
    """Test skills integration with environment."""
    
    @pytest.mark.asyncio
    async def test_mock_mode_detection(self):
        """Test that mock mode is properly detected."""
        # Should be True in development
        assert os.getenv("MODE") == "dev" or os.getenv("MODE") is None

        # Test mock functions return expected data
        slots = await calendar_find_free_slot()
        assert isinstance(slots, list)
        assert len(slots) > 0 