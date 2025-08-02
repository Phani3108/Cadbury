"""
Router regression tests for Digital Twin.
"""
import pytest
from orchestrator.router import pick

def test_router_cheap_path():
    """Test that router selects GPT-3.5 for <12k tokens."""
    result = pick("STATUS", 5000)
    assert result in ["MODEL_GPT35", "gpt-3.5-turbo"], f"Expected GPT-3.5 model, got {result}"

def test_router_expensive_path():
    """Test that router selects GPT-4 for >12k tokens."""
    result = pick("INSIGHT", 15000)
    assert result in ["MODEL_GPT4", "gpt-4o-mini"], f"Expected GPT-4 model, got {result}"

def test_router_intent_based():
    """Test that specific intents trigger expensive model."""
    result = pick("COMPARISON", 5000)
    assert result in ["MODEL_GPT4", "gpt-4o-mini"], f"Expected GPT-4 model for COMPARISON, got {result}"

def test_router_development_fallback():
    """Test router works in development mode."""
    result = pick("GENERAL", 5000)
    assert result in ["MODEL_GPT35", "MODEL_GPT4", "gpt-3.5-turbo", "gpt-4o-mini"], f"Invalid model: {result}"

def test_router_cheap_routing():
    """Test that router returns LLM_CHEAP for simple queries."""
    import os
    from digital_twin.utils.config import get_settings
    
    settings = get_settings()
    result = pick("STATUS", 5000)
    
    # Should return the cheap model from settings
    assert result == settings.LLM_CHEAP, f"Expected {settings.LLM_CHEAP}, got {result}" 