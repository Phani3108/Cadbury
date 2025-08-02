#!/usr/bin/env python3
"""
AI Cost Dashboard Script
Pulls telemetry spans and writes daily cost CSV for analysis.
"""

import os
import csv
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any
import requests

# Try to import Azure dependencies (optional)
try:
    from azure.monitor.query import LogsQueryClient
    from azure.identity import DefaultAzureCredential
    AZURE_AVAILABLE = True
except ImportError:
    AZURE_AVAILABLE = False

def get_azure_logs_client():
    """Get Azure Logs client for querying Application Insights."""
    if not AZURE_AVAILABLE:
        print("⚠️  Azure Monitor not available")
        return None
    
    try:
        credential = DefaultAzureCredential()
        client = LogsQueryClient(credential)
        return client
    except Exception as e:
        print(f"⚠️  Azure Logs client failed: {e}")
        return None

def query_telemetry_spans(workspace_id: str, date: str) -> List[Dict[str, Any]]:
    """
    Query telemetry spans for cost analysis.
    
    Args:
        workspace_id: Azure Log Analytics workspace ID
        date: Date in YYYY-MM-DD format
        
    Returns:
        List of span data
    """
    client = get_azure_logs_client()
    if not client:
        return []
    
    # KQL query to get spans with cost-relevant attributes
    query = f"""
    traces
    | where timestamp >= datetime({date}) and timestamp < datetime({date}) + 1d
    | where customDimensions has "total_tokens" or customDimensions has "model_used"
    | project 
        timestamp,
        operation_Name,
        customDimensions,
        duration,
        resultCode
    | order by timestamp desc
    """
    
    try:
        response = client.query_workspace(workspace_id, query)
        return [dict(row) for row in response.tables[0].rows]
    except Exception as e:
        print(f"⚠️  Query failed: {e}")
        return []

def parse_span_data(spans: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Parse span data into cost metrics.
    
    Args:
        spans: Raw span data
        
    Returns:
        List of cost records
    """
    cost_records = []
    
    for span in spans:
        try:
            # Extract custom dimensions
            custom_dims = span.get('customDimensions', {})
            if isinstance(custom_dims, str):
                custom_dims = json.loads(custom_dims)
            
            # Extract cost-relevant fields
            total_tokens = int(custom_dims.get('total_tokens', 0))
            model_used = custom_dims.get('model_used', 'unknown')
            prompt_hash = custom_dims.get('prompt_hash', 'unknown')
            operation = span.get('operation_Name', 'unknown')
            
            # Calculate cost (rough estimates)
            cost_per_1k_tokens = {
                'gpt-3.5-turbo': 0.002,
                'gpt-4': 0.03,
                'gpt-4-turbo': 0.01,
                'MODEL_GPT35': 0.002,
                'MODEL_GPT4': 0.03
            }
            
            cost_per_1k = cost_per_1k_tokens.get(model_used, 0.002)
            cost = (total_tokens / 1000) * cost_per_1k
            
            record = {
                'timestamp': span.get('timestamp', ''),
                'operation': operation,
                'model': model_used,
                'total_tokens': total_tokens,
                'cost_usd': round(cost, 4),
                'prompt_hash': prompt_hash,
                'duration_ms': span.get('duration', 0),
                'result_code': span.get('resultCode', '')
            }
            
            cost_records.append(record)
            
        except Exception as e:
            print(f"⚠️  Failed to parse span: {e}")
            continue
    
    return cost_records

def write_cost_csv(cost_records: List[Dict[str, Any]], date: str):
    """
    Write cost records to CSV file.
    
    Args:
        cost_records: List of cost records
        date: Date for filename
    """
    filename = f"cost_{date}.csv"
    
    if not cost_records:
        print(f"⚠️  No cost data for {date}")
        return
    
    with open(filename, 'w', newline='') as csvfile:
        fieldnames = [
            'timestamp', 'operation', 'model', 'total_tokens', 
            'cost_usd', 'prompt_hash', 'duration_ms', 'result_code'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for record in cost_records:
            writer.writerow(record)
    
    # Calculate summary
    total_cost = sum(r['cost_usd'] for r in cost_records)
    total_tokens = sum(r['total_tokens'] for r in cost_records)
    model_breakdown = {}
    for record in cost_records:
        model = record['model']
        model_breakdown[model] = model_breakdown.get(model, 0) + record['cost_usd']
    
    print(f"✅ Cost report for {date}:")
    print(f"   Total cost: ${total_cost:.4f}")
    print(f"   Total tokens: {total_tokens:,}")
    print(f"   Records: {len(cost_records)}")
    print(f"   Model breakdown: {model_breakdown}")
    print(f"   File: {filename}")

def main():
    """Main function to generate cost report."""
    # Get date (default to yesterday)
    import sys
    if len(sys.argv) > 1:
        date = sys.argv[1]
    else:
        date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    # Get workspace ID from environment
    workspace_id = os.getenv('AZURE_LOG_ANALYTICS_WORKSPACE_ID')
    if not workspace_id:
        print("⚠️  AZURE_LOG_ANALYTICS_WORKSPACE_ID not set")
        print("ℹ️  Set AZURE_LOG_ANALYTICS_WORKSPACE_ID to collect real telemetry data")
        cost_records = []
    else:
        # Query real telemetry data
        spans = query_telemetry_spans(workspace_id, date)
        cost_records = parse_span_data(spans)
    
    write_cost_csv(cost_records, date)

if __name__ == "__main__":
    main() 