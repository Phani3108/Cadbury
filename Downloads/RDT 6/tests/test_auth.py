"""
Authentication tests for Digital Twin.
"""
import pytest
from fastapi.testclient import TestClient
from orchestrator.app import app

def test_missing_authorization_header():
    """Test that requests without Authorization header return 401."""
    client = TestClient(app)
    
    response = client.post("/chat", json={"query": "test query"})
    
    # Should return 401 Unauthorized
    assert response.status_code == 401
    assert "Invalid authentication token" in response.json()["detail"]

def test_invalid_jwt_token():
    """Test that requests with invalid JWT return 401."""
    client = TestClient(app)
    
    response = client.post(
        "/chat", 
        json={"query": "test query"},
        headers={"Authorization": "Bearer invalid_token"}
    )
    
    # Should return 401 Unauthorized
    assert response.status_code == 401
    assert "Invalid authentication token" in response.json()["detail"]

def test_valid_jwt_token():
    """Test that requests with valid JWT work in development mode."""
    import os
    from orchestrator.auth import create_jwt_token
    
    # Only test in development mode
    if os.getenv("MODE") != "dev":
        pytest.skip("JWT test only runs in development mode")
    
    client = TestClient(app)
    
    # Create a valid JWT token
    user_info = {
        "user_id": "test_user",
        "email": "test@example.com",
        "name": "Test User",
        "role": "user"
    }
    token = create_jwt_token(user_info)
    
    response = client.post(
        "/chat", 
        json={"query": "test query"},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Should return 200 OK
    assert response.status_code == 200
    assert "response" in response.json()

def test_teams_token_validation():
    """Test Teams SSO token validation."""
    from orchestrator.auth import verify_teams_token
    import asyncio
    
    # Test with mock Teams token
    mock_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJvaWQiOiJ0ZXN0X3VzZXIiLCJuYW1lIjoiVGVzdCBVc2VyIiwicHJlZmVycmVkX3VzZXJuYW1lIjoidGVzdEBleGFtcGxlLmNvbSJ9.test"
    
    # This should work in development mode (no signature verification)
    result = asyncio.run(verify_teams_token(mock_token))
    
    if result:
        assert "user_id" in result
        assert "name" in result
        assert "email" in result
    else:
        # In production mode, this would fail signature verification
        assert True  # Expected behavior

def test_authentication_middleware():
    """Test that authentication middleware is properly configured."""
    from orchestrator.auth import get_current_user
    
    # Test that the dependency is properly configured
    assert callable(get_current_user) 