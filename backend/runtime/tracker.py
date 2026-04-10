"""
Pipeline run tracker — wraps any delegate pipeline's run() to record
execution in the pipeline_runs table. Emits stage updates via the event bus.
"""

from __future__ import annotations

import traceback
import uuid
from datetime import datetime, timezone
from functools import wraps
from typing import Any, Callable, Coroutine

from memory.graph import create_pipeline_run, update_pipeline_run


def tracked_pipeline(delegate_id: str):
    """
    Decorator for pipeline run() methods.
    Records run start/stage/complete/failure in pipeline_runs table.

    Usage:
        class RecruiterPipeline:
            @tracked_pipeline("recruiter")
            async def run(self) -> PipelineContext:
                ...
    """
    def decorator(fn):
        @wraps(fn)
        async def wrapper(self, *args, **kwargs):
            run_id = str(uuid.uuid4())
            # If the pipeline context has a trace_id, use it; otherwise generate one
            trace_id = str(uuid.uuid4())

            await create_pipeline_run(run_id, delegate_id, trace_id)

            try:
                result = await fn(self, *args, **kwargs)

                # Try to extract trace_id from result
                if hasattr(result, "trace_id"):
                    trace_id = result.trace_id

                # Build a summary from the result if possible
                summary = None
                if hasattr(result, "events_emitted"):
                    summary = f"{len(result.events_emitted)} events emitted"
                if hasattr(result, "errors") and result.errors:
                    summary = (summary or "") + f", {len(result.errors)} errors"

                await update_pipeline_run(
                    run_id,
                    status="completed",
                    summary=summary,
                )
                return result

            except Exception as exc:
                await update_pipeline_run(
                    run_id,
                    status="failed",
                    error=f"{type(exc).__name__}: {exc}",
                )
                raise

        return wrapper
    return decorator
