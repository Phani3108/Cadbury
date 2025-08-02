#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from digital_twin.utils.config import get_settings
from skills.kb_search import hybrid_search

def main():
    if len(sys.argv) != 2:
        print("Usage: python scripts/quick_search.py <query>")
        sys.exit(1)
    
    query = sys.argv[1]
    settings = get_settings()
    
    print(f"🔍 Testing search for: '{query}'")
    print(f"📊 Backend: {settings.SEARCH_BACKEND}")
    print(f"🌍 Mode: {'PROD' if settings.MODE == 'prod' else 'DEV'}")
    
    try:
        results = hybrid_search(query, entities=[], k=5)
        print(f"✅ Found {len(results)} results")
        
        for i, result in enumerate(results[:3], 1):
            print(f"  {i}. {result.text[:60]}...")
            print(f"     Speaker: {result.speaker or 'Unknown'}")
            print(f"     Source: {result.chunk_id}")
            print()
            
    except Exception as e:
        print(f"❌ Search failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
