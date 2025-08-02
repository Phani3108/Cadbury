import asyncio
import pytest
from orchestrator.pipeline import run_pipeline

class DummyCtx: 
    pass

def test_optum():
    """Smoke test for pipeline with Optum query."""
    out = asyncio.run(run_pipeline("What was last discussion on Optum?", DummyCtx()))
    assert "Buddy" in out
    assert isinstance(out, str)
    assert len(out) > 0
    assert len(out) < 1200  # Check compressed result length

def test_pipeline_no_exceptions():
    """Test that pipeline doesn't throw exceptions."""
    try:
        out = asyncio.run(run_pipeline("Tell me about microservices", DummyCtx()))
        assert isinstance(out, str)
    except Exception as e:
        pytest.fail(f"Pipeline threw exception: {e}")

def test_pipeline_empty_query():
    """Test pipeline handles empty queries gracefully."""
    try:
        out = asyncio.run(run_pipeline("", DummyCtx()))
        assert isinstance(out, str)
    except Exception as e:
        pytest.fail(f"Pipeline threw exception on empty query: {e}") 