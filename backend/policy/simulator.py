"""
Policy Simulator -- replay historical opportunities through hypothetical policy settings.

Answers the question: "What would have happened with these policy thresholds?"

Inspired by MiroFish's sandbox concept, this engine lets users experiment with
threshold changes before committing them, by showing concrete before/after
impacts on real historical data.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from memory.models import DecisionLog, JobOpportunity
from policy.models import PolicyThresholds

# Average minutes a human spends reviewing one opportunity.
_MINUTES_PER_REVIEW = 5.0


# ---------------------------------------------------------------------------
# Result data classes
# ---------------------------------------------------------------------------

@dataclass
class OutcomeChange:
    """One opportunity whose outcome would differ under the hypothetical policy."""

    opportunity_id: str
    company: str
    role: str
    match_score: float
    actual_action: str       # what actually happened
    simulated_action: str    # what would happen under new thresholds
    reason: str              # human-readable explanation


@dataclass
class SimulationResult:
    """Aggregate result of replaying opportunities through hypothetical policy."""

    period_days: int
    total_opportunities: int
    would_auto_decline: int
    would_engage: int
    would_hold: int
    would_review: int
    changed_outcomes: list[OutcomeChange] = field(default_factory=list)
    time_saved_hours: float = 0.0
    approval_reduction_pct: float = 0.0   # % fewer items needing review


# ---------------------------------------------------------------------------
# Simulator
# ---------------------------------------------------------------------------

class PolicySimulator:
    """Replays historical opportunity data through hypothetical thresholds.

    Usage::

        sim = PolicySimulator()
        result = sim.simulate(
            opportunities=past_opps,
            hypothetical=PolicyThresholds(min_score_for_engagement=0.70,
                                         auto_decline_below=0.35),
            actual_thresholds=current_policy.thresholds,
            decisions=past_decisions,
        )
        print(result.changed_outcomes)
    """

    # ----- public helpers --------------------------------------------------

    @staticmethod
    def auto_decline_threshold(thresholds: PolicyThresholds) -> float:
        """Return the auto-decline cutoff from the given thresholds."""
        return thresholds.auto_decline_below

    # ----- core simulation -------------------------------------------------

    def simulate(
        self,
        opportunities: list[JobOpportunity],
        hypothetical: PolicyThresholds,
        actual_thresholds: PolicyThresholds,
        decisions: list[DecisionLog],
    ) -> SimulationResult:
        """Replay *opportunities* through *hypothetical* thresholds and compare
        against the *actual_thresholds* that were in effect when the decisions
        were originally made.

        Parameters
        ----------
        opportunities:
            Historical ``JobOpportunity`` records to replay.
        hypothetical:
            The "what-if" thresholds the user wants to evaluate.
        actual_thresholds:
            The thresholds that were active when the opportunities were
            originally processed.
        decisions:
            Historical ``DecisionLog`` entries (used for enrichment /
            cross-referencing; keyed by ``event_id``).

        Returns
        -------
        SimulationResult
            Aggregated metrics and a list of individual outcome changes.
        """
        # Build a lookup from opportunity_id -> decision for quick access.
        # DecisionLog does not carry opportunity_id directly, but the
        # event_id often corresponds; callers should ensure alignment.
        _decisions_by_event: dict[str, DecisionLog] = {
            d.event_id: d for d in decisions
        }

        changed_outcomes: list[OutcomeChange] = []
        would_auto_decline = 0
        would_engage = 0
        would_hold = 0

        for opp in opportunities:
            score = opp.match_score

            simulated = self._classify(score, hypothetical)
            actual = self._classify(score, actual_thresholds)

            # Tally simulated buckets
            if simulated == "auto_decline":
                would_auto_decline += 1
            elif simulated == "engage":
                would_engage += 1
            else:
                would_hold += 1

            # Record changes
            if simulated != actual:
                reason = self._explain_change(
                    score, actual, simulated, actual_thresholds, hypothetical,
                )
                changed_outcomes.append(
                    OutcomeChange(
                        opportunity_id=opp.opportunity_id,
                        company=opp.company,
                        role=opp.role,
                        match_score=score,
                        actual_action=actual,
                        simulated_action=simulated,
                        reason=reason,
                    )
                )

        total = len(opportunities)
        would_review = would_engage + would_hold

        # Items that required review under the *actual* policy.
        actual_review = sum(
            1
            for opp in opportunities
            if self._classify(opp.match_score, actual_thresholds) != "auto_decline"
        )

        # Time saved: each auto-declined item no longer needs human review.
        time_saved_hours = would_auto_decline * (_MINUTES_PER_REVIEW / 60.0)

        # Approval-queue reduction percentage.
        if actual_review > 0:
            approval_reduction_pct = round(
                (1.0 - would_review / actual_review) * 100.0, 2,
            )
        else:
            approval_reduction_pct = 0.0

        # Period calculation: span between earliest and latest opportunity.
        period_days = self._compute_period_days(opportunities)

        return SimulationResult(
            period_days=period_days,
            total_opportunities=total,
            would_auto_decline=would_auto_decline,
            would_engage=would_engage,
            would_hold=would_hold,
            would_review=would_review,
            changed_outcomes=changed_outcomes,
            time_saved_hours=round(time_saved_hours, 2),
            approval_reduction_pct=approval_reduction_pct,
        )

    # ----- private helpers -------------------------------------------------

    @staticmethod
    def _classify(score: float, thresholds: PolicyThresholds) -> str:
        """Classify an opportunity score into an action bucket.

        Returns one of ``"engage"``, ``"auto_decline"``, or ``"hold"``.
        """
        if score >= thresholds.min_score_for_engagement:
            return "engage"
        if score < thresholds.auto_decline_below:
            return "auto_decline"
        return "hold"

    @staticmethod
    def _explain_change(
        score: float,
        actual: str,
        simulated: str,
        actual_thresholds: PolicyThresholds,
        hypothetical: PolicyThresholds,
    ) -> str:
        """Return a human-readable sentence explaining why the outcome changed."""
        parts: list[str] = [
            f"Score {score:.2f} was '{actual}' under actual thresholds "
            f"(engage >= {actual_thresholds.min_score_for_engagement}, "
            f"decline < {actual_thresholds.auto_decline_below})",
            f"but would be '{simulated}' under hypothetical thresholds "
            f"(engage >= {hypothetical.min_score_for_engagement}, "
            f"decline < {hypothetical.auto_decline_below}).",
        ]
        return " ".join(parts)

    @staticmethod
    def _compute_period_days(opportunities: list[JobOpportunity]) -> int:
        """Compute the calendar-day span covered by the given opportunities."""
        if not opportunities:
            return 0
        dates = [opp.created_at for opp in opportunities]
        delta = max(dates) - min(dates)
        # Always report at least 1 day when there are opportunities.
        return max(delta.days, 1) if len(opportunities) > 1 else 1
