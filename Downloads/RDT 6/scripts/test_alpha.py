#!/usr/bin/env python3
"""
Test script for alpha functionality - end-to-end testing.
"""
import os
import sys
import asyncio
import requests
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_local_server():
    """Test the local FastAPI server."""
    print("🧪 Testing Local Server...")
    
    try:
        # Test health endpoint
        response = requests.get("http://localhost:8000/health")
        if response.status_code == 200:
            print("✅ Health endpoint working")
        else:
            print(f"❌ Health endpoint failed: {response.status_code}")
            return False
        
        # Test config endpoint
        response = requests.get("http://localhost:8000/config")
        if response.status_code == 200:
            config = response.json()
            print(f"✅ Config endpoint working - Mode: {config.get('mode')}")
        else:
            print(f"❌ Config endpoint failed: {response.status_code}")
            return False
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Server not running. Start with: MODE=dev uvicorn orchestrator.app:app --reload")
        return False

def test_optum_query():
    """Test Optum discussion query."""
    print("\n🔍 Testing Optum Query...")
    
    try:
        response = requests.post(
            "http://localhost:8000/chat",
            json={"query": "Last discussion on Optum"}
        )
        
        if response.status_code == 200:
            result = response.json()
            response_text = result["response"]
            
            print(f"✅ Query successful")
            print(f"Response length: {len(response_text)} characters")
            print(f"Response preview: {response_text[:200]}...")
            
            # Check response quality
            if len(response_text) < 1200:
                print("✅ Response length within limits")
            else:
                print("⚠️ Response length exceeds 1200 characters")
            
            if "Source-" in response_text:
                print("✅ Response includes source citations")
            else:
                print("⚠️ Response missing source citations")
            
            return True
        else:
            print(f"❌ Query failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Query test failed: {e}")
        return False

def test_booking_query():
    """Test booking slot query."""
    print("\n📅 Testing Booking Query...")
    
    try:
        response = requests.post(
            "http://localhost:8000/chat",
            json={"query": "Book a slot with Ramki"}
        )
        
        if response.status_code == 200:
            result = response.json()
            response_text = result["response"]
            
            print(f"✅ Booking query successful")
            print(f"Response length: {len(response_text)} characters")
            print(f"Response preview: {response_text[:200]}...")
            
            # Check for booking-specific content
            if any(word in response_text.lower() for word in ["slot", "meeting", "calendar", "time"]):
                print("✅ Response includes booking-related content")
            else:
                print("⚠️ Response missing booking-related content")
            
            return True
        else:
            print(f"❌ Booking query failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Booking test failed: {e}")
        return False

def test_jira_query():
    """Test Jira creation query."""
    print("\n🎫 Testing Jira Query...")
    
    try:
        response = requests.post(
            "http://localhost:8000/chat",
            json={"query": "Create Jira for Optum P1 blockers"}
        )
        
        if response.status_code == 200:
            result = response.json()
            response_text = result["response"]
            
            print(f"✅ Jira query successful")
            print(f"Response length: {len(response_text)} characters")
            print(f"Response preview: {response_text[:200]}...")
            
            # Check for Jira-specific content
            if any(word in response_text.lower() for word in ["jira", "ticket", "issue", "created"]):
                print("✅ Response includes Jira-related content")
            else:
                print("⚠️ Response missing Jira-related content")
            
            return True
        else:
            print(f"❌ Jira query failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Jira test failed: {e}")
        return False

def main():
    """Run all alpha tests."""
    print("🚀 Digital Twin Alpha Testing")
    print("=" * 50)
    
    # Test server
    if not test_local_server():
        return
    
    # Test queries
    tests = [
        test_optum_query,
        test_booking_query,
        test_jira_query
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n📊 Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed! Alpha is ready.")
    else:
        print("⚠️ Some tests failed. Check implementation.")

if __name__ == "__main__":
    main() 