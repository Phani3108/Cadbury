#!/usr/bin/env python3
"""
Sanity script to test model connectivity and configuration.
"""
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from digital_twin.utils.config import openai_kwargs, get_model_key, is_development, is_production

def main():
    """Test model configuration and connectivity."""
    print("🔧 Digital Twin Model Configuration Test")
    print("=" * 50)
    
    # Check environment
    mode = os.getenv("MODE", "development")
    print(f"Mode: {mode}")
    print(f"Development: {is_development()}")
    print(f"Production: {is_production()}")
    print()
    
    # Test model keys
    print("📋 Model Configuration:")
    gpt35_key = get_model_key(is_heavy=False)
    gpt4_key = get_model_key(is_heavy=True)
    print(f"GPT-3.5 Key: {gpt35_key}")
    print(f"GPT-4 Key: {gpt4_key}")
    print()
    
    # Test OpenAI kwargs
    print("🔗 OpenAI Configuration:")
    gpt35_kwargs = openai_kwargs(gpt35_key)
    gpt4_kwargs = openai_kwargs(gpt4_key)
    
    print("GPT-3.5 kwargs:")
    for key, value in gpt35_kwargs.items():
        if key == "api_key":
            print(f"  {key}: {value[:10]}..." if value else f"  {key}: None")
        else:
            print(f"  {key}: {value}")
    
    print("\nGPT-4 kwargs:")
    for key, value in gpt4_kwargs.items():
        if key == "api_key":
            print(f"  {key}: {value[:10]}..." if value else f"  {key}: None")
        else:
            print(f"  {key}: {value}")
    print()
    
    # Check environment variables
    print("🔍 Environment Variables:")
    important_vars = [
        "OPENAI_API_TYPE",
        "OPENAI_API_KEY", 
        "AZURE_OPENAI_ENDPOINT",
        "MODEL_GPT4",
        "MODEL_GPT35"
    ]
    
    for var in important_vars:
        value = os.getenv(var)
        if value:
            if "KEY" in var:
                print(f"  {var}: {value[:10]}...")
            else:
                print(f"  {var}: {value}")
        else:
            print(f"  {var}: ❌ NOT SET")
    
    print()
    print("✅ Configuration test complete!")
    
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  Warning: OPENAI_API_KEY not set")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 