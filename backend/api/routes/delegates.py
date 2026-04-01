from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from runtime.kernel import get_runtime
from memory.graph import MemoryGraph, list_approvals, list_decisions
from memory.models import ApprovalStatus
from runtime.event_bus import get_event_bus
from policy.loader import load_policy
from policy.models import DelegationPolicy

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


async def _get_recruiter_stats() -> DelegateStats:
    """Compute live stats for the recruiter delegate."""
    from datetime import datetime, timezone, timedelta
    from memory.graph import list_opportunities, list_events

    pending = await list_approvals(ApprovalStatus.PENDING)
    opps = await list_opportunities(500)
    today = datetime.now(timezone.utc).date()
    events_today = [
        e for e in await list_events("recruiter", 500)
        if e.timestamp.date() == today
    ]

    scored = [o for o in opps if o.match_score > 0]
    avg_score = sum(o.match_score for o in scored) / len(scored) if scored else 0.0

    decisions = await list_decisions("recruiter", 500)
    auto_count = sum(1 for d in decisions if not d.human_approved and d.action_taken.startswith("auto"))
    auto_rate = auto_count / len(decisions) if decisions else 0.0

    # "processed today" = distinct opportunities touched today
    opp_ids_today = {
        e.payload.get("opportunity_id")
        for e in events_today
        if e.payload.get("opportunity_id")
    }

    return DelegateStats(
        processed_today=len(opp_ids_today),
        pending_approvals=len(pending),
        auto_rate=round(auto_rate, 3),
        avg_score=round(avg_score, 3),
    )


@router.get("", response_model=list[DelegateInfo])
async def list_delegates():
    stats = await _get_recruiter_stats()
    DELEGATE_REGISTRY[0].stats = stats
    return DELEGATE_REGISTRY


@router.get("/{delegate_id}", response_model=DelegateInfo)
async def get_delegate(delegate_id: str):
    for d in DELEGATE_REGISTRY:
        if d.id == delegate_id:
            if delegate_id == "recruiter":
                d.stats = await _get_recruiter_stats()
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


# ─── Policy endpoints ──────────────────────────────────────────────────────────

class PolicyImpact(BaseModel):
    period_days: int = 30
    total_processed: int = 0
    auto_approved: int = 0
    reviewed: int = 0
    auto_rejected: int = 0
    estimated_time_saved_hours: float = 0.0


@router.get("/{delegate_id}/policy", response_model=DelegationPolicy)
async def get_policy(delegate_id: str):
    try:
        return load_policy(delegate_id)
    except FileNotFoundError:
        raise HTTPException(404, f"No policy found for delegate '{delegate_id}'")


@router.get("/{delegate_id}/policy/impact", response_model=PolicyImpact)
async def get_policy_impact(delegate_id: str):
    """Calculate what the historical approval distribution looks like."""
    from memory.graph import list_approvals as _la, list_opportunities
    from memory.models import ApprovalStatus as AS
    from policy.engine import PolicyEngine

    try:
        engine = PolicyEngine(delegate_id)
    except FileNotFoundError:
        raise HTTPException(404, f"No policy found for delegate '{delegate_id}'")

    opps = await list_opportunities(500)
    thresholds = engine.policy.thresholds

    auto_rejected = sum(1 for o in opps if o.match_score < thresholds.auto_decline_below)
    would_engage = sum(1 for o in opps if o.match_score >= thresholds.min_score_for_engagement)
    reviewed = len(opps) - auto_rejected

    # ~5 min per review saved when auto-rejected
    time_saved = auto_rejected * (5 / 60)

    return PolicyImpact(
        period_days=30,
        total_processed=len(opps),
        auto_approved=0,          # Phase 2 when auto_approve=true for declines
        reviewed=reviewed,
        auto_rejected=auto_rejected,
        estimated_time_saved_hours=round(time_saved, 2),
    )


# ─── Manual pipeline trigger ───────────────────────────────────────────────────

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
        llm_enabled=False,
    )
    ctx = await pipeline.run()
    return RunResult(
        trace_id=ctx.trace_id,
        emails_ingested=len(ctx.emails_ingested),
        opportunities_found=len(ctx.opportunities),
        events_emitted=len(ctx.events_emitted),
        errors=ctx.errors,
    )
