"""
SQLAlchemy ORM models — single source of truth for the database schema.
All tables previously defined inline in graph.py init_db() are now here.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


def utcnow():
    return datetime.now(timezone.utc)


# ─── Career Goals ─────────────────────────────────────────────────────────────

class CareerGoalsRow(Base):
    __tablename__ = "career_goals"
    user_id: Mapped[str] = mapped_column(String, primary_key=True)
    data: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


# ─── Recruiter Contacts ──────────────────────────────────────────────────────

class RecruiterContactRow(Base):
    __tablename__ = "recruiter_contacts"
    contact_id: Mapped[str] = mapped_column(String, primary_key=True)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    data: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


# ─── Job Opportunities ───────────────────────────────────────────────────────

class JobOpportunityRow(Base):
    __tablename__ = "job_opportunities"
    opportunity_id: Mapped[str] = mapped_column(String, primary_key=True)
    contact_id: Mapped[str] = mapped_column(String, nullable=False)
    company: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[str] = mapped_column(String, nullable=False)
    match_score: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String, default="received")
    thread_id: Mapped[str | None] = mapped_column(String, nullable=True)
    data: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    __table_args__ = (
        Index("idx_opportunities_status", "status"),
    )


# ─── Approval Items ──────────────────────────────────────────────────────────

class ApprovalItemRow(Base):
    __tablename__ = "approval_items"
    approval_id: Mapped[str] = mapped_column(String, primary_key=True)
    delegate_id: Mapped[str] = mapped_column(String, nullable=False)
    opportunity_id: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, default="pending")
    data: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    __table_args__ = (
        Index("idx_approvals_status", "status"),
    )


# ─── Delegate Events ─────────────────────────────────────────────────────────

class DelegateEventRow(Base):
    __tablename__ = "delegate_events"
    event_id: Mapped[str] = mapped_column(String, primary_key=True)
    delegate_id: Mapped[str] = mapped_column(String, nullable=False)
    event_type: Mapped[str] = mapped_column(String, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    data: Mapped[str] = mapped_column(Text, nullable=False)

    __table_args__ = (
        Index("idx_events_delegate", "delegate_id", "timestamp"),
    )


# ─── Decision Log ────────────────────────────────────────────────────────────

class DecisionLogRow(Base):
    __tablename__ = "decision_log"
    decision_id: Mapped[str] = mapped_column(String, primary_key=True)
    delegate_id: Mapped[str] = mapped_column(String, nullable=False)
    event_id: Mapped[str] = mapped_column(String, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    data: Mapped[str] = mapped_column(Text, nullable=False)


# ─── Calendar Events ─────────────────────────────────────────────────────────

class CalendarEventRow(Base):
    __tablename__ = "calendar_events"
    event_id: Mapped[str] = mapped_column(String, primary_key=True)
    opportunity_id: Mapped[str | None] = mapped_column(String, nullable=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String, default="proposed")
    data: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    __table_args__ = (
        Index("idx_calendar_status", "status"),
    )


# ─── Notifications ───────────────────────────────────────────────────────────

class NotificationRow(Base):
    __tablename__ = "notifications"
    notification_id: Mapped[str] = mapped_column(String, primary_key=True)
    type: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    severity: Mapped[str] = mapped_column(String, default="info")  # action_required | attention | info
    read: Mapped[bool] = mapped_column(Boolean, default=False)
    archived: Mapped[bool] = mapped_column(Boolean, default=False)
    source_delegate_id: Mapped[str | None] = mapped_column(String, nullable=True)
    data: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    __table_args__ = (
        Index("idx_notifications_read", "read"),
        Index("idx_notifications_severity", "severity"),
    )


# ─── Policy Overrides ────────────────────────────────────────────────────────

class PolicyOverrideRow(Base):
    __tablename__ = "policy_overrides"
    delegate_id: Mapped[str] = mapped_column(String, primary_key=True)
    key: Mapped[str] = mapped_column(String, primary_key=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


# ─── Tier 1: Memories ────────────────────────────────────────────────────────

class MemoryRow(Base):
    __tablename__ = "memories"
    memory_id: Mapped[str] = mapped_column(String, primary_key=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String, default="general")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


# ─── Tier 2: Scratchpad ──────────────────────────────────────────────────────

class ScratchpadRow(Base):
    __tablename__ = "scratchpad"
    entry_id: Mapped[str] = mapped_column(String, primary_key=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String, default="general")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


# ─── Comms Messages ──────────────────────────────────────────────────────────

class CommsMessageRow(Base):
    __tablename__ = "comms_messages"
    message_id: Mapped[str] = mapped_column(String, primary_key=True)
    channel: Mapped[str] = mapped_column(String, nullable=False)
    sender: Mapped[str] = mapped_column(String, nullable=False)
    priority: Mapped[str] = mapped_column(String, default="normal")
    category: Mapped[str] = mapped_column(String, default="personal")
    data: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    __table_args__ = (
        Index("idx_comms_channel", "channel"),
        Index("idx_comms_priority", "priority"),
    )


# ─── Finance: Transactions ───────────────────────────────────────────────────

class TransactionRow(Base):
    __tablename__ = "transactions"
    transaction_id: Mapped[str] = mapped_column(String, primary_key=True)
    merchant: Mapped[str] = mapped_column(String, nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    category: Mapped[str] = mapped_column(String, default="other")
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False)
    data: Mapped[str] = mapped_column(Text, nullable=False)
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("idx_tx_merchant", "merchant"),
    )


# ─── Finance: Subscriptions ──────────────────────────────────────────────────

class SubscriptionRow(Base):
    __tablename__ = "subscriptions"
    subscription_id: Mapped[str] = mapped_column(String, primary_key=True)
    merchant: Mapped[str] = mapped_column(String, nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String, default="active")
    data: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


# ─── Shopping: Watch Items ───────────────────────────────────────────────────

class WatchItemRow(Base):
    __tablename__ = "watch_items"
    item_id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, default="watching")
    data: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


# ─── Learning Paths ──────────────────────────────────────────────────────────

class LearningPathRow(Base):
    __tablename__ = "learning_paths"
    path_id: Mapped[str] = mapped_column(String, primary_key=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    data: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


# ─── Health Routines ─────────────────────────────────────────────────────────

class HealthRoutineRow(Base):
    __tablename__ = "health_routines"
    routine_id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    data: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


# ─── Health Appointments ─────────────────────────────────────────────────────

class HealthAppointmentRow(Base):
    __tablename__ = "health_appointments"
    appointment_id: Mapped[str] = mapped_column(String, primary_key=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, default="scheduled")
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    data: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


# ─── Pipeline Runs (A3: execution tracking) ──────────────────────────────────

class PipelineRunRow(Base):
    __tablename__ = "pipeline_runs"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    delegate_id: Mapped[str] = mapped_column(String, nullable=False)
    trace_id: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, default="running")  # running | completed | failed
    stage: Mapped[str | None] = mapped_column(String, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("idx_pipeline_delegate", "delegate_id", "started_at"),
        Index("idx_pipeline_status", "status"),
    )


# ─── Chat Sessions (B5: agent chat) ──────────────────────────────────────────

class ChatSessionRow(Base):
    __tablename__ = "chat_sessions"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    delegate_id: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, default="active")  # active | archived
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    __table_args__ = (
        Index("idx_chat_delegate", "delegate_id", "status"),
    )


class ChatMessageRow(Base):
    __tablename__ = "chat_messages"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    session_id: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[str] = mapped_column(String, nullable=False)  # user | assistant
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    __table_args__ = (
        Index("idx_chat_msg_session", "session_id", "created_at"),
    )
