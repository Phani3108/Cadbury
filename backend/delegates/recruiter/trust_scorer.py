"""
Recruiter Trust Scorer — quality scoring for incoming recruiters.
Tracks: opportunity match quality, comp disclosure rate, user approval rate.
"""
from __future__ import annotations

from memory.models import RecruiterContact, JobOpportunity, DecisionLog

# Minimum opportunities required before we move away from the neutral score.
_MIN_SAMPLE_SIZE = 2

# Weight allocation for the three scoring factors.
_W_MATCH = 0.4
_W_COMP = 0.3
_W_APPROVAL = 0.3


def _filter_opportunities(
    contact: RecruiterContact,
    opportunities: list[JobOpportunity],
) -> list[JobOpportunity]:
    """Return only opportunities belonging to *contact*."""
    return [o for o in opportunities if o.contact_id == contact.contact_id]


def _filter_decisions(
    opp_ids: set[str],
    decisions: list[DecisionLog],
) -> list[DecisionLog]:
    """Return decisions whose ``action_taken`` references one of *opp_ids*."""
    return [d for d in decisions if any(oid in d.action_taken for oid in opp_ids)]


def _avg_match_score(opps: list[JobOpportunity]) -> float:
    """Average ``match_score`` across opportunities, or 0.0 if empty."""
    if not opps:
        return 0.0
    return sum(o.match_score for o in opps) / len(opps)


def _comp_disclosure_rate(opps: list[JobOpportunity]) -> float:
    """Fraction of opportunities that include compensation information."""
    if not opps:
        return 0.0
    disclosed = sum(
        1 for o in opps if o.comp_range_min is not None or o.comp_range_max is not None
    )
    return disclosed / len(opps)


def _approval_rate(
    opps: list[JobOpportunity],
    decisions: list[DecisionLog],
) -> float:
    """Fraction of this recruiter's opportunities the user approved."""
    if not opps:
        return 0.0
    opp_ids = {o.opportunity_id for o in opps}
    relevant = _filter_decisions(opp_ids, decisions)
    if not relevant:
        return 0.0
    approved = sum(1 for d in relevant if d.human_approved is True)
    return approved / len(relevant)


def compute_trust_score(
    contact: RecruiterContact,
    opportunities: list[JobOpportunity],
    decisions: list[DecisionLog],
) -> float:
    """
    Compute a trust score (0.0-1.0) for a recruiter contact.

    Factors:
    - avg_match_score: average match score of their opportunities (weight: 0.4)
    - comp_disclosure_rate: fraction of opps with comp info (weight: 0.3)
    - approval_rate: fraction of opps the user approved (weight: 0.3)

    Returns 0.5 (neutral) if insufficient data (fewer than 2 opportunities).
    """
    contact_opps = _filter_opportunities(contact, opportunities)

    if len(contact_opps) < _MIN_SAMPLE_SIZE:
        return 0.5

    avg_match = _avg_match_score(contact_opps)
    comp_rate = _comp_disclosure_rate(contact_opps)
    approve_rate = _approval_rate(contact_opps, decisions)

    score = (_W_MATCH * avg_match) + (_W_COMP * comp_rate) + (_W_APPROVAL * approve_rate)

    # Clamp to [0.0, 1.0] for safety.
    return max(0.0, min(1.0, score))
