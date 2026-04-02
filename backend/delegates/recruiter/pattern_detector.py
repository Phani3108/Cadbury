"""
Pattern Detector — analyzes decision history to find actionable behavioral patterns.
Used by the Learning System (Sprint 7) to suggest goal/policy changes.
"""
from __future__ import annotations

import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Optional

from memory.models import CareerGoals, JobOpportunity, DecisionLog

# ─── Thresholds ──────────────────────────────────────────────────────────────

_SECTOR_REJECTION_THRESHOLD = 0.80  # keyword must appear in >80% of rejections
_SECTOR_MIN_SAMPLES = 5
_COMP_DRIFT_FACTOR = 1.25           # approved avg must exceed floor by 25%
_COMP_MIN_SAMPLES = 3
_RECRUITER_MIN_SAMPLES = 3
_DEFAULT_MIN_SCORE_FOR_ENGAGEMENT = 0.65
_BACKLOG_THRESHOLD = 5
_KEYWORD_MIN_LENGTH = 3             # ignore very short tokens


# ─── Data classes ────────────────────────────────────────────────────────────

@dataclass
class GoalSuggestion:
    """Suggested change to CareerGoals."""
    field: str          # e.g. "dealbreakers", "min_comp_usd"
    action: str         # "add", "remove", "update"
    value: str          # the value to add/update
    reason: str


@dataclass
class PolicySuggestion:
    """Suggested change to policy thresholds."""
    field: str          # e.g. "min_score_for_engagement"
    new_value: float
    reason: str


@dataclass
class PatternInsight:
    """A detected behavioral pattern with an optional suggested action."""
    pattern_type: str       # sector_rejection, comp_drift, recruiter_quality, score_calibration, backlog
    label: str
    description: str
    confidence: float       # 0.0-1.0
    evidence_count: int
    suggested_action: Optional[GoalSuggestion | PolicySuggestion] = None


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _opp_map(opportunities: list[JobOpportunity]) -> dict[str, JobOpportunity]:
    """Map opportunity_id -> JobOpportunity for fast lookup."""
    return {o.opportunity_id: o for o in opportunities}


def _split_decisions(
    decisions: list[DecisionLog],
    opp_lookup: dict[str, JobOpportunity],
) -> tuple[list[JobOpportunity], list[JobOpportunity], list[DecisionLog]]:
    """Split into (approved_opps, rejected_opps, pending_decisions)."""
    approved: list[JobOpportunity] = []
    rejected: list[JobOpportunity] = []
    pending: list[DecisionLog] = []

    for d in decisions:
        # Try to find the opportunity referenced in action_taken.
        matched_opp: Optional[JobOpportunity] = None
        for oid, opp in opp_lookup.items():
            if oid in d.action_taken:
                matched_opp = opp
                break

        if d.human_approved is True and matched_opp is not None:
            approved.append(matched_opp)
        elif d.human_approved is False and matched_opp is not None:
            rejected.append(matched_opp)
        elif d.human_approved is None:
            pending.append(d)

    return approved, rejected, pending


def _extract_keywords(text: str) -> list[str]:
    """Extract lowercased alphabetic tokens of reasonable length."""
    tokens = re.findall(r"[a-zA-Z]+", text.lower())
    return [t for t in tokens if len(t) >= _KEYWORD_MIN_LENGTH]


# ─── Detector ────────────────────────────────────────────────────────────────

class PatternDetector:
    """Analyzes decision log and opportunity history for patterns."""

    def analyze(
        self,
        opportunities: list[JobOpportunity],
        decisions: list[DecisionLog],
        current_goals: CareerGoals,
    ) -> list[PatternInsight]:
        """
        Run all pattern detectors and return insights sorted by confidence
        (descending).
        """
        opp_lookup = _opp_map(opportunities)
        approved, rejected, pending = _split_decisions(decisions, opp_lookup)

        insights: list[PatternInsight] = []
        insights.extend(self._detect_sector_rejection(rejected, current_goals))
        insights.extend(self._detect_comp_drift(approved, current_goals))
        insights.extend(self._detect_recruiter_quality(opportunities, decisions, opp_lookup))
        insights.extend(self._detect_score_calibration(approved))
        insights.extend(self._detect_backlog(pending))

        insights.sort(key=lambda i: i.confidence, reverse=True)
        return insights

    # ── 1. Sector rejection ──────────────────────────────────────────────────

    def _detect_sector_rejection(
        self,
        rejected: list[JobOpportunity],
        goals: CareerGoals,
    ) -> list[PatternInsight]:
        if len(rejected) < _SECTOR_MIN_SAMPLES:
            return []

        # Collect keyword frequencies from jd_summary and company fields.
        keyword_counts: Counter[str] = Counter()
        for opp in rejected:
            seen: set[str] = set()
            text = " ".join(filter(None, [opp.jd_summary, opp.company]))
            for kw in _extract_keywords(text):
                if kw not in seen:
                    keyword_counts[kw] += 1
                    seen.add(kw)

        total = len(rejected)
        existing_dealbreakers = {db.lower() for db in goals.dealbreakers}
        insights: list[PatternInsight] = []

        for kw, count in keyword_counts.most_common():
            rate = count / total
            if rate <= _SECTOR_REJECTION_THRESHOLD:
                break  # sorted descending, no more will qualify
            if kw in existing_dealbreakers:
                continue
            confidence = min(1.0, rate * (count / _SECTOR_MIN_SAMPLES))
            insights.append(
                PatternInsight(
                    pattern_type="sector_rejection",
                    label=f"Frequent rejection keyword: '{kw}'",
                    description=(
                        f"The keyword '{kw}' appears in {count}/{total} "
                        f"({rate:.0%}) of rejected opportunities."
                    ),
                    confidence=round(confidence, 3),
                    evidence_count=count,
                    suggested_action=GoalSuggestion(
                        field="dealbreakers",
                        action="add",
                        value=kw,
                        reason=f"'{kw}' appears in {rate:.0%} of rejected opportunities",
                    ),
                )
            )

        return insights

    # ── 2. Comp threshold drift ──────────────────────────────────────────────

    def _detect_comp_drift(
        self,
        approved: list[JobOpportunity],
        goals: CareerGoals,
    ) -> list[PatternInsight]:
        if goals.min_comp_usd <= 0:
            return []

        comps = [
            o.comp_range_min
            for o in approved
            if o.comp_range_min is not None and o.comp_range_min > 0
        ]
        if len(comps) < _COMP_MIN_SAMPLES:
            return []

        avg_comp = sum(comps) / len(comps)
        floor = goals.min_comp_usd

        if avg_comp < floor * _COMP_DRIFT_FACTOR:
            return []

        suggested_floor = int(avg_comp * 0.9)  # 90% of observed average
        drift_ratio = avg_comp / floor
        confidence = min(1.0, 0.5 + (drift_ratio - _COMP_DRIFT_FACTOR) * 0.5)

        return [
            PatternInsight(
                pattern_type="comp_drift",
                label="Compensation floor may be too low",
                description=(
                    f"Approved opportunities average ${avg_comp:,.0f} comp, "
                    f"which is {drift_ratio:.1f}x the current floor of "
                    f"${floor:,}."
                ),
                confidence=round(confidence, 3),
                evidence_count=len(comps),
                suggested_action=GoalSuggestion(
                    field="min_comp_usd",
                    action="update",
                    value=str(suggested_floor),
                    reason=(
                        f"Approved opportunities average ${avg_comp:,.0f}, "
                        f"suggesting the floor of ${floor:,} is too conservative"
                    ),
                ),
            )
        ]

    # ── 3. Recruiter quality ─────────────────────────────────────────────────

    def _detect_recruiter_quality(
        self,
        opportunities: list[JobOpportunity],
        decisions: list[DecisionLog],
        opp_lookup: dict[str, JobOpportunity],
    ) -> list[PatternInsight]:
        # Group opportunities by contact_id.
        by_recruiter: dict[str, list[JobOpportunity]] = defaultdict(list)
        for opp in opportunities:
            by_recruiter[opp.contact_id].append(opp)

        # Build a set of rejected opportunity_ids.
        rejected_ids: set[str] = set()
        for d in decisions:
            if d.human_approved is False:
                for oid in opp_lookup:
                    if oid in d.action_taken:
                        rejected_ids.add(oid)

        insights: list[PatternInsight] = []

        for contact_id, opps in by_recruiter.items():
            if len(opps) < _RECRUITER_MIN_SAMPLES:
                continue
            opp_ids = {o.opportunity_id for o in opps}
            rejected_count = len(opp_ids & rejected_ids)
            if rejected_count < len(opps):
                continue  # not 100% reject rate

            # All opportunities from this recruiter were rejected.
            company = opps[0].company
            confidence = min(1.0, 0.7 + 0.1 * (len(opps) - _RECRUITER_MIN_SAMPLES))

            insights.append(
                PatternInsight(
                    pattern_type="recruiter_quality",
                    label=f"Low-quality recruiter: {company}",
                    description=(
                        f"All {len(opps)} opportunities from recruiter "
                        f"(contact {contact_id}, company '{company}') were rejected."
                    ),
                    confidence=round(confidence, 3),
                    evidence_count=len(opps),
                    suggested_action=GoalSuggestion(
                        field="avoid_companies",
                        action="add",
                        value=company,
                        reason=(
                            f"100% rejection rate across {len(opps)} "
                            f"opportunities from '{company}'"
                        ),
                    ),
                )
            )

        return insights

    # ── 4. Score calibration drift ───────────────────────────────────────────

    def _detect_score_calibration(
        self,
        approved: list[JobOpportunity],
    ) -> list[PatternInsight]:
        if len(approved) < _COMP_MIN_SAMPLES:
            return []

        threshold = _DEFAULT_MIN_SCORE_FOR_ENGAGEMENT
        below = [o for o in approved if o.match_score < threshold]

        if not below:
            return []

        below_rate = len(below) / len(approved)
        if below_rate < 0.3:
            # Not enough approvals below threshold to be meaningful.
            return []

        avg_below = sum(o.match_score for o in below) / len(below)
        suggested = round(avg_below - 0.05, 2)  # small buffer below observed avg
        suggested = max(0.0, min(1.0, suggested))
        confidence = min(1.0, 0.5 + below_rate)

        return [
            PatternInsight(
                pattern_type="score_calibration",
                label="Match-score threshold may be too high",
                description=(
                    f"{len(below)}/{len(approved)} approved opportunities "
                    f"({below_rate:.0%}) scored below the engagement threshold "
                    f"of {threshold}. Their average score is {avg_below:.2f}."
                ),
                confidence=round(confidence, 3),
                evidence_count=len(below),
                suggested_action=PolicySuggestion(
                    field="min_score_for_engagement",
                    new_value=suggested,
                    reason=(
                        f"{below_rate:.0%} of approved opps score below "
                        f"{threshold}; lowering to {suggested} would capture them"
                    ),
                ),
            )
        ]

    # ── 5. Approval backlog ──────────────────────────────────────────────────

    def _detect_backlog(
        self,
        pending: list[DecisionLog],
    ) -> list[PatternInsight]:
        if len(pending) <= _BACKLOG_THRESHOLD:
            return []

        confidence = min(1.0, 0.5 + 0.1 * (len(pending) - _BACKLOG_THRESHOLD))

        return [
            PatternInsight(
                pattern_type="backlog",
                label="Approval backlog detected",
                description=(
                    f"There are {len(pending)} pending decisions awaiting "
                    f"review, exceeding the threshold of {_BACKLOG_THRESHOLD}."
                ),
                confidence=round(confidence, 3),
                evidence_count=len(pending),
                suggested_action=PolicySuggestion(
                    field="auto_decline_below_score",
                    new_value=0.3,
                    reason=(
                        f"{len(pending)} unresolved decisions; enabling "
                        f"auto-decline for scores below 0.3 would reduce backlog"
                    ),
                ),
            )
        ]
