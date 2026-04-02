from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from runtime.kernel import get_runtime
from memory.graph import MemoryGraph, list_approvals, list_decisions
from memory.models import ApprovalStatus, SimulationRequest
from runtime.event_bus import get_event_bus
from policy.loader import load_policy
from policy.engine import PolicyEngine
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


# ─── Learning patterns endpoint ────────────────────────────────────────────────

class PatternInsight(BaseModel):
    label: str
    description: str
    confidence: float  # 0-1
    evidence: int      # sample count


@router.get("/{delegate_id}/learning/patterns", response_model=list[PatternInsight])
async def get_learning_patterns(delegate_id: str):
    """Derive behavioral patterns from decision log and opportunity history."""
    from memory.graph import list_decisions, list_opportunities, list_approvals as _la
    from memory.models import ApprovalStatus as AS

    decisions = await list_decisions(delegate_id, 500)
    opps = await list_opportunities(500)
    pending = await _la(AS.PENDING)

    human_approved = [d for d in decisions if d.human_approved is True]
    human_rejected = [d for d in decisions if d.human_approved is False]
    auto_acted = [d for d in decisions if d.human_approved is None]
    scored = [o for o in opps if o.match_score > 0]

    patterns: list[PatternInsight] = []

    # Pattern: consistent rejections → delegate learning standards
    if len(human_rejected) >= 2:
        patterns.append(PatternInsight(
            label="Rejection pattern active",
            description=(
                f"{len(human_rejected)} opportunities rejected — delegate is calibrating "
                "to your quality bar"
            ),
            confidence=min(0.4 + len(human_rejected) * 0.08, 0.90),
            evidence=len(human_rejected),
        ))

    # Pattern: approvals → delegate knows what good looks like
    if len(human_approved) >= 1:
        patterns.append(PatternInsight(
            label="Approval signal established",
            description=(
                f"{len(human_approved)} item{'' if len(human_approved) == 1 else 's'} approved — "
                "delegate is learning what high-quality looks like"
            ),
            confidence=min(0.5 + len(human_approved) * 0.10, 0.95),
            evidence=len(human_approved),
        ))

    # Pattern: scoring volume → model reliability
    if len(scored) >= 5:
        avg = sum(o.match_score for o in scored) / len(scored)
        patterns.append(PatternInsight(
            label="Scoring model reliable",
            description=(
                f"{len(scored)} opportunities scored, avg match {avg:.0%} — "
                "scoring is consistent enough to trust"
            ),
            confidence=min(0.60 + len(scored) * 0.015, 0.95),
            evidence=len(scored),
        ))

    # Pattern: score drift — if approved opps have low scores, threshold may be too high
    approved_opps = [
        o for o in opps
        if any(d.action_taken.startswith("approved") and o.opportunity_id in d.action_taken
               for d in human_approved)
    ]
    if len(approved_opps) >= 3:
        avg_approved_score = sum(o.match_score for o in approved_opps) / len(approved_opps)
        if avg_approved_score < 0.55:
            patterns.append(PatternInsight(
                label="Score threshold may be high",
                description=(
                    f"Approved opportunities avg {avg_approved_score:.0%} match — "
                    "consider lowering engagement threshold in policy"
                ),
                confidence=0.70,
                evidence=len(approved_opps),
            ))

    # Pattern: pending backlog building up
    if len(pending) >= 3:
        patterns.append(PatternInsight(
            label="Approval backlog growing",
            description=(
                f"{len(pending)} items waiting for review — consider enabling "
                "auto-decline for low scores to reduce queue"
            ),
            confidence=0.99,
            evidence=len(pending),
        ))

    return patterns


# ─── Policy Simulator endpoint ─────────────────────────────────────────────────

@router.post("/{delegate_id}/policy/simulate")
async def simulate_policy(delegate_id: str, req: "SimulationRequest"):
    """Replay historical opportunities through hypothetical policy thresholds."""
    from memory.graph import list_opportunities, list_decisions
    from memory.models import SimulationRequest
    from policy.models import PolicyThresholds
    from policy.simulator import PolicySimulator

    try:
        engine = PolicyEngine(delegate_id)
    except FileNotFoundError:
        raise HTTPException(404, f"No policy found for delegate '{delegate_id}'")

    opps = await list_opportunities(500)
    decisions = await list_decisions(delegate_id, 500)

    simulator = PolicySimulator()
    result = simulator.simulate(
        opportunities=opps,
        hypothetical=PolicyThresholds(
            min_score_for_engagement=req.min_score_for_engagement,
            auto_decline_below=req.auto_decline_below,
            auto_decline_threshold=req.auto_decline_threshold,
        ),
        actual_thresholds=engine.policy.thresholds,
        decisions=decisions,
    )
    return result


# ─── Apply Learning Suggestion endpoint ────────────────────────────────────────

class ApplySuggestionRequest(BaseModel):
    type: str  # "goal_update" or "policy_update"
    field: str
    action: str = "update"  # "add", "remove", "update"
    value: str = ""


@router.post("/{delegate_id}/learning/apply-suggestion")
async def apply_suggestion(delegate_id: str, req: ApplySuggestionRequest):
    """Apply a learning suggestion to goals or policy."""
    if req.type == "goal_update":
        from memory.graph import get_career_goals, upsert_career_goals
        goals = await get_career_goals()
        field_val = getattr(goals, req.field, None)
        if isinstance(field_val, list):
            if req.action == "add" and req.value not in field_val:
                field_val.append(req.value)
            elif req.action == "remove" and req.value in field_val:
                field_val.remove(req.value)
            setattr(goals, req.field, field_val)
        elif req.action == "update":
            try:
                setattr(goals, req.field, type(field_val)(req.value) if field_val is not None else req.value)
            except (ValueError, TypeError):
                raise HTTPException(400, f"Cannot set {req.field} to {req.value}")
        await upsert_career_goals(goals)
        return {"status": "applied", "type": "goal_update", "field": req.field}

    elif req.type == "policy_update":
        from memory.graph import set_policy_override
        await set_policy_override(delegate_id, req.field, req.value)
        return {"status": "applied", "type": "policy_update", "field": req.field}

    raise HTTPException(400, f"Unknown suggestion type: {req.type}")


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

    from config.settings import settings
    pipeline = RecruiterPipeline(
        email_provider=MockEmailProvider(),
        graph=MemoryGraph(),
        event_bus=get_event_bus(),
        llm_enabled=bool(settings.openai_api_key),
    )
    ctx = await pipeline.run()
    return RunResult(
        trace_id=ctx.trace_id,
        emails_ingested=len(ctx.emails_ingested),
        opportunities_found=len(ctx.opportunities),
        events_emitted=len(ctx.events_emitted),
        errors=ctx.errors,
    )
