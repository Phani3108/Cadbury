"""
Integration tests for telemetry functionality.
"""

import pytest
import os
from digital_twin.observability.tracing import trace_span, add_span_attribute

def test_tracing_decorator():
    """Test trace_span decorator."""
    @trace_span("test_operation")
    def test_function():
        add_span_attribute("test_key", "test_value")
        return "success"
    
    result = test_function()
    assert result == "success"

def test_span_attributes():
    """Test adding span attributes."""
    @trace_span("test_attributes")
    def test_attributes():
        add_span_attribute("string_attr", "test")
        add_span_attribute("int_attr", 42)
        add_span_attribute("bool_attr", True)
        return True
    
    result = test_attributes()
    assert result is True

def test_telemetry_environment():
    """Test telemetry environment configuration."""
    # Check if Azure Monitor connection string is available
    connection_string = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
    
    if connection_string:
        # Should work with real Azure Monitor
        assert len(connection_string) > 0
    else:
        # Should fall back to console exporter
        print("ℹ️  No Azure Monitor connection string - using console exporter")

def test_pipeline_telemetry():
    """Test pipeline telemetry integration."""
    from orchestrator.pipeline import DigitalTwinPipeline
    
    pipeline = DigitalTwinPipeline()
    
    # Test that pipeline stages have telemetry
    assert hasattr(pipeline._intent_stage, '__wrapped__')
    assert hasattr(pipeline._hybrid_search_stage, '__wrapped__')
    assert hasattr(pipeline._coherence_stage, '__wrapped__')
    assert hasattr(pipeline._compress_stage, '__wrapped__')
    assert hasattr(pipeline._router_stage, '__wrapped__')
    assert hasattr(pipeline._planner_stage, '__wrapped__')
    assert hasattr(pipeline._verifier_stage, '__wrapped__')
    assert hasattr(pipeline._formatter_stage, '__wrapped__')

def test_cost_tracking():
    """Test cost tracking functionality."""
    from scripts.ai_cost_to_csv import parse_span_data
    
    # Test with empty data
    empty_spans = []
    cost_records = parse_span_data(empty_spans)
    assert len(cost_records) == 0
    
    # Test with sample data
    sample_spans = [
        {
            'timestamp': '2025-08-01T10:00:00Z',
            'operation_Name': 'planner_stage',
            'customDimensions': '{"total_tokens": 1000, "model_used": "MODEL_GPT35"}',
            'duration': 2000,
            'resultCode': '200'
        }
    ]
    
    cost_records = parse_span_data(sample_spans)
    assert len(cost_records) == 1
    assert cost_records[0]['total_tokens'] == 1000
    assert cost_records[0]['model'] == 'MODEL_GPT35'

def test_metrics_collection():
    """Test metrics collection functionality."""
    from scripts.nightly_metrics import collect_daily_metrics
    
    # Test metrics collection
    metrics = collect_daily_metrics("2025-08-01")
    
    # Should return valid metrics structure
    assert 'date' in metrics
    assert 'query_count' in metrics
    assert 'grounding_percentage' in metrics
    assert 'total_cost' in metrics
    assert 'total_tokens' in metrics
    assert 'model_breakdown' in metrics
    assert 'error_count' in metrics
    assert 'avg_response_time' in metrics 