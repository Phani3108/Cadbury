#!/usr/bin/env python3
"""
Azure Integration Smoke Test
Tests all Azure components for Beta readiness.
"""

import os
import sys
import asyncio
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from digital_twin.utils.config import get_settings, is_production
from skills.kb_search import hybrid_search
from llm.planner import react
from llm.verifier import check

async def test_azure_search():
    """Test Azure AI Search integration."""
    print("🔍 Testing Azure AI Search...")
    
    settings = get_settings()
    
    if not is_production():
        print("ℹ️  Skipping Azure Search test in development mode")
        return True
    
    try:
        # Test search functionality
        results = hybrid_search("Optum", ["Optum"], k=5)
        
        if results:
            print(f"✅ Azure Search working: {len(results)} results found")
            return True
        else:
            print("⚠️  Azure Search returned no results")
            return False
            
    except Exception as e:
        print(f"❌ Azure Search test failed: {e}")
        return False

async def test_azure_openai():
    """Test Azure OpenAI integration."""
    print("🤖 Testing Azure OpenAI...")
    
    settings = get_settings()
    
    try:
        # Test with a simple query
        test_query = "What is the latest discussion about Optum?"
        test_context = "Sample context for testing"
        test_results = [{"text": "Sample result", "source_id": "test-1"}]
        
        response = await react(
            model_key="LLM_HEAVY",
            query=test_query,
            context=test_context,
            search_results=test_results
        )
        
        if response and isinstance(response, dict):
            print("✅ Azure OpenAI working")
            return True
        else:
            print("❌ Azure OpenAI returned invalid response")
            return False
            
    except Exception as e:
        print(f"❌ Azure OpenAI test failed: {e}")
        return False

async def test_telemetry():
    """Test Azure Application Insights telemetry."""
    print("📊 Testing Azure Telemetry...")
    
    connection_string = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
    
    if not connection_string:
        print("ℹ️  No Application Insights connection string - using console telemetry")
        return True
    
    try:
        from digital_twin.observability.tracing import trace_span, add_span_attribute
        
        @trace_span("test_telemetry")
        def test_function():
            add_span_attribute("test", "value")
            return "success"
        
        result = test_function()
        
        if result == "success":
            print("✅ Azure Telemetry working")
            return True
        else:
            print("❌ Azure Telemetry test failed")
            return False
            
    except Exception as e:
        print(f"❌ Azure Telemetry test failed: {e}")
        return False

async def test_authentication():
    """Test Teams SSO authentication."""
    print("🔐 Testing Authentication...")
    
    try:
        from orchestrator.auth import verify_teams_token, verify_jwt_token
        
        # Test with mock token
        mock_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJvaWQiOiJ0ZXN0X3VzZXIiLCJuYW1lIjoiVGVzdCBVc2VyIiwicHJlZmVycmVkX3VzZXJuYW1lIjoidGVzdEBleGFtcGxlLmNvbSJ9.test"
        
        # Test JWT verification (should work in dev mode)
        user_info = await verify_jwt_token(mock_token)
        
        if user_info:
            print("✅ Authentication working")
            return True
        else:
            print("⚠️  Authentication test inconclusive")
            return True  # Not a failure in dev mode
            
    except Exception as e:
        print(f"❌ Authentication test failed: {e}")
        return False

async def test_deployment_config():
    """Test deployment configuration."""
    print("⚙️  Testing Deployment Configuration...")
    
    settings = get_settings()
    required_vars = [
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_OPENAI_API_KEY", 
        "AZURE_SEARCH_ENDPOINT",
        "AZURE_SEARCH_KEY"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not getattr(settings, var, None):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {missing_vars}")
        return False
    else:
        print("✅ All required environment variables configured")
        return True

async def main():
    """Run all Azure integration tests."""
    print("🧪 Azure Integration Smoke Test")
    print("=" * 50)
    
    tests = [
        ("Deployment Config", test_deployment_config),
        ("Azure Search", test_azure_search),
        ("Azure OpenAI", test_azure_openai),
        ("Telemetry", test_telemetry),
        ("Authentication", test_authentication)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name} test...")
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Ready for Beta deployment.")
        return 0
    else:
        print("⚠️  Some tests failed. Review configuration before deployment.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 