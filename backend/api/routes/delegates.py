from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from runtime.kernel import get_runtime
from memory.graph import MemoryGraph
from runtime.event_bus import get_event_bus

router = APIRouter(prefix="/v1/delegates", tags=["delegates"])


class DelegateStats(BaseModel):
    processed_today: int = 0
    pending_approvals: int = 0
    auto_rate: float = 0.0
    avg_score: float = 0.0


class DelegateInfo(BaseModel):
    id: str
    name: str
    description: str
    status: str
    last_active: str | None
    stats: DelegateStats


DELEGATE_REGISTRY = [
    DelegateInfo(
        id="recruiter",
        name="Recruiter Delegate",
        description="Screens inbound recruiter emails and job opportunities",
        status="active",
        last_active=None,
        stats=DelegateStats(),
    )
]


@router.get("", response_model=list[DelegateInfo])
async def list_delegates():
    return DELEGATE_REGISTRY


@router.get("/{delegate_id}", response_model=DelegateInfo)
async def get_delegate(delegate_id: str):
    for d in DELEGATE_REGISTRY:
        if d.id == delegate_id:
            return d
    raise HTTPException(404, "Delegate not found")


@router.post("/{delegate_id}/pause")
async def pause_delegate(delegate_id: str):
    runtime = get_runtime()
    if runtime:
        await runtime.pause(delegate_id)
    return {"status": "paused", "delegate_id": delegate_id}


@router.post("/{delegate_id}/resume")
async def resume_delegate(delegate_id: str):
    runtime = get_runtime()
    if runtime:
        await runtime.resume(delegate_id)
    return {"status": "resumed", "delegate_id": delegate_id}


class RunResult(BaseModel):
    trace_id: str
    emails_ingested: int
    opportunities_found: int
    events_emitted: int
    errors: list[str]


@router.post("/recruiter/run", response_model=RunResult)
async def run_recruiter_pipeline():
    """Manually trigger the recruiter pipeline (for testing/demo). Uses mock email provider."""
    from delegates.recruiter.pipeline import RecruiterPipeline
    from skills.email.mock import MockEmailProvider

    pipeline = RecruiterPipeline(
        email_provider=MockEmailProvider(),
        graph=MemoryGraph(),
        event_bus=get_event_bus(),
        llm_enabled=False,  # Use mock extraction — no OpenAI key needed for demo
    )
    ctx = await pipeline.run()
    return RunResult(
        trace_id=ctx.trace_id,
        emails_ingested=len(ctx.emails_ingested),
        opportunities_found=len(ctx.opportunities),
        events_emitted=len(ctx.events_emitted),
        errors=ctx.errors,
    )
