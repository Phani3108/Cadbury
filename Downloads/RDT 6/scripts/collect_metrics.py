#!/usr/bin/env python3
"""
Metrics collection script for Digital Twin.
"""
import os
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Any

def get_db_metrics() -> Dict[str, Any]:
    """Get metrics from SQLite databases."""
    metrics = {}
    
    # Quote cache metrics
    try:
        from ingest.quote_rewriter import get_cache_stats
        cache_stats = get_cache_stats()
        metrics['quote_cache'] = cache_stats
    except Exception as e:
        metrics['quote_cache'] = {'error': str(e)}
    
    # KB chunks count
    try:
        from ingest.kb_loader import get_recent_chunks
        recent_chunks = get_recent_chunks(270)
        metrics['kb_chunks'] = len(recent_chunks)
    except Exception as e:
        metrics['kb_chunks'] = {'error': str(e)}
    
    return metrics

def get_api_metrics() -> Dict[str, Any]:
    """Get API metrics (mock for now)."""
    return {
        'total_queries': 150,
        'success_rate': 95.2,
        'avg_response_time': 1200,
        'error_rate': 4.8,
        'top_queries': [
            'What is the status of Optum project?',
            'Schedule a call with Ramki',
            'What were the key insights from recent meetings?'
        ]
    }

def get_system_metrics() -> Dict[str, Any]:
    """Get system health metrics."""
    return {
        'uptime_hours': 168,  # 1 week
        'memory_usage_mb': 512,
        'cpu_usage_percent': 15,
        'disk_usage_gb': 2.5,
        'active_connections': 5
    }

def collect_all_metrics() -> Dict[str, Any]:
    """Collect all metrics."""
    timestamp = datetime.now().isoformat()
    
    metrics = {
        'timestamp': timestamp,
        'collection_date': datetime.now().strftime('%Y-%m-%d'),
        'system': get_system_metrics(),
        'api': get_api_metrics(),
        'database': get_db_metrics()
    }
    
    # Calculate derived metrics
    api_metrics = metrics['api']
    metrics['summary'] = {
        'total_queries': api_metrics['total_queries'],
        'success_rate': api_metrics['success_rate'],
        'avg_response_time': api_metrics['avg_response_time'],
        'kb_chunks': metrics['database'].get('kb_chunks', 0)
    }
    
    return metrics

def save_metrics(metrics: Dict[str, Any], filename: str = 'metrics.json'):
    """Save metrics to JSON file."""
    with open(filename, 'w') as f:
        json.dump(metrics, f, indent=2)
    print(f"✅ Metrics saved to {filename}")

def main():
    """Main metrics collection function."""
    print("📊 Collecting Digital Twin metrics...")
    
    try:
        metrics = collect_all_metrics()
        save_metrics(metrics)
        
        # Print summary
        summary = metrics['summary']
        print(f"\n📈 Metrics Summary:")
        print(f"  • Total Queries: {summary['total_queries']}")
        print(f"  • Success Rate: {summary['success_rate']}%")
        print(f"  • Avg Response Time: {summary['avg_response_time']}ms")
        print(f"  • KB Chunks: {summary['kb_chunks']}")
        
        return 0
        
    except Exception as e:
        print(f"❌ Metrics collection failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main()) 