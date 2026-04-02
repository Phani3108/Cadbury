"""Pydantic models for delegation policies."""
from __future__ import annotations

from typing import Literal
from pydantic import BaseModel

TrustZone = Literal["auto", "review", "block"]


class RiskBoundary(BaseModel):
    max_financial_commitment: float = 0.0
    max_calendar_commitment_hours: float = 2.0
    max_autonomy_score: float = 0.6


class PolicyThresholds(BaseModel):
    min_score_for_engagement: float = 0.65
    auto_decline_below: float = 0.30
    auto_decline_threshold: float = 0.25  # Below this, auto-decline without human review


class ActionPermission(BaseModel):
    action: str
    action_label: str = ""
    auto_approve: bool = False
    zone: TrustZone = "review"


class DelegationPolicy(BaseModel):
    version: int = 1
    delegate_id: str
    risk_boundary: RiskBoundary = RiskBoundary()
    thresholds: PolicyThresholds = PolicyThresholds()
    allowed_actions: list[ActionPermission] = []
    approval_required_for: list[str] = []

    def get_action(self, action: str) -> ActionPermission | None:
        for a in self.allowed_actions:
            if a.action == action:
                return a
        return None

    def requires_approval(self, action: str) -> bool:
        return action in self.approval_required_for

    def get_zone_for_score(self, score: float) -> TrustZone:
        """Determine trust zone based on opportunity match score."""
        if score < self.thresholds.auto_decline_threshold:
            return "auto"     # Very low match — auto-decline without human review
        if score >= self.thresholds.min_score_for_engagement:
            return "review"   # High match — draft engage reply, needs approval
        elif score < self.thresholds.auto_decline_below:
            return "review"   # Low match — draft decline, needs approval
        else:
            return "review"   # Middle ground — request info, needs approval
