#!/usr/bin/env python3
"""
Test script for local development setup.
"""
import os
import sys
import asyncio
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from digital_twin.utils.config import is_development, is_production
from skills._mock_mode import MOCK, calendar_find_free_slot, jira_create

def test_config():
    """Test configuration loading."""
    print("🔧 Testing Configuration...")
    print(f"Mode: {os.getenv('MODE', 'development')}")
    print(f"Development: {is_development()}")
    print(f"Production: {is_production()}")
    print(f"Mock Mode: {MOCK}")
    print("✅ Configuration test passed")
    print()

async def test_mock_skills():
    """Test mock skills functionality."""
    print("🎭 Testing Mock Skills...")
    
    # Test calendar
    slots = await calendar_find_free_slot()
    print(f"Calendar slots: {len(slots)} found")
    for slot in slots:
        print(f"  - {slot['start']} to {slot['end']}")
    
    # Test Jira
    ticket = await jira_create("Test ticket", "Test description")
    print(f"Jira ticket created: {ticket}")
    
    print("✅ Mock skills test passed")
    print()

async def test_pipeline():
    """Test pipeline with mock data."""
    print("🔄 Testing Pipeline...")
    
    try:
        from orchestrator.pipeline import run_pipeline
        
        # Create dummy context
        class DummyCtx:
            user_id = "test_user"
            session_id = "test_session"
        
        # Test query
        query = "What was discussed about Optum project?"
        response = await run_pipeline(query, DummyCtx())
        
        print(f"Query: {query}")
        print(f"Response length: {len(response)} characters")
        print(f"Response preview: {response[:100]}...")
        
        print("✅ Pipeline test passed")
        
    except Exception as e:
        print(f"❌ Pipeline test failed: {e}")
    
    print()

async def main():
    """Run all tests."""
    print("🧪 Digital Twin Local Development Test")
    print("=" * 50)
    print()
    
    test_config()
    await test_mock_skills()
    
    # Run async test
    await test_pipeline()
    
    print("🎉 All tests completed!")

if __name__ == "__main__":
    asyncio.run(main())

 