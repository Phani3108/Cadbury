"""
OpenTelemetry tracing for Digital Twin.
"""
import os
from functools import wraps
from typing import Optional, Dict, Any
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.resources import Resource

# Try to import Azure Monitor exporter (optional)
try:
    from opentelemetry.exporter.azure_monitor import AzureMonitorTraceExporter
    AZURE_MONITOR_AVAILABLE = True
except ImportError:
    AZURE_MONITOR_AVAILABLE = False

# Initialize tracer
_tracer = None

def _get_tracer():
    """Get or initialize the tracer."""
    global _tracer
    if _tracer is None:
        # Set up tracer provider
        trace.set_tracer_provider(
            TracerProvider(
                resource=Resource.create({"service.name": "digital-twin"})
            )
        )
        
        # Set up Azure Monitor exporter if configured and available
        connection_string = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
        if connection_string and AZURE_MONITOR_AVAILABLE:
            try:
                azure_exporter = AzureMonitorTraceExporter(
                    connection_string=connection_string
                )
                trace.get_tracer_provider().add_span_processor(
                    BatchSpanProcessor(azure_exporter)
                )
                print("✅ Azure Monitor telemetry configured")
            except Exception as e:
                print(f"⚠️  Azure Monitor setup failed: {e}, using console exporter")
                console_exporter = ConsoleSpanExporter()
                trace.get_tracer_provider().add_span_processor(
                    BatchSpanProcessor(console_exporter)
                )
        else:
            # Use console exporter for development
            console_exporter = ConsoleSpanExporter()
            trace.get_tracer_provider().add_span_processor(
                BatchSpanProcessor(console_exporter)
            )
            if os.getenv("MODE") == "prod":
                print("⚠️  Production mode but no Azure Monitor connection string")
            else:
                print("ℹ️  Development mode - using console telemetry")
        
        _tracer = trace.get_tracer(__name__)
    
    return _tracer

def trace_span(name: str, attributes: Optional[Dict[str, Any]] = None):
    """
    Decorator to trace function execution.
    
    Args:
        name: Span name
        attributes: Optional span attributes
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            tracer = _get_tracer()
            with tracer.start_as_current_span(name, attributes=attributes) as span:
                try:
                    result = await func(*args, **kwargs)
                    span.set_attribute("success", True)
                    return result
                except Exception as e:
                    span.set_attribute("success", False)
                    span.set_attribute("error", str(e))
                    raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            tracer = _get_tracer()
            with tracer.start_as_current_span(name, attributes=attributes) as span:
                try:
                    result = func(*args, **kwargs)
                    span.set_attribute("success", True)
                    return result
                except Exception as e:
                    span.set_attribute("success", False)
                    span.set_attribute("error", str(e))
                    raise
        
        # Return appropriate wrapper based on function type
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

def add_span_attribute(key: str, value: Any):
    """Add attribute to current span."""
    current_span = trace.get_current_span()
    if current_span:
        current_span.set_attribute(key, value) 