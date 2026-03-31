"""Pure-Python job opportunity scorer — no LLM, deterministic, testable."""
from __future__ import annotations

from memory.models import CareerGoals, JobOpportunity, MatchBreakdown, RemotePolicy, WorkStyle

# Scoring weights (must sum to 1.0)
W_COMP = 0.35
W_ROLE = 0.30
W_LOCATION = 0.20
W_CRITERIA = 0.15


def score_comp(opportunity: JobOpportunity, goals: CareerGoals) -> float:
    """Score compensation alignment. 1.0 = at or above min, 0.0 = unknown/far below.

    Goals store comp in USD. Opportunities store comp in INR (extracted from email).
    Convert goal to INR at 83x for comparison.
    """
    if not goals.min_comp_usd:
        return 0.5  # no preference set — neutral

    min_comp_inr = goals.min_comp_usd * 83  # USD → INR

    # Use midpoint of range if available, otherwise max, otherwise min
    offer: float | None = None
    if opportunity.comp_range_max and opportunity.comp_range_min:
        offer = (opportunity.comp_range_min + opportunity.comp_range_max) / 2
    elif opportunity.comp_range_max:
        offer = float(opportunity.comp_range_max)
    elif opportunity.comp_range_min:
        offer = float(opportunity.comp_range_min)

    if offer is None:
        return 0.3  # comp not disclosed — penalise slightly

    ratio = offer / min_comp_inr
    # 1.0 at 100% of min, 0.0 at 50% or below, linear interpolation
    return max(0.0, min(1.0, (ratio - 0.5) / 0.5))


def score_role(opportunity: JobOpportunity, goals: CareerGoals) -> float:
    """Score role fit based on title overlap with target roles and dealbreakers."""
    if not goals.target_roles:
        return 0.5

    role_lower = opportunity.role.lower()

    # Hard block on dealbreakers
    for db in goals.dealbreakers:
        if db.lower() in role_lower or db.lower() in (opportunity.jd_summary or "").lower():
            return 0.0

    # Check target role match
    best = 0.0
    for target in goals.target_roles:
        target_lower = target.lower()
        # Exact substring match
        if target_lower in role_lower or role_lower in target_lower:
            best = 1.0
            break
        # Word overlap
        target_words = set(target_lower.split())
        role_words = set(role_lower.split())
        overlap = len(target_words & role_words)
        if overlap:
            score = overlap / max(len(target_words), len(role_words))
            best = max(best, score)

    return best


def score_location(opportunity: JobOpportunity, goals: CareerGoals) -> float:
    """Score location/remote-policy alignment."""
    opp_remote = opportunity.remote_policy
    opp_location = (opportunity.location or "").lower()

    # If candidate wants remote and role is fully remote → perfect
    if goals.work_style == WorkStyle.REMOTE:
        if opp_remote == RemotePolicy.REMOTE:
            return 1.0
        elif opp_remote == RemotePolicy.HYBRID:
            return 0.5
        else:
            # onsite — check if preferred location matches
            for loc in goals.preferred_locations:
                if loc.lower() in opp_location:
                    return 0.4  # onsite but in preferred city
            return 0.1

    if goals.work_style == WorkStyle.HYBRID:
        if opp_remote in (RemotePolicy.REMOTE, RemotePolicy.HYBRID):
            return 1.0
        # onsite — check city
        for loc in goals.preferred_locations:
            if loc.lower() in opp_location:
                return 0.7
        return 0.3

    # Candidate wants onsite or no preference
    if goals.preferred_locations:
        for loc in goals.preferred_locations:
            if loc.lower() in opp_location:
                return 1.0
        if goals.open_to_relocation:
            return 0.7
        return 0.3

    return 0.6  # no location preference set — mostly neutral


def score_criteria(opportunity: JobOpportunity, goals: CareerGoals) -> float:
    """Score must-have criteria overlap with JD summary and role."""
    if not goals.must_have_criteria:
        return 0.5

    text = f"{opportunity.role} {opportunity.jd_summary or ''} {opportunity.company or ''}".lower()
    hits = sum(1 for c in goals.must_have_criteria if c.lower() in text)
    return hits / len(goals.must_have_criteria)


def score(opportunity: JobOpportunity, goals: CareerGoals) -> tuple[float, MatchBreakdown]:
    """
    Score a job opportunity against career goals.

    Dealbreakers are hard blockers — if any dealbreaker is triggered, overall = 0.0.

    Returns:
        (overall_score, breakdown) where overall_score is 0.0–1.0
    """
    # Check dealbreakers first — hard block
    text = f"{opportunity.role} {opportunity.jd_summary or ''} {opportunity.company or ''}".lower()
    for db in goals.dealbreakers:
        if db.lower() in text:
            return 0.0, MatchBreakdown(role=0.0, comp=0.0, location=0.0, criteria=0.0, company=0.0)

    comp = score_comp(opportunity, goals)
    role = score_role(opportunity, goals)
    location = score_location(opportunity, goals)
    criteria = score_criteria(opportunity, goals)

    overall = (
        W_COMP * comp
        + W_ROLE * role
        + W_LOCATION * location
        + W_CRITERIA * criteria
    )

    breakdown = MatchBreakdown(
        role=round(role, 3),
        comp=round(comp, 3),
        location=round(location, 3),
        criteria=round(criteria, 3),
        company=0.5,  # placeholder — company scoring in Phase 2
    )

    return round(overall, 3), breakdown
