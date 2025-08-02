#!/usr/bin/env python3
"""
Token Cost Tracking Script
Calculates total token usage for the repository.
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, Any, List
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from digital_twin.utils.config import get_settings

def count_tokens_in_file(file_path: str) -> int:
    """Count tokens in a single file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        # Rough token estimation: 1 token ≈ 4 characters
        return len(content) // 4
    except Exception as e:
        print(f"⚠️  Error reading {file_path}: {e}")
        return 0

def count_tokens_in_directory(directory: str, extensions: List[str] = None) -> Dict[str, int]:
    """Count tokens in all files in a directory."""
    if extensions is None:
        extensions = ['.py', '.md', '.txt', '.json', '.yaml', '.yml']
    
    token_counts = {}
    total_tokens = 0
    
    for file_path in Path(directory).rglob('*'):
        if file_path.is_file() and file_path.suffix in extensions:
            # Skip certain directories and files
            skip_patterns = [
                '__pycache__', '.git', '.pytest_cache', 'venv', 'node_modules',
                'data/', 'cache/', '.cache/', 'logs/', 'build/', 'dist/',
                '*.pyc', '*.log', '*.tmp', '*.bak'
            ]
            
            if any(skip in str(file_path) for skip in skip_patterns):
                continue
            
            # Only count source code and documentation
            if file_path.suffix in ['.py', '.md', '.txt']:
                tokens = count_tokens_in_file(str(file_path))
                token_counts[str(file_path)] = tokens
                total_tokens += tokens
    
    token_counts['TOTAL'] = total_tokens
    return token_counts

def calculate_cost_estimate(token_count: int, model: str = "gpt-3.5-turbo") -> float:
    """Calculate estimated cost for token count."""
    # Cost per 1K tokens (approximate)
    costs = {
        "gpt-3.5-turbo": 0.002,
        "gpt-4o-mini": 0.00015,
        "gpt-4": 0.03,
        "gpt-4o": 0.005
    }
    
    cost_per_1k = costs.get(model, 0.002)
    return (token_count / 1000) * cost_per_1k

def main():
    """Main function to calculate repository token cost."""
    settings = get_settings()
    
    # Get repository root
    repo_root = Path(__file__).parent.parent
    
    print(f"📊 Token Cost Analysis for {repo_root}")
    print(f"🔧 Mode: {settings.MODE}")
    print(f"💰 Model: {settings.LLM_CHEAP} (cheap), {settings.LLM_HEAVY} (heavy)")
    print()
    
    # Count tokens in repository
    token_counts = count_tokens_in_directory(str(repo_root))
    total_tokens = token_counts['TOTAL']
    
    # Calculate costs
    cheap_cost = calculate_cost_estimate(total_tokens, settings.LLM_CHEAP)
    heavy_cost = calculate_cost_estimate(total_tokens, settings.LLM_HEAVY)
    
    print(f"📈 Repository Statistics:")
    print(f"   Total files analyzed: {len(token_counts) - 1}")
    print(f"   Total tokens: {total_tokens:,}")
    print(f"   Estimated cost ({settings.LLM_CHEAP}): ${cheap_cost:.4f}")
    print(f"   Estimated cost ({settings.LLM_HEAVY}): ${heavy_cost:.4f}")
    print()
    
    # Check against limit
    limit = settings.TOKEN_COST_LIMIT
    if total_tokens > limit:
        print(f"❌ Token count ({total_tokens:,}) exceeds limit ({limit:,})")
        return 1
    else:
        print(f"✅ Token count ({total_tokens:,}) within limit ({limit:,})")
        return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 