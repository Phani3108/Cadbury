"""initial schema — all 21 tables from db/models.py

For EXISTING SQLite databases the legacy init_db() already created most tables.
This migration uses ``op.create_table(..., if_not_exists=True)`` safety and
skips no-op type changes so it works on both fresh PostgreSQL and existing
SQLite databases.

Revision ID: 0bb44fd43b18
Revises:
Create Date: 2026-04-10 15:02:00.953337
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect as sa_inspect


revision: str = "0bb44fd43b18"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(name: str) -> bool:
    """Check if a table already exists (handles legacy SQLite DBs)."""
    conn = op.get_bind()
    insp = sa_inspect(conn)
    return name in insp.get_table_names()


def _index_exists(name: str) -> bool:
    conn = op.get_bind()
    # Works for both SQLite and PostgreSQL
    if conn.dialect.name == "sqlite":
        result = conn.execute(
            sa.text("SELECT 1 FROM sqlite_master WHERE type='index' AND name=:n"),
            {"n": name},
        )
        return result.fetchone() is not None
    result = conn.execute(
        sa.text("SELECT 1 FROM pg_indexes WHERE indexname=:n"),
        {"n": name},
    )
    return result.fetchone() is not None


def _create_table_if_not_exists(name, *columns):
    if not _table_exists(name):
        op.create_table(name, *columns)


def _create_index_if_not_exists(idx_name, table, columns, **kw):
    if not _index_exists(idx_name):
        op.create_index(idx_name, table, columns, **kw)


def upgrade() -> None:
    # ── Legacy tables (may already exist in SQLite) ───────────────────────

    _create_table_if_not_exists("career_goals",
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("data", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("user_id"),
    )

    _create_table_if_not_exists("recruiter_contacts",
        sa.Column("contact_id", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("data", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("contact_id"),
        sa.UniqueConstraint("email"),
    )

    _create_table_if_not_exists("job_opportunities",
        sa.Column("opportunity_id", sa.String(), nullable=False),
        sa.Column("contact_id", sa.String(), nullable=False),
        sa.Column("company", sa.String(), nullable=False),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("match_score", sa.Float(), server_default="0"),
        sa.Column("status", sa.String(), server_default="'received'"),
        sa.Column("thread_id", sa.String(), nullable=True),
        sa.Column("data", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("opportunity_id"),
    )
    _create_index_if_not_exists("idx_opportunities_status", "job_opportunities", ["status"])

    _create_table_if_not_exists("approval_items",
        sa.Column("approval_id", sa.String(), nullable=False),
        sa.Column("delegate_id", sa.String(), nullable=False),
        sa.Column("opportunity_id", sa.String(), nullable=True),
        sa.Column("status", sa.String(), server_default="'pending'"),
        sa.Column("data", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("approval_id"),
    )
    _create_index_if_not_exists("idx_approvals_status", "approval_items", ["status"])

    _create_table_if_not_exists("delegate_events",
        sa.Column("event_id", sa.String(), nullable=False),
        sa.Column("delegate_id", sa.String(), nullable=False),
        sa.Column("event_type", sa.String(), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.Column("data", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("event_id"),
    )
    _create_index_if_not_exists("idx_events_delegate", "delegate_events", ["delegate_id", "timestamp"])

    _create_table_if_not_exists("decision_log",
        sa.Column("decision_id", sa.String(), nullable=False),
        sa.Column("delegate_id", sa.String(), nullable=False),
        sa.Column("event_id", sa.String(), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.Column("data", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("decision_id"),
    )

    _create_table_if_not_exists("calendar_events",
        sa.Column("event_id", sa.String(), nullable=False),
        sa.Column("opportunity_id", sa.String(), nullable=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(), server_default="'proposed'"),
        sa.Column("data", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("event_id"),
    )
    _create_index_if_not_exists("idx_calendar_status", "calendar_events", ["status"])

    _create_table_if_not_exists("notifications",
        sa.Column("notification_id", sa.String(), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("severity", sa.String(), server_default="'info'"),
        sa.Column("read", sa.Boolean(), server_default="0"),
        sa.Column("archived", sa.Boolean(), server_default="0"),
        sa.Column("source_delegate_id", sa.String(), nullable=True),
        sa.Column("data", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("notification_id"),
    )
    _create_index_if_not_exists("idx_notifications_read", "notifications", ["read"])
    _create_index_if_not_exists("idx_notifications_severity", "notifications", ["severity"])

    _create_table_if_not_exists("policy_overrides",
        sa.Column("delegate_id", sa.String(), nullable=False),
        sa.Column("key", sa.String(), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("delegate_id", "key"),
    )

    _create_table_if_not_exists("memories",
        sa.Column("memory_id", sa.String(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("category", sa.String(), server_default="'general'"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("memory_id"),
    )

    _create_table_if_not_exists("scratchpad",
        sa.Column("entry_id", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("category", sa.String(), server_default="'general'"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("entry_id"),
    )

    _create_table_if_not_exists("comms_messages",
        sa.Column("message_id", sa.String(), nullable=False),
        sa.Column("channel", sa.String(), nullable=False),
        sa.Column("sender", sa.String(), nullable=False),
        sa.Column("priority", sa.String(), server_default="'normal'"),
        sa.Column("category", sa.String(), server_default="'personal'"),
        sa.Column("data", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("message_id"),
    )
    _create_index_if_not_exists("idx_comms_channel", "comms_messages", ["channel"])
    _create_index_if_not_exists("idx_comms_priority", "comms_messages", ["priority"])

    _create_table_if_not_exists("transactions",
        sa.Column("transaction_id", sa.String(), nullable=False),
        sa.Column("merchant", sa.String(), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("category", sa.String(), server_default="'other'"),
        sa.Column("is_recurring", sa.Boolean(), server_default="0"),
        sa.Column("data", sa.Text(), nullable=False),
        sa.Column("date", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("transaction_id"),
    )
    _create_index_if_not_exists("idx_tx_merchant", "transactions", ["merchant"])

    _create_table_if_not_exists("subscriptions",
        sa.Column("subscription_id", sa.String(), nullable=False),
        sa.Column("merchant", sa.String(), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("status", sa.String(), server_default="'active'"),
        sa.Column("data", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("subscription_id"),
    )

    _create_table_if_not_exists("watch_items",
        sa.Column("item_id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("status", sa.String(), server_default="'watching'"),
        sa.Column("data", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("item_id"),
    )

    _create_table_if_not_exists("learning_paths",
        sa.Column("path_id", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("data", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("path_id"),
    )

    _create_table_if_not_exists("health_routines",
        sa.Column("routine_id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("active", sa.Boolean(), server_default="1"),
        sa.Column("data", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("routine_id"),
    )

    _create_table_if_not_exists("health_appointments",
        sa.Column("appointment_id", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("status", sa.String(), server_default="'scheduled'"),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("data", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("appointment_id"),
    )

    # ── New tables (A3 pipeline runs, B5 chat) ────────────────────────────

    _create_table_if_not_exists("pipeline_runs",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("delegate_id", sa.String(), nullable=False),
        sa.Column("trace_id", sa.String(), nullable=False),
        sa.Column("status", sa.String(), server_default="'running'"),
        sa.Column("stage", sa.String(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    _create_index_if_not_exists("idx_pipeline_delegate", "pipeline_runs", ["delegate_id", "started_at"])
    _create_index_if_not_exists("idx_pipeline_status", "pipeline_runs", ["status"])

    _create_table_if_not_exists("chat_sessions",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("delegate_id", sa.String(), nullable=False),
        sa.Column("status", sa.String(), server_default="'active'"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    _create_index_if_not_exists("idx_chat_delegate", "chat_sessions", ["delegate_id", "status"])

    _create_table_if_not_exists("chat_messages",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("session_id", sa.String(), nullable=False),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    _create_index_if_not_exists("idx_chat_msg_session", "chat_messages", ["session_id", "created_at"])

    # ── Backfill columns on legacy tables ─────────────────────────────────
    # thread_id on job_opportunities (was added via ALTER TABLE in old init_db)
    conn = op.get_bind()
    insp = sa_inspect(conn)
    if _table_exists("job_opportunities"):
        cols = [c["name"] for c in insp.get_columns("job_opportunities")]
        if "thread_id" not in cols:
            op.add_column("job_opportunities", sa.Column("thread_id", sa.String(), nullable=True))
    # severity + archived + source_delegate_id on notifications (new columns)
    if _table_exists("notifications"):
        cols = [c["name"] for c in insp.get_columns("notifications")]
        if "severity" not in cols:
            op.add_column("notifications", sa.Column("severity", sa.String(), server_default="'info'"))
        if "archived" not in cols:
            op.add_column("notifications", sa.Column("archived", sa.Boolean(), server_default="0"))
        if "source_delegate_id" not in cols:
            op.add_column("notifications", sa.Column("source_delegate_id", sa.String(), nullable=True))


def downgrade() -> None:
    # Drop new tables only — legacy tables remain for backward compat
    for idx in ("idx_chat_msg_session", "idx_chat_delegate", "idx_pipeline_status", "idx_pipeline_delegate"):
        op.drop_index(idx, table_name=idx.replace("idx_", "").split("_")[0] + "_runs" if "pipeline" in idx else "chat_sessions" if "chat_delegate" in idx else "chat_messages")
    op.drop_table("chat_messages")
    op.drop_table("chat_sessions")
    op.drop_table("pipeline_runs")
