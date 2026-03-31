"""
Core domain models for the memory graph.
These are Pydantic models used across API, DB, and business logic.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional
from enum import StrEnum

from pydantic import BaseModel, Field


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _uid() -> str:
    return str(uuid.uuid4())


# ─── Enums ────────────────────────────────────────────────────────────────────

class EventType(StrEnum):
    EMAIL_RECEIVED = "email_received"
    OPPORTUNITY_EXTRACTED = "opportunity_extracted"
    OPPORTUNITY_SCORED = "opportunity_scored"
    DRAFT_CREATED = "draft_created"
    APPROVAL_REQUESTED = "approval_requested"
    HUMAN_APPROVED = "human_approved"
    HUMAN_REJECTED = "human_rejected"
    RESPONSE_SENT = "response_sent"
    CALENDAR_BOOKED = "calendar_booked"
    POLICY_BLOCKED = "policy_blocked"
    ERROR = "error"


class ApprovalStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    SKIPPED = "skipped"
    EXPIRED = "expired"


class OpportunityStatus(StrEnum):
    RECEIVED = "received"
    EXTRACTED = "extracted"
    SCORED = "scored"
    DRAFT_CREATED = "draft_created"
    APPROVAL_PENDING = "approval_pending"
    RESPONDED = "responded"
    REJECTED = "rejected"
    SCHEDULED = "scheduled"


class RemotePolicy(StrEnum):
    REMOTE = "remote"
    HYBRID = "hybrid"
    ONSITE = "onsite"
    UNKNOWN = "unknown"


class WorkStyle(StrEnum):
    REMOTE = "remote"
    HYBRID = "hybrid"
    ONSITE = "onsite"
    ANY = "any"


class CommunicationTone(StrEnum):
    PROFESSIONAL = "professional"
    CASUAL = "casual"
    FORMAL = "formal"


# ─── Career Goals ─────────────────────────────────────────────────────────────

class CareerGoals(BaseModel):
    user_id: str = "default"
    target_roles: list[str] = Field(default_factory=list)
    min_comp_usd: int = 0
    preferred_locations: list[str] = Field(default_factory=list)
    open_to_relocation: bool = False
    work_style: WorkStyle = WorkStyle.REMOTE
    must_have_criteria: list[str] = Field(default_factory=list)
    dealbreakers: list[str] = Field(default_factory=list)
    company_stages: list[str] = Field(default_factory=list)
    preferred_industries: list[str] = Field(default_factory=list)
    avoid_companies: list[str] = Field(default_factory=list)
    comp_includes_equity: bool = True
    comp_includes_bonus: bool = True
    communication_tone: CommunicationTone = CommunicationTone.PROFESSIONAL
    updated_at: datetime = Field(default_factory=_now)


class CareerGoalsUpdate(BaseModel):
    target_roles: Optional[list[str]] = None
    min_comp_usd: Optional[int] = None
    preferred_locations: Optional[list[str]] = None
    open_to_relocation: Optional[bool] = None
    work_style: Optional[WorkStyle] = None
    must_have_criteria: Optional[list[str]] = None
    dealbreakers: Optional[list[str]] = None
    company_stages: Optional[list[str]] = None
    preferred_industries: Optional[list[str]] = None
    avoid_companies: Optional[list[str]] = None
    comp_includes_equity: Optional[bool] = None
    comp_includes_bonus: Optional[bool] = None
    communication_tone: Optional[CommunicationTone] = None


# ─── Recruiter Contact ────────────────────────────────────────────────────────

class RecruiterContact(BaseModel):
    contact_id: str = Field(default_factory=_uid)
    name: str
    email: str
    company: str
    title: str = ""
    first_contact: datetime = Field(default_factory=_now)
    interaction_count: int = 0
    trust_score: float = 0.5  # 0-1


# ─── Match Breakdown ──────────────────────────────────────────────────────────

class MatchBreakdown(BaseModel):
    role: float = 0.0       # 0-1
    comp: float = 0.0       # 0-1
    location: float = 0.0   # 0-1
    criteria: float = 0.0   # 0-1
    company: float = 0.0    # 0-1


# ─── Job Opportunity ──────────────────────────────────────────────────────────

class JobOpportunity(BaseModel):
    opportunity_id: str = Field(default_factory=_uid)
    contact_id: str
    company: str
    role: str
    comp_range_min: Optional[int] = None
    comp_range_max: Optional[int] = None
    location: str = ""
    remote_policy: RemotePolicy = RemotePolicy.UNKNOWN
    equity: Optional[str] = None
    jd_summary: Optional[str] = None
    jd_text: Optional[str] = None
    match_score: float = 0.0
    match_breakdown: MatchBreakdown = Field(default_factory=MatchBreakdown)
    status: OpportunityStatus = OpportunityStatus.RECEIVED
    email_subject: Optional[str] = None
    email_id: Optional[str] = None
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)


# ─── Approval Item ────────────────────────────────────────────────────────────

class ApprovalItem(BaseModel):
    approval_id: str = Field(default_factory=_uid)
    delegate_id: str
    event_id: str
    opportunity_id: Optional[str] = None
    action: str
    action_label: str
    context_summary: str
    draft_content: Optional[str] = None
    risk_score: float = 0.0
    reasoning: str = ""
    policy_check: dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=_now)
    expires_at: Optional[datetime] = None
    status: ApprovalStatus = ApprovalStatus.PENDING


class ApprovalAction(BaseModel):
    draft_content: Optional[str] = None
    reason: Optional[str] = None


# ─── Delegate Event ───────────────────────────────────────────────────────────

class DelegateEvent(BaseModel):
    event_id: str = Field(default_factory=_uid)
    delegate_id: str
    event_type: EventType
    timestamp: datetime = Field(default_factory=_now)
    payload: dict = Field(default_factory=dict)
    parent_event_id: Optional[str] = None
    trace_id: Optional[str] = None
    risk_score: float = 0.0
    requires_approval: bool = False
    summary: str = ""
    reasoning: Optional[str] = None
    policy_rules_checked: list[str] = Field(default_factory=list)


# ─── Decision Log ─────────────────────────────────────────────────────────────

class DecisionLog(BaseModel):
    decision_id: str = Field(default_factory=_uid)
    delegate_id: str
    event_id: str
    action_taken: str
    reasoning: str
    policy_check: dict = Field(default_factory=dict)
    human_approved: Optional[bool] = None
    outcome: Optional[str] = None
    timestamp: datetime = Field(default_factory=_now)
