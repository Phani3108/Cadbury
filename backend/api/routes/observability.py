"""API route for system observability / health dashboard."""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/v1/observability", tags=["observability"])


@router.get("/health")
async def system_health():
    """Return comprehensive system health data."""
    from observability.metrics import get_system_health
    return await get_system_health()


@router.get("/metrics")
async def get_metrics():
    """Return raw metrics data."""
    from observability.metrics import _metrics, _counters, get_metric_summary
    return {
        "metrics": {name: get_metric_summary(name) for name in _metrics.keys()},
        "counters": dict(_counters),
    }
