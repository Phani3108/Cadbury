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
    AUTO_DECLINED = "auto_declined"
    CALENDAR_BOOKED = "calendar_booked"
    CALENDAR_CANCELLED = "calendar_cancelled"
    CALENDAR_PREBLOCK_REQUESTED = "calendar_preblock_requested"
    CALENDAR_SLOTS_FOUND = "calendar_slots_found"
    CALENDAR_PROPOSED = "calendar_proposed"
    # Comms delegate
    MESSAGE_RECEIVED = "message_received"
    MESSAGE_CLASSIFIED = "message_classified"
    MESSAGE_ROUTED = "message_routed"
    MESSAGE_DRAFTED = "message_drafted"
    MESSAGE_SENT = "message_sent"
    MESSAGE_ARCHIVED = "message_archived"
    # Finance delegate
    TRANSACTION_INGESTED = "transaction_ingested"
    RECURRING_DETECTED = "recurring_detected"
    SPENDING_ALERT = "spending_alert"
    SUBSCRIPTION_FLAGGED = "subscription_flagged"
    # Shopping delegate
    PRICE_TRACKED = "price_tracked"
    PRICE_DROP = "price_drop"
    DEAL_FOUND = "deal_found"
    # Learning delegate
    SKILL_ASSESSED = "skill_assessed"
    LEARNING_PATH_CREATED = "learning_path_created"
    LEARNING_PROGRESS = "learning_progress"
    LEARNING_NUDGE = "learning_nudge"
    # Health delegate
    HEALTH_REMINDER = "health_reminder"
    HEALTH_APPOINTMENT = "health_appointment"
    HEALTH_ROUTINE_LOGGED = "health_routine_logged"
    HEALTH_ALERT = "health_alert"
    POLICY_BLOCKED = "policy_blocked"
    NOTIFICATION_CREATED = "notification_created"
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
    thread_id: Optional[str] = None
    company_enrichment: dict = Field(default_factory=dict)
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


# ─── Calendar Event ──────────────────────────────────────────────────────────

class CalendarEventStatus(StrEnum):
    PROPOSED = "proposed"
    CONFIRMED = "confirmed"
    TENTATIVE = "tentative"
    CANCELLED = "cancelled"


class CalendarEvent(BaseModel):
    event_id: str = Field(default_factory=_uid)
    opportunity_id: Optional[str] = None
    title: str
    start_at: datetime
    end_at: datetime
    attendees: list[str] = Field(default_factory=list)
    status: CalendarEventStatus = CalendarEventStatus.PROPOSED
    provider_event_id: Optional[str] = None
    delegate_id: str = "calendar"
    created_at: datetime = Field(default_factory=_now)


# ─── Notification ────────────────────────────────────────────────────────────

class NotificationType(StrEnum):
    NEW_APPROVAL = "new_approval"
    HIGH_MATCH = "high_match"
    AUTO_ACTED = "auto_acted"
    DIGEST_READY = "digest_ready"
    THRESHOLD_CROSSED = "threshold_crossed"


class Notification(BaseModel):
    notification_id: str = Field(default_factory=_uid)
    type: NotificationType
    title: str
    body: str
    link: str = ""
    read: bool = False
    created_at: datetime = Field(default_factory=_now)


# ─── Simulation Result ───────────────────────────────────────────────────────

class SimulationRequest(BaseModel):
    min_score_for_engagement: float = 0.65
    auto_decline_below: float = 0.30
    auto_decline_threshold: float = 0.25
    period_days: int = 90


# ─── Comms Models ─────────────────────────────────────────────────────────────

class MessageChannel(StrEnum):
    EMAIL = "email"
    TELEGRAM = "telegram"
    WHATSAPP = "whatsapp"
    SLACK = "slack"
    SMS = "sms"


class MessagePriority(StrEnum):
    URGENT = "urgent"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"
    SPAM = "spam"


class MessageCategory(StrEnum):
    PERSONAL = "personal"
    WORK = "work"
    TRANSACTIONAL = "transactional"
    SPAM = "spam"
    URGENT = "urgent"
    NEWSLETTER = "newsletter"


class CommsMessage(BaseModel):
    message_id: str = Field(default_factory=_uid)
    channel: MessageChannel
    sender: str
    sender_name: str = ""
    subject: str = ""
    body: str = ""
    priority: MessagePriority = MessagePriority.NORMAL
    category: MessageCategory = MessageCategory.PERSONAL
    reply_draft: Optional[str] = None
    action_taken: str = ""  # archived, replied, forwarded, escalated
    created_at: datetime = Field(default_factory=_now)


# ─── Finance Models ──────────────────────────────────────────────────────────

class TransactionCategory(StrEnum):
    SUBSCRIPTION = "subscription"
    FOOD = "food"
    TRANSPORT = "transport"
    ENTERTAINMENT = "entertainment"
    SHOPPING = "shopping"
    UTILITIES = "utilities"
    HEALTHCARE = "healthcare"
    INCOME = "income"
    TRANSFER = "transfer"
    OTHER = "other"


class Transaction(BaseModel):
    transaction_id: str = Field(default_factory=_uid)
    amount: float
    currency: str = "USD"
    merchant: str
    category: TransactionCategory = TransactionCategory.OTHER
    date: datetime = Field(default_factory=_now)
    is_recurring: bool = False
    recurrence_period_days: Optional[int] = None
    notes: str = ""


class Subscription(BaseModel):
    subscription_id: str = Field(default_factory=_uid)
    merchant: str
    amount: float
    currency: str = "USD"
    period_days: int = 30  # billing cycle
    last_charged: Optional[datetime] = None
    next_charge: Optional[datetime] = None
    status: str = "active"  # active, cancelled, flagged
    usage_rating: str = "unknown"  # high, medium, low, unused, unknown
    cancel_instructions: str = ""
    created_at: datetime = Field(default_factory=_now)


# ─── Shopping Models ─────────────────────────────────────────────────────────

class WatchItem(BaseModel):
    item_id: str = Field(default_factory=_uid)
    name: str
    target_price: Optional[float] = None
    current_price: Optional[float] = None
    url: str = ""
    retailer: str = ""
    price_history: list[dict] = Field(default_factory=list)  # [{date, price}]
    alert_on_drop: bool = True
    status: str = "watching"  # watching, purchased, removed
    created_at: datetime = Field(default_factory=_now)


# ─── Learning Models ─────────────────────────────────────────────────────────

class SkillGap(BaseModel):
    skill: str
    current_level: str = "beginner"  # beginner, intermediate, advanced
    target_level: str = "intermediate"
    priority: str = "medium"  # high, medium, low
    related_roles: list[str] = Field(default_factory=list)


class LearningPath(BaseModel):
    path_id: str = Field(default_factory=_uid)
    title: str
    skill_gaps: list[SkillGap] = Field(default_factory=list)
    resources: list[dict] = Field(default_factory=list)  # [{title, url, type, completed}]
    progress_pct: float = 0.0
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)


# ─── Health Models ────────────────────────────────────────────────────────────

class HealthRoutineType(StrEnum):
    MEDICATION = "medication"
    EXERCISE = "exercise"
    SLEEP = "sleep"
    WATER = "water"
    CUSTOM = "custom"


class HealthRoutine(BaseModel):
    routine_id: str = Field(default_factory=_uid)
    name: str
    routine_type: HealthRoutineType = HealthRoutineType.CUSTOM
    frequency: str = "daily"  # daily, weekly, as_needed
    time_of_day: str = ""  # morning, afternoon, evening, or HH:MM
    last_logged: Optional[datetime] = None
    streak_days: int = 0
    active: bool = True
    created_at: datetime = Field(default_factory=_now)


class HealthAppointment(BaseModel):
    appointment_id: str = Field(default_factory=_uid)
    title: str
    provider: str = ""  # doctor name / clinic
    appointment_type: str = ""  # checkup, dental, specialist, etc.
    scheduled_at: Optional[datetime] = None
    status: str = "scheduled"  # scheduled, completed, cancelled, overdue
    notes: str = ""
    created_at: datetime = Field(default_factory=_now)
