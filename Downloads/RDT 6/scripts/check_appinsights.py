#!/usr/bin/env python3
"""
Check Application Insights telemetry.
"""

import os
import sys
import json
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

def check_console_telemetry():
    """Check console telemetry in development mode."""
    print("📊 Checking Console Telemetry...")
    
    try:
        from digital_twin.observability.tracing import trace_span, add_span_attribute
        
        @trace_span("test_telemetry_check")
        def test_function():
            add_span_attribute("test", "console_telemetry")
            add_span_attribute("timestamp", datetime.now().isoformat())
            return "success"
        
        result = test_function()
        
        if result == "success":
            print("✅ Console telemetry working")
            return True
        else:
            print("❌ Console telemetry failed")
            return False
            
    except Exception as e:
        print(f"❌ Console telemetry check failed: {e}")
        return False

def check_appinsights_telemetry():
    """Check Application Insights telemetry."""
    print("📊 Checking Application Insights Telemetry...")
    
    connection_string = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
    
    if not connection_string:
        print("ℹ️  No Application Insights connection string - skipping")
        return True
    
    try:
        from azure.monitor.query import LogsQueryClient
        from azure.identity import DefaultAzureCredential
        
        # Create client
        credential = DefaultAzureCredential()
        client = LogsQueryClient(credential)
        
        # Query for today's spans
        today = datetime.now().strftime("%Y-%m-%d")
        query = f"""
        traces
        | where timestamp >= datetime({today})
        | where customDimensions.service_name == "digital-twin"
        | count
        """
        
        response = client.query_workspace(
            workspace_id=os.getenv("AZURE_LOG_ANALYTICS_WORKSPACE_ID"),
            query=query,
            timespan=timedelta(hours=24)
        )
        
        span_count = response.tables[0].rows[0][0]
        
        if span_count > 0:
            print(f"✅ Application Insights working: {span_count} spans found today")
            return True
        else:
            print("⚠️  No spans found in Application Insights")
            return False
            
    except Exception as e:
        print(f"❌ Application Insights check failed: {e}")
        return False

def check_telemetry_integration():
    """Check telemetry integration with pipeline."""
    print("📊 Checking Telemetry Integration...")
    
    try:
        from digital_twin.observability.tracing import trace_span, add_span_attribute
        from orchestrator.pipeline import run_pipeline
        
        @trace_span("test_pipeline_telemetry")
        async def test_pipeline():
            add_span_attribute("test_query", "telemetry test")
            
            # Mock user context
            class MockUserContext:
                def __init__(self):
                    self.user_id = "test_user"
                    self.session_id = "test_session"
            
            user_ctx = MockUserContext()
            
            # Run a simple pipeline test
            result = await run_pipeline("test query", user_ctx)
            
            add_span_attribute("result_length", len(result))
            return result
        
        import asyncio
        result = asyncio.run(test_pipeline())
        
        if result and len(result) > 0:
            print("✅ Pipeline telemetry integration working")
            return True
        else:
            print("❌ Pipeline telemetry integration failed")
            return False
            
    except Exception as e:
        print(f"❌ Telemetry integration check failed: {e}")
        return False

def main():
    """Run telemetry checks."""
    print("🧪 Telemetry Integration Test")
    print("=" * 50)
    
    tests = [
        ("Console Telemetry", check_console_telemetry),
        ("Application Insights", check_appinsights_telemetry),
        ("Pipeline Integration", check_telemetry_integration)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name} test...")
        try:
            result = test_func()
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
        print("🎉 All telemetry tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed. Review configuration.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 