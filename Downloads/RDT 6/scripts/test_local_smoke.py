#!/usr/bin/env python3
"""
Local Smoke Test Script
Tests core functionality without server dependencies.
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orchestrator.pipeline import run_pipeline
from digital_twin.utils.config import get_settings

class MockUserContext:
    def __init__(self):
        self.user_id = "test_user"
        self.session_id = "test_session"

async def test_smoke_queries():
    """Test core smoke queries."""
    settings = get_settings()
    
    print(f"🧪 Testing Digital Twin in {settings.MODE} mode")
    print(f"🔧 Search Backend: {settings.SEARCH_BACKEND}")
    print(f"💰 Models: {settings.LLM_CHEAP} (cheap), {settings.LLM_HEAVY} (heavy)")
    print(f"🛠️  Mock Tools: {settings.TOOLS_MOCK}")
    print()
    
    # Test queries
    test_queries = [
        "Last discussion on Optum",
        "Schedule call with Ramki", 
        "Did Ramki promise 10X revenue?"
    ]
    
    user_ctx = MockUserContext()
    
    for i, query in enumerate(test_queries, 1):
        print(f"📝 Test {i}: {query}")
        try:
            result = await run_pipeline(query, user_ctx)
            print(f"✅ Response: {result[:200]}...")
            
            # Check for SAFE_FAIL
            if "SAFE_FAIL" in query and "don't have a recent source" in result:
                print("✅ SAFE_FAIL working correctly")
            elif "SAFE_FAIL" not in query and len(result) > 50:
                print("✅ Normal response working")
            else:
                print("⚠️  Response format unexpected")
                
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print("-" * 50)
    
    print("🎉 Smoke test completed!")

if __name__ == "__main__":
    asyncio.run(test_smoke_queries()) 