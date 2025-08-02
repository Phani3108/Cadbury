#!/usr/bin/env python3
"""
Test Azure Search ingestion functionality.
"""

import os
import sys
import asyncio
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

def test_azure_ingest():
    """Test Azure Search ingestion."""
    print("📤 Testing Azure Search Ingestion...")
    
    # Check if we're in production mode
    if os.getenv("MODE") != "prod":
        print("ℹ️  Skipping Azure ingest test in development mode")
        print("💡 To test: MODE=prod python scripts/test_azure_ingest.py")
        return True
    
    # Check required environment variables
    required_vars = [
        "AZURE_SEARCH_ENDPOINT",
        "AZURE_SEARCH_KEY", 
        "AZURE_INDEX"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {missing_vars}")
        return False
    
    try:
        # Test with sample data directory
        sample_dir = "./data"
        if not os.path.exists(sample_dir):
            print(f"❌ Sample data directory not found: {sample_dir}")
            return False
        
        # Run the uploader
        from ingest.uploader import upload_documents
        
        print(f"📁 Uploading documents from {sample_dir}...")
        upload_documents(sample_dir, batch_size=50)
        
        print("✅ Azure Search ingestion test completed")
        return True
        
    except Exception as e:
        print(f"❌ Azure Search ingestion failed: {e}")
        return False

def test_azure_search_query():
    """Test Azure Search query functionality."""
    print("🔍 Testing Azure Search Query...")
    
    try:
        from skills.kb_search import hybrid_search
        
        # Test a simple query
        results = hybrid_search("Optum", ["Optum"], k=5)
        
        if results:
            print(f"✅ Azure Search query working: {len(results)} results found")
            return True
        else:
            print("⚠️  Azure Search returned no results")
            return False
            
    except Exception as e:
        print(f"❌ Azure Search query failed: {e}")
        return False

def main():
    """Run Azure ingest and query tests."""
    print("🧪 Azure Search Integration Test")
    print("=" * 50)
    
    tests = [
        ("Azure Ingest", test_azure_ingest),
        ("Azure Query", test_azure_search_query)
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
        print("🎉 All Azure Search tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed. Review configuration.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 