"""
Observability module — metrics, health checks, and structured logging.

Provides:
- Pipeline execution timing
- LLM call metrics (latency, tokens, cost)
- Delegate health dashboard data
- Error rate tracking
"""
from __future__ import annotations

import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Optional

logger = logging.getLogger(__name__)

# In-memory metrics (production would use Prometheus/OpenTelemetry)
_metrics: dict[str, list[float]] = defaultdict(list)
_counters: dict[str, int] = defaultdict(int)
_last_reset = datetime.now(timezone.utc)

MAX_METRIC_POINTS = 1000  # Keep last N data points per metric


def record_timing(name: str, duration_seconds: float) -> None:
    """Record a timing metric (e.g., pipeline_duration, llm_latency)."""
    points = _metrics[name]
    points.append(duration_seconds)
    if len(points) > MAX_METRIC_POINTS:
        _metrics[name] = points[-MAX_METRIC_POINTS:]


def increment_counter(name: str, amount: int = 1) -> None:
    """Increment a counter (e.g., pipeline_runs, errors, approvals)."""
    _counters[name] += amount


def get_metric_summary(name: str) -> dict:
    """Get summary stats for a timing metric."""
    points = _metrics.get(name, [])
    if not points:
        return {"count": 0, "avg": 0, "min": 0, "max": 0, "p95": 0}
    sorted_points = sorted(points)
    p95_idx = int(len(sorted_points) * 0.95)
    return {
        "count": len(points),
        "avg": round(sum(points) / len(points), 4),
        "min": round(min(points), 4),
        "max": round(max(points), 4),
        "p95": round(sorted_points[min(p95_idx, len(sorted_points) - 1)], 4),
    }


class PipelineTimer:
    """Context manager for timing pipeline stages."""

    def __init__(self, delegate_id: str, stage: str):
        self.metric_name = f"{delegate_id}.{stage}.duration"
        self._start: float = 0

    def __enter__(self):
        self._start = time.monotonic()
        return self

    def __exit__(self, *args):
        duration = time.monotonic() - self._start
        record_timing(self.metric_name, duration)
        increment_counter(f"{self.metric_name}.count")


@dataclass
class DelegateHealth:
    delegate_id: str
    status: str = "healthy"  # healthy, degraded, error
    last_run: Optional[datetime] = None
    last_error: Optional[str] = None
    runs_24h: int = 0
    errors_24h: int = 0
    avg_pipeline_duration_s: float = 0.0
    error_rate: float = 0.0


async def get_system_health() -> dict:
    """Return overall system health for the monitoring dashboard."""
    from runtime.kernel import get_runtime
    from memory.graph import list_approvals, list_events
    from memory.models import ApprovalStatus
    from policy.budget import get_all_budgets

    runtime = get_runtime()
    runtime_status = runtime.get_status() if runtime else {"paused_delegates": [], "active_jobs": []}

    pending = await list_approvals(ApprovalStatus.PENDING)
    recent_events = await list_events(limit=100)

    now = datetime.now(timezone.utc)
    events_24h = [e for e in recent_events if e.timestamp >= now - timedelta(hours=24)]
    errors_24h = [e for e in events_24h if e.event_type == "error"]

    # Per-delegate health
    delegate_ids = ["recruiter", "calendar", "comms", "finance", "shopping", "learning", "health"]
    delegate_health = {}
    for did in delegate_ids:
        d_events = [e for e in events_24h if e.delegate_id == did]
        d_errors = [e for e in d_events if e.event_type == "error"]
        duration_stats = get_metric_summary(f"{did}.pipeline.duration")

        delegate_health[did] = DelegateHealth(
            delegate_id=did,
            status="error" if len(d_errors) > 3 else ("degraded" if d_errors else "healthy"),
            runs_24h=len(d_events),
            errors_24h=len(d_errors),
            avg_pipeline_duration_s=duration_stats["avg"],
            error_rate=round(len(d_errors) / max(len(d_events), 1), 3),
        )

    budgets = await get_all_budgets()

    return {
        "status": "healthy" if len(errors_24h) < 5 else "degraded",
        "timestamp": now.isoformat(),
        "runtime": runtime_status,
        "pending_approvals": len(pending),
        "events_24h": len(events_24h),
        "errors_24h": len(errors_24h),
        "delegates": {d.delegate_id: {
            "status": d.status,
            "runs_24h": d.runs_24h,
            "errors_24h": d.errors_24h,
            "avg_duration_s": d.avg_pipeline_duration_s,
            "error_rate": d.error_rate,
        } for d in delegate_health.values()},
        "budgets": budgets,
        "metrics": {
            name: get_metric_summary(name)
            for name in _metrics.keys()
        },
        "counters": dict(_counters),
    }
