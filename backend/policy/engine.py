"""PolicyEngine — evaluates actions against DelegationPolicy boundaries."""
from __future__ import annotations

from policy.loader import load_policy
from policy.models import DelegationPolicy, TrustZone


class PolicyEngine:
    """Evaluates whether a delegate action can proceed automatically or needs approval."""

    def __init__(self, delegate_id: str):
        self.delegate_id = delegate_id
        self._policy: DelegationPolicy | None = None

    @property
    def policy(self) -> DelegationPolicy:
        if self._policy is None:
            self._policy = load_policy(self.delegate_id)
        return self._policy

    def check(self, action: str, score: float = 0.0) -> TrustZone:
        """
        Determine trust zone for an action.

        Returns:
            "auto"   — proceed without human approval
            "review" — create ApprovalItem, wait for human
            "block"  — refuse action entirely
        """
        permission = self.policy.get_action(action)
        if permission is None:
            return "block"  # unknown action → block

        if permission.auto_approve:
            return "auto"

        if self.policy.requires_approval(action):
            return "review"

        return permission.zone

    def can_auto_act(self, action: str, score: float = 0.0) -> bool:
        return self.check(action, score) == "auto"

    def should_block(self, action: str, score: float = 0.0) -> bool:
        return self.check(action, score) == "block"

    def get_response_type(self, score: float) -> str:
        """Map a match score to the appropriate response type for drafting."""
        thresholds = self.policy.thresholds
        if score >= thresholds.min_score_for_engagement:
            return "engage"
        elif score < thresholds.auto_decline_below:
            return "decline"
        else:
            return "hold"
