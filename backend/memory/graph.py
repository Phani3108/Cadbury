"""
SQLite-backed memory graph with three-tier knowledge system.

Tier 1: Memories — always injected into LLM context (user preferences, career goals, dealbreakers)
Tier 2: Scratchpad — titles in context, body loaded on demand (recruiter history, company notes)
Tier 3: Database — structured data (opportunities, scores, decision logs) — existing tables

Also stores: CareerGoals, RecruiterContact, JobOpportunity, ApprovalItem, DelegateEvent, DecisionLog.
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import aiosqlite

from memory.models import (
    ApprovalItem,
    ApprovalStatus,
    CalendarEvent,
    CareerGoals,
    CommsMessage,
    DecisionLog,
    DelegateEvent,
    HealthAppointment,
    HealthRoutine,
    JobOpportunity,
    LearningPath,
    MatchBreakdown,
    Notification,
    RecruiterContact,
    Subscription,
    Transaction,
    WatchItem,
)

DB_PATH = Path("data/delegates.db")


async def _get_conn() -> aiosqlite.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = await aiosqlite.connect(DB_PATH)
    conn.row_factory = aiosqlite.Row
    await conn.execute("PRAGMA journal_mode=WAL")
    await conn.execute("PRAGMA foreign_keys=ON")
    return conn


@asynccontextmanager
async def db():
    conn = await _get_conn()
    try:
        yield conn
    finally:
        await conn.close()


async def init_db() -> None:
    """Create tables if not exists."""
    async with db() as conn:
        await conn.executescript("""
            CREATE TABLE IF NOT EXISTS career_goals (
                user_id TEXT PRIMARY KEY,
                data    TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS recruiter_contacts (
                contact_id TEXT PRIMARY KEY,
                email      TEXT UNIQUE NOT NULL,
                data       TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS job_opportunities (
                opportunity_id TEXT PRIMARY KEY,
                contact_id     TEXT NOT NULL,
                company        TEXT NOT NULL,
                role           TEXT NOT NULL,
                match_score    REAL NOT NULL DEFAULT 0,
                status         TEXT NOT NULL DEFAULT 'received',
                data           TEXT NOT NULL,
                created_at     TEXT NOT NULL,
                updated_at     TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS approval_items (
                approval_id    TEXT PRIMARY KEY,
                delegate_id    TEXT NOT NULL,
                opportunity_id TEXT,
                status         TEXT NOT NULL DEFAULT 'pending',
                data           TEXT NOT NULL,
                created_at     TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS delegate_events (
                event_id    TEXT PRIMARY KEY,
                delegate_id TEXT NOT NULL,
                event_type  TEXT NOT NULL,
                timestamp   TEXT NOT NULL,
                data        TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS decision_log (
                decision_id TEXT PRIMARY KEY,
                delegate_id TEXT NOT NULL,
                event_id    TEXT NOT NULL,
                timestamp   TEXT NOT NULL,
                data        TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_approvals_status ON approval_items(status);
            CREATE INDEX IF NOT EXISTS idx_events_delegate ON delegate_events(delegate_id, timestamp);
            CREATE INDEX IF NOT EXISTS idx_opportunities_status ON job_opportunities(status);

            CREATE TABLE IF NOT EXISTS calendar_events (
                event_id       TEXT PRIMARY KEY,
                opportunity_id TEXT,
                title          TEXT NOT NULL,
                start_at       TEXT NOT NULL,
                end_at         TEXT NOT NULL,
                status         TEXT NOT NULL DEFAULT 'proposed',
                data           TEXT NOT NULL,
                created_at     TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_calendar_status ON calendar_events(status);

            CREATE TABLE IF NOT EXISTS notifications (
                notification_id TEXT PRIMARY KEY,
                type            TEXT NOT NULL,
                title           TEXT NOT NULL,
                read            INTEGER NOT NULL DEFAULT 0,
                data            TEXT NOT NULL,
                created_at      TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_notifications_read ON notifications(read);

            CREATE TABLE IF NOT EXISTS policy_overrides (
                delegate_id TEXT NOT NULL,
                key         TEXT NOT NULL,
                value       TEXT NOT NULL,
                updated_at  TEXT NOT NULL,
                PRIMARY KEY (delegate_id, key)
            );

            -- Tier 1: Memories — always injected into LLM system prompt
            CREATE TABLE IF NOT EXISTS memories (
                memory_id  TEXT PRIMARY KEY,
                content    TEXT NOT NULL,
                category   TEXT NOT NULL DEFAULT 'general',
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            -- Tier 2: Scratchpad — title injected, body loaded on demand
            CREATE TABLE IF NOT EXISTS scratchpad (
                entry_id   TEXT PRIMARY KEY,
                title      TEXT NOT NULL,
                body       TEXT NOT NULL,
                category   TEXT NOT NULL DEFAULT 'general',
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            -- Comms messages
            CREATE TABLE IF NOT EXISTS comms_messages (
                message_id TEXT PRIMARY KEY,
                channel    TEXT NOT NULL,
                sender     TEXT NOT NULL,
                priority   TEXT NOT NULL DEFAULT 'normal',
                category   TEXT NOT NULL DEFAULT 'personal',
                data       TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_comms_channel ON comms_messages(channel);
            CREATE INDEX IF NOT EXISTS idx_comms_priority ON comms_messages(priority);

            -- Finance transactions
            CREATE TABLE IF NOT EXISTS transactions (
                transaction_id TEXT PRIMARY KEY,
                merchant       TEXT NOT NULL,
                amount         REAL NOT NULL,
                category       TEXT NOT NULL DEFAULT 'other',
                is_recurring   INTEGER NOT NULL DEFAULT 0,
                data           TEXT NOT NULL,
                date           TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_tx_merchant ON transactions(merchant);

            -- Subscriptions
            CREATE TABLE IF NOT EXISTS subscriptions (
                subscription_id TEXT PRIMARY KEY,
                merchant        TEXT NOT NULL,
                amount          REAL NOT NULL,
                status          TEXT NOT NULL DEFAULT 'active',
                data            TEXT NOT NULL,
                created_at      TEXT NOT NULL
            );

            -- Shopping watch items
            CREATE TABLE IF NOT EXISTS watch_items (
                item_id    TEXT PRIMARY KEY,
                name       TEXT NOT NULL,
                status     TEXT NOT NULL DEFAULT 'watching',
                data       TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            -- Learning paths
            CREATE TABLE IF NOT EXISTS learning_paths (
                path_id    TEXT PRIMARY KEY,
                title      TEXT NOT NULL,
                data       TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            -- Health routines
            CREATE TABLE IF NOT EXISTS health_routines (
                routine_id TEXT PRIMARY KEY,
                name       TEXT NOT NULL,
                active     INTEGER NOT NULL DEFAULT 1,
                data       TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            -- Health appointments
            CREATE TABLE IF NOT EXISTS health_appointments (
                appointment_id TEXT PRIMARY KEY,
                title          TEXT NOT NULL,
                status         TEXT NOT NULL DEFAULT 'scheduled',
                scheduled_at   TEXT,
                data           TEXT NOT NULL,
                created_at     TEXT NOT NULL
            );
        """)
        # Add thread_id column if missing (migration-safe)
        try:
            await conn.execute("ALTER TABLE job_opportunities ADD COLUMN thread_id TEXT")
        except Exception:
            pass  # Column already exists
        await conn.commit()


# ─── Career Goals ─────────────────────────────────────────────────────────────

async def get_career_goals(user_id: str = "default") -> CareerGoals:
    async with db() as conn:
        row = await conn.execute_fetchall(
            "SELECT data FROM career_goals WHERE user_id = ?", (user_id,)
        )
        if row:
            return CareerGoals.model_validate_json(row[0]["data"])
        return CareerGoals(user_id=user_id)


async def upsert_career_goals(goals: CareerGoals) -> CareerGoals:
    from datetime import timezone
    goals.updated_at = datetime.now(timezone.utc)
    async with db() as conn:
        await conn.execute(
            """
            INSERT INTO career_goals(user_id, data, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET data=excluded.data, updated_at=excluded.updated_at
            """,
            (goals.user_id, goals.model_dump_json(), goals.updated_at.isoformat()),
        )
        await conn.commit()
    return goals


# ─── Recruiter Contacts ───────────────────────────────────────────────────────

async def get_or_create_contact(email: str, name: str, company: str) -> RecruiterContact:
    async with db() as conn:
        rows = await conn.execute_fetchall(
            "SELECT data FROM recruiter_contacts WHERE email = ?", (email,)
        )
        if rows:
            contact = RecruiterContact.model_validate_json(rows[0]["data"])
            contact.interaction_count += 1
            await conn.execute(
                "UPDATE recruiter_contacts SET data = ? WHERE email = ?",
                (contact.model_dump_json(), email),
            )
            await conn.commit()
            return contact

        contact = RecruiterContact(email=email, name=name, company=company)
        await conn.execute(
            "INSERT INTO recruiter_contacts(contact_id, email, data, created_at) VALUES(?,?,?,?)",
            (contact.contact_id, email, contact.model_dump_json(), contact.first_contact.isoformat()),
        )
        await conn.commit()
        return contact


# ─── Job Opportunities ────────────────────────────────────────────────────────

async def save_opportunity(opp: JobOpportunity) -> JobOpportunity:
    async with db() as conn:
        await conn.execute(
            """
            INSERT INTO job_opportunities
            (opportunity_id, contact_id, company, role, match_score, status, data, created_at, updated_at)
            VALUES (?,?,?,?,?,?,?,?,?)
            ON CONFLICT(opportunity_id) DO UPDATE SET
              match_score=excluded.match_score,
              status=excluded.status,
              data=excluded.data,
              updated_at=excluded.updated_at
            """,
            (
                opp.opportunity_id,
                opp.contact_id,
                opp.company,
                opp.role,
                opp.match_score,
                opp.status,
                opp.model_dump_json(),
                opp.created_at.isoformat(),
                opp.updated_at.isoformat(),
            ),
        )
        await conn.commit()
    return opp


async def list_opportunities(limit: int = 100) -> list[JobOpportunity]:
    async with db() as conn:
        rows = await conn.execute_fetchall(
            "SELECT data FROM job_opportunities ORDER BY created_at DESC LIMIT ?", (limit,)
        )
        return [JobOpportunity.model_validate_json(r["data"]) for r in rows]


async def get_opportunity(opportunity_id: str) -> Optional[JobOpportunity]:
    async with db() as conn:
        rows = await conn.execute_fetchall(
            "SELECT data FROM job_opportunities WHERE opportunity_id = ?", (opportunity_id,)
        )
        if rows:
            return JobOpportunity.model_validate_json(rows[0]["data"])
        return None


async def get_opportunities_batch(ids: list[str]) -> dict[str, JobOpportunity]:
    if not ids:
        return {}
    placeholders = ",".join("?" * len(ids))
    async with db() as conn:
        rows = await conn.execute_fetchall(
            f"SELECT data FROM job_opportunities WHERE opportunity_id IN ({placeholders})",
            ids,
        )
    return {
        opp.opportunity_id: opp
        for opp in (JobOpportunity.model_validate_json(r["data"]) for r in rows)
    }


# ─── Approval Items ───────────────────────────────────────────────────────────

async def save_approval(item: ApprovalItem) -> ApprovalItem:
    async with db() as conn:
        await conn.execute(
            """
            INSERT INTO approval_items(approval_id, delegate_id, opportunity_id, status, data, created_at)
            VALUES (?,?,?,?,?,?)
            ON CONFLICT(approval_id) DO UPDATE SET status=excluded.status, data=excluded.data
            """,
            (
                item.approval_id,
                item.delegate_id,
                item.opportunity_id,
                item.status,
                item.model_dump_json(),
                item.created_at.isoformat(),
            ),
        )
        await conn.commit()
    return item


async def list_approvals(status: Optional[ApprovalStatus] = None) -> list[ApprovalItem]:
    async with db() as conn:
        if status:
            rows = await conn.execute_fetchall(
                "SELECT data FROM approval_items WHERE status = ? ORDER BY created_at DESC",
                (status,),
            )
        else:
            rows = await conn.execute_fetchall(
                "SELECT data FROM approval_items ORDER BY created_at DESC"
            )
        return [ApprovalItem.model_validate_json(r["data"]) for r in rows]


async def get_approval(approval_id: str) -> Optional[ApprovalItem]:
    async with db() as conn:
        rows = await conn.execute_fetchall(
            "SELECT data FROM approval_items WHERE approval_id = ?", (approval_id,)
        )
        if rows:
            return ApprovalItem.model_validate_json(rows[0]["data"])
        return None


async def update_approval_status(approval_id: str, status: ApprovalStatus) -> Optional[ApprovalItem]:
    item = await get_approval(approval_id)
    if not item:
        return None
    item.status = status
    return await save_approval(item)


# ─── Delegate Events ──────────────────────────────────────────────────────────

async def save_event(event: DelegateEvent) -> DelegateEvent:
    async with db() as conn:
        await conn.execute(
            """
            INSERT OR IGNORE INTO delegate_events(event_id, delegate_id, event_type, timestamp, data)
            VALUES (?,?,?,?,?)
            """,
            (
                event.event_id,
                event.delegate_id,
                event.event_type,
                event.timestamp.isoformat(),
                event.model_dump_json(),
            ),
        )
        await conn.commit()
    return event


async def list_events(delegate_id: Optional[str] = None, limit: int = 100) -> list[DelegateEvent]:
    async with db() as conn:
        if delegate_id:
            rows = await conn.execute_fetchall(
                "SELECT data FROM delegate_events WHERE delegate_id = ? ORDER BY timestamp DESC LIMIT ?",
                (delegate_id, limit),
            )
        else:
            rows = await conn.execute_fetchall(
                "SELECT data FROM delegate_events ORDER BY timestamp DESC LIMIT ?", (limit,)
            )
        return [DelegateEvent.model_validate_json(r["data"]) for r in rows]


# ─── Decision Log ─────────────────────────────────────────────────────────────

async def log_decision(decision: DecisionLog) -> DecisionLog:
    async with db() as conn:
        await conn.execute(
            """
            INSERT OR IGNORE INTO decision_log(decision_id, delegate_id, event_id, timestamp, data)
            VALUES (?,?,?,?,?)
            """,
            (
                decision.decision_id,
                decision.delegate_id,
                decision.event_id,
                decision.timestamp.isoformat(),
                decision.model_dump_json(),
            ),
        )
        await conn.commit()
    return decision


async def list_decisions(delegate_id: Optional[str] = None, limit: int = 100) -> list[DecisionLog]:
    async with db() as conn:
        if delegate_id:
            rows = await conn.execute_fetchall(
                "SELECT data FROM decision_log WHERE delegate_id = ? ORDER BY timestamp DESC LIMIT ?",
                (delegate_id, limit),
            )
        else:
            rows = await conn.execute_fetchall(
                "SELECT data FROM decision_log ORDER BY timestamp DESC LIMIT ?", (limit,)
            )
        return [DecisionLog.model_validate_json(r["data"]) for r in rows]


# ─── Contacts ────────────────────────────────────────────────────────────────

async def list_contacts() -> list[RecruiterContact]:
    async with db() as conn:
        rows = await conn.execute_fetchall(
            "SELECT data FROM recruiter_contacts ORDER BY created_at DESC"
        )
        return [RecruiterContact.model_validate_json(r["data"]) for r in rows]


async def get_contact(contact_id: str) -> Optional[RecruiterContact]:
    async with db() as conn:
        rows = await conn.execute_fetchall(
            "SELECT data FROM recruiter_contacts WHERE contact_id = ?", (contact_id,)
        )
        if rows:
            return RecruiterContact.model_validate_json(rows[0]["data"])
        return None


async def update_contact(contact: RecruiterContact) -> RecruiterContact:
    async with db() as conn:
        await conn.execute(
            "UPDATE recruiter_contacts SET data = ? WHERE contact_id = ?",
            (contact.model_dump_json(), contact.contact_id),
        )
        await conn.commit()
    return contact


# ─── Thread Tracking ─────────────────────────────────────────────────────────

async def get_opportunity_by_thread(thread_id: str) -> Optional[JobOpportunity]:
    if not thread_id:
        return None
    async with db() as conn:
        rows = await conn.execute_fetchall(
            "SELECT data FROM job_opportunities WHERE json_extract(data, '$.thread_id') = ? LIMIT 1",
            (thread_id,),
        )
        if rows:
            return JobOpportunity.model_validate_json(rows[0]["data"])
        return None


# ─── Calendar Events ─────────────────────────────────────────────────────────

async def save_calendar_event(event: CalendarEvent) -> CalendarEvent:
    async with db() as conn:
        await conn.execute(
            """
            INSERT INTO calendar_events(event_id, opportunity_id, title, start_at, end_at, status, data, created_at)
            VALUES (?,?,?,?,?,?,?,?)
            ON CONFLICT(event_id) DO UPDATE SET status=excluded.status, data=excluded.data
            """,
            (
                event.event_id,
                event.opportunity_id,
                event.title,
                event.start_at.isoformat(),
                event.end_at.isoformat(),
                event.status,
                event.model_dump_json(),
                event.created_at.isoformat(),
            ),
        )
        await conn.commit()
    return event


async def list_calendar_events(status: Optional[str] = None, limit: int = 50) -> list[CalendarEvent]:
    async with db() as conn:
        if status:
            rows = await conn.execute_fetchall(
                "SELECT data FROM calendar_events WHERE status = ? ORDER BY start_at DESC LIMIT ?",
                (status, limit),
            )
        else:
            rows = await conn.execute_fetchall(
                "SELECT data FROM calendar_events ORDER BY start_at DESC LIMIT ?", (limit,)
            )
        return [CalendarEvent.model_validate_json(r["data"]) for r in rows]


async def get_calendar_event(event_id: str) -> Optional[CalendarEvent]:
    async with db() as conn:
        rows = await conn.execute_fetchall(
            "SELECT data FROM calendar_events WHERE event_id = ?", (event_id,)
        )
        if rows:
            return CalendarEvent.model_validate_json(rows[0]["data"])
        return None


async def get_calendar_events_for_opportunity(opportunity_id: str) -> list[CalendarEvent]:
    async with db() as conn:
        rows = await conn.execute_fetchall(
            "SELECT data FROM calendar_events WHERE opportunity_id = ?", (opportunity_id,)
        )
        return [CalendarEvent.model_validate_json(r["data"]) for r in rows]


# ─── Notifications ───────────────────────────────────────────────────────────

async def save_notification(notif: Notification) -> Notification:
    async with db() as conn:
        await conn.execute(
            """
            INSERT OR IGNORE INTO notifications(notification_id, type, title, read, data, created_at)
            VALUES (?,?,?,?,?,?)
            """,
            (
                notif.notification_id,
                notif.type,
                notif.title,
                int(notif.read),
                notif.model_dump_json(),
                notif.created_at.isoformat(),
            ),
        )
        await conn.commit()
    return notif


async def list_notifications(unread_only: bool = False, limit: int = 20) -> list[Notification]:
    async with db() as conn:
        if unread_only:
            rows = await conn.execute_fetchall(
                "SELECT data FROM notifications WHERE read = 0 ORDER BY created_at DESC LIMIT ?",
                (limit,),
            )
        else:
            rows = await conn.execute_fetchall(
                "SELECT data FROM notifications ORDER BY created_at DESC LIMIT ?", (limit,)
            )
        return [Notification.model_validate_json(r["data"]) for r in rows]


async def mark_notification_read(notification_id: str) -> bool:
    async with db() as conn:
        rows = await conn.execute_fetchall(
            "SELECT data FROM notifications WHERE notification_id = ?", (notification_id,)
        )
        if not rows:
            return False
        notif = Notification.model_validate_json(rows[0]["data"])
        notif.read = True
        await conn.execute(
            "UPDATE notifications SET read = 1, data = ? WHERE notification_id = ?",
            (notif.model_dump_json(), notification_id),
        )
        await conn.commit()
        return True


async def mark_all_notifications_read() -> int:
    async with db() as conn:
        # Get all unread
        rows = await conn.execute_fetchall(
            "SELECT notification_id, data FROM notifications WHERE read = 0"
        )
        for r in rows:
            notif = Notification.model_validate_json(r["data"])
            notif.read = True
            await conn.execute(
                "UPDATE notifications SET read = 1, data = ? WHERE notification_id = ?",
                (notif.model_dump_json(), notif.notification_id),
            )
        await conn.commit()
        return len(rows)


# ─── Policy Overrides ────────────────────────────────────────────────────────

async def get_policy_overrides(delegate_id: str) -> dict[str, str]:
    async with db() as conn:
        rows = await conn.execute_fetchall(
            "SELECT key, value FROM policy_overrides WHERE delegate_id = ?",
            (delegate_id,),
        )
        return {r["key"]: r["value"] for r in rows}


async def set_policy_override(delegate_id: str, key: str, value: str) -> None:
    async with db() as conn:
        await conn.execute(
            """
            INSERT INTO policy_overrides(delegate_id, key, value, updated_at)
            VALUES (?,?,?,?)
            ON CONFLICT(delegate_id, key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at
            """,
            (delegate_id, key, value, datetime.now(timezone.utc).isoformat()),
        )
        await conn.commit()


# ─── MemoryGraph class (injectable wrapper for testing / DI) ──────────────────

class MemoryGraph:
    """Thin class wrapper around module-level graph functions for dependency injection."""

    async def get_career_goals(self, user_id: str = "default") -> CareerGoals:
        return await get_career_goals(user_id)

    async def upsert_career_goals(self, goals: CareerGoals) -> CareerGoals:
        return await upsert_career_goals(goals)

    async def get_or_create_contact(
        self, email_addr: str, name: str, company: str
    ) -> RecruiterContact:
        return await get_or_create_contact(email=email_addr, name=name, company=company)

    async def save_opportunity(self, opp: JobOpportunity) -> JobOpportunity:
        return await save_opportunity(opp)

    async def list_opportunities(self, limit: int = 100) -> list[JobOpportunity]:
        return await list_opportunities(limit)

    async def get_opportunity(self, opportunity_id: str) -> Optional[JobOpportunity]:
        return await get_opportunity(opportunity_id)

    async def save_approval(self, item: ApprovalItem) -> ApprovalItem:
        return await save_approval(item)

    async def list_approvals(self, status: Optional[ApprovalStatus] = None) -> list[ApprovalItem]:
        return await list_approvals(status)

    async def get_approval(self, approval_id: str) -> Optional[ApprovalItem]:
        return await get_approval(approval_id)

    async def update_approval_status(
        self, approval_id: str, status: ApprovalStatus
    ) -> Optional[ApprovalItem]:
        return await update_approval_status(approval_id, status)

    async def save_event(self, event: DelegateEvent) -> DelegateEvent:
        return await save_event(event)

    async def list_events(
        self, delegate_id: Optional[str] = None, limit: int = 100
    ) -> list[DelegateEvent]:
        return await list_events(delegate_id, limit)

    async def log_decision(self, decision: DecisionLog) -> DecisionLog:
        return await log_decision(decision)

    async def list_decisions(
        self, delegate_id: Optional[str] = None, limit: int = 100
    ) -> list[DecisionLog]:
        return await list_decisions(delegate_id, limit)

    async def get_opportunity_by_thread(self, thread_id: str) -> Optional[JobOpportunity]:
        return await get_opportunity_by_thread(thread_id)

    async def list_contacts(self) -> list[RecruiterContact]:
        return await list_contacts()

    async def get_contact(self, contact_id: str) -> Optional[RecruiterContact]:
        return await get_contact(contact_id)

    async def update_contact(self, contact: RecruiterContact) -> RecruiterContact:
        return await update_contact(contact)

    async def save_calendar_event(self, event: CalendarEvent) -> CalendarEvent:
        return await save_calendar_event(event)

    async def list_calendar_events(self, status: Optional[str] = None, limit: int = 50) -> list[CalendarEvent]:
        return await list_calendar_events(status, limit)

    async def get_calendar_event(self, event_id: str) -> Optional[CalendarEvent]:
        return await get_calendar_event(event_id)

    async def save_notification(self, notif: Notification) -> Notification:
        return await save_notification(notif)


# ─── Comms Messages ──────────────────────────────────────────────────────────

async def save_comms_message(msg: CommsMessage) -> CommsMessage:
    async with db() as conn:
        await conn.execute(
            """INSERT INTO comms_messages(message_id, channel, sender, priority, category, data, created_at)
               VALUES (?,?,?,?,?,?,?)
               ON CONFLICT(message_id) DO UPDATE SET data=excluded.data, priority=excluded.priority, category=excluded.category""",
            (msg.message_id, msg.channel, msg.sender, msg.priority, msg.category,
             msg.model_dump_json(), msg.created_at.isoformat()),
        )
        await conn.commit()
    return msg


async def list_comms_messages(channel: Optional[str] = None, limit: int = 100) -> list[CommsMessage]:
    async with db() as conn:
        if channel:
            rows = await conn.execute_fetchall(
                "SELECT data FROM comms_messages WHERE channel = ? ORDER BY created_at DESC LIMIT ?",
                (channel, limit),
            )
        else:
            rows = await conn.execute_fetchall(
                "SELECT data FROM comms_messages ORDER BY created_at DESC LIMIT ?", (limit,)
            )
        return [CommsMessage.model_validate_json(r["data"]) for r in rows]


# ─── Finance: Transactions ───────────────────────────────────────────────────

async def save_transaction(tx: Transaction) -> Transaction:
    async with db() as conn:
        await conn.execute(
            """INSERT INTO transactions(transaction_id, merchant, amount, category, is_recurring, data, date)
               VALUES (?,?,?,?,?,?,?)
               ON CONFLICT(transaction_id) DO UPDATE SET data=excluded.data""",
            (tx.transaction_id, tx.merchant, tx.amount, tx.category,
             int(tx.is_recurring), tx.model_dump_json(), tx.date.isoformat()),
        )
        await conn.commit()
    return tx


async def list_transactions(limit: int = 200) -> list[Transaction]:
    async with db() as conn:
        rows = await conn.execute_fetchall(
            "SELECT data FROM transactions ORDER BY date DESC LIMIT ?", (limit,)
        )
        return [Transaction.model_validate_json(r["data"]) for r in rows]


# ─── Finance: Subscriptions ─────────────────────────────────────────────────

async def save_subscription(sub: Subscription) -> Subscription:
    async with db() as conn:
        await conn.execute(
            """INSERT INTO subscriptions(subscription_id, merchant, amount, status, data, created_at)
               VALUES (?,?,?,?,?,?)
               ON CONFLICT(subscription_id) DO UPDATE SET data=excluded.data, status=excluded.status""",
            (sub.subscription_id, sub.merchant, sub.amount, sub.status,
             sub.model_dump_json(), sub.created_at.isoformat()),
        )
        await conn.commit()
    return sub


async def list_subscriptions(status: Optional[str] = None) -> list[Subscription]:
    async with db() as conn:
        if status:
            rows = await conn.execute_fetchall(
                "SELECT data FROM subscriptions WHERE status = ? ORDER BY created_at DESC", (status,)
            )
        else:
            rows = await conn.execute_fetchall("SELECT data FROM subscriptions ORDER BY created_at DESC")
        return [Subscription.model_validate_json(r["data"]) for r in rows]


# ─── Shopping: Watch Items ───────────────────────────────────────────────────

async def save_watch_item(item: WatchItem) -> WatchItem:
    async with db() as conn:
        await conn.execute(
            """INSERT INTO watch_items(item_id, name, status, data, created_at)
               VALUES (?,?,?,?,?)
               ON CONFLICT(item_id) DO UPDATE SET data=excluded.data, status=excluded.status""",
            (item.item_id, item.name, item.status, item.model_dump_json(), item.created_at.isoformat()),
        )
        await conn.commit()
    return item


async def list_watch_items(status: Optional[str] = None) -> list[WatchItem]:
    async with db() as conn:
        if status:
            rows = await conn.execute_fetchall(
                "SELECT data FROM watch_items WHERE status = ? ORDER BY created_at DESC", (status,)
            )
        else:
            rows = await conn.execute_fetchall("SELECT data FROM watch_items ORDER BY created_at DESC")
        return [WatchItem.model_validate_json(r["data"]) for r in rows]


async def get_watch_item(item_id: str) -> Optional[WatchItem]:
    async with db() as conn:
        rows = await conn.execute_fetchall(
            "SELECT data FROM watch_items WHERE item_id = ?", (item_id,)
        )
        return WatchItem.model_validate_json(rows[0]["data"]) if rows else None


# ─── Learning Paths ──────────────────────────────────────────────────────────

async def save_learning_path(path: LearningPath) -> LearningPath:
    path.updated_at = datetime.now(timezone.utc)
    async with db() as conn:
        await conn.execute(
            """INSERT INTO learning_paths(path_id, title, data, created_at, updated_at)
               VALUES (?,?,?,?,?)
               ON CONFLICT(path_id) DO UPDATE SET data=excluded.data, updated_at=excluded.updated_at""",
            (path.path_id, path.title, path.model_dump_json(),
             path.created_at.isoformat(), path.updated_at.isoformat()),
        )
        await conn.commit()
    return path


async def list_learning_paths() -> list[LearningPath]:
    async with db() as conn:
        rows = await conn.execute_fetchall("SELECT data FROM learning_paths ORDER BY updated_at DESC")
        return [LearningPath.model_validate_json(r["data"]) for r in rows]


async def get_learning_path(path_id: str) -> Optional[LearningPath]:
    async with db() as conn:
        rows = await conn.execute_fetchall(
            "SELECT data FROM learning_paths WHERE path_id = ?", (path_id,)
        )
        return LearningPath.model_validate_json(rows[0]["data"]) if rows else None


# ─── Health Routines ─────────────────────────────────────────────────────────

async def save_health_routine(routine: HealthRoutine) -> HealthRoutine:
    async with db() as conn:
        await conn.execute(
            """INSERT INTO health_routines(routine_id, name, active, data, created_at)
               VALUES (?,?,?,?,?)
               ON CONFLICT(routine_id) DO UPDATE SET data=excluded.data, active=excluded.active""",
            (routine.routine_id, routine.name, int(routine.active),
             routine.model_dump_json(), routine.created_at.isoformat()),
        )
        await conn.commit()
    return routine


async def list_health_routines(active_only: bool = True) -> list[HealthRoutine]:
    async with db() as conn:
        if active_only:
            rows = await conn.execute_fetchall(
                "SELECT data FROM health_routines WHERE active = 1 ORDER BY created_at"
            )
        else:
            rows = await conn.execute_fetchall("SELECT data FROM health_routines ORDER BY created_at")
        return [HealthRoutine.model_validate_json(r["data"]) for r in rows]


# ─── Health Appointments ─────────────────────────────────────────────────────

async def save_health_appointment(apt: HealthAppointment) -> HealthAppointment:
    async with db() as conn:
        await conn.execute(
            """INSERT INTO health_appointments(appointment_id, title, status, scheduled_at, data, created_at)
               VALUES (?,?,?,?,?,?)
               ON CONFLICT(appointment_id) DO UPDATE SET data=excluded.data, status=excluded.status""",
            (apt.appointment_id, apt.title, apt.status,
             apt.scheduled_at.isoformat() if apt.scheduled_at else None,
             apt.model_dump_json(), apt.created_at.isoformat()),
        )
        await conn.commit()
    return apt


async def list_health_appointments(status: Optional[str] = None) -> list[HealthAppointment]:
    async with db() as conn:
        if status:
            rows = await conn.execute_fetchall(
                "SELECT data FROM health_appointments WHERE status = ? ORDER BY scheduled_at", (status,)
            )
        else:
            rows = await conn.execute_fetchall("SELECT data FROM health_appointments ORDER BY scheduled_at")
        return [HealthAppointment.model_validate_json(r["data"]) for r in rows]


# ─── Tier 1: Memories (always in LLM context) ─────────────────────────────────

async def save_memory(memory_id: str, content: str, category: str = "general") -> dict:
    async with db() as conn:
        now = datetime.now(timezone.utc).isoformat()
        await conn.execute(
            """
            INSERT INTO memories (memory_id, content, category, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(memory_id) DO UPDATE SET content=excluded.content, category=excluded.category, updated_at=excluded.updated_at
            """,
            (memory_id, content, category, now, now),
        )
        await conn.commit()
    return {"memory_id": memory_id, "content": content, "category": category}


async def list_memories() -> list[dict]:
    async with db() as conn:
        rows = await conn.execute_fetchall(
            "SELECT memory_id, content, category, created_at FROM memories ORDER BY created_at"
        )
        return [dict(r) for r in rows]


async def delete_memory(memory_id: str) -> None:
    async with db() as conn:
        await conn.execute("DELETE FROM memories WHERE memory_id = ?", (memory_id,))
        await conn.commit()


async def get_all_memory_text() -> str:
    """Return all memories as a single string for LLM system prompt injection."""
    memories = await list_memories()
    if not memories:
        return ""
    lines = [f"- {m['content']}" for m in memories]
    return "## User Memories (always consider these)\n" + "\n".join(lines)


# ─── Tier 2: Scratchpad (titles in context, body on demand) ───────────────────

async def save_scratchpad_entry(entry_id: str, title: str, body: str, category: str = "general") -> dict:
    async with db() as conn:
        now = datetime.now(timezone.utc).isoformat()
        await conn.execute(
            """
            INSERT INTO scratchpad (entry_id, title, body, category, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(entry_id) DO UPDATE SET title=excluded.title, body=excluded.body, category=excluded.category, updated_at=excluded.updated_at
            """,
            (entry_id, title, body, category, now, now),
        )
        await conn.commit()
    return {"entry_id": entry_id, "title": title, "category": category}


async def list_scratchpad_titles() -> list[dict]:
    """Return only titles (for LLM context injection — body loaded on demand)."""
    async with db() as conn:
        rows = await conn.execute_fetchall(
            "SELECT entry_id, title, category, updated_at FROM scratchpad ORDER BY updated_at DESC"
        )
        return [dict(r) for r in rows]


async def get_scratchpad_entry(entry_id: str) -> Optional[dict]:
    """Load full entry body (on-demand, not always in context)."""
    async with db() as conn:
        rows = await conn.execute_fetchall(
            "SELECT entry_id, title, body, category, created_at, updated_at FROM scratchpad WHERE entry_id = ?",
            (entry_id,),
        )
        if rows:
            return dict(rows[0])
        return None


async def delete_scratchpad_entry(entry_id: str) -> None:
    async with db() as conn:
        await conn.execute("DELETE FROM scratchpad WHERE entry_id = ?", (entry_id,))
        await conn.commit()


async def get_scratchpad_titles_text() -> str:
    """Return scratchpad titles as text for LLM context — body NOT included."""
    titles = await list_scratchpad_titles()
    if not titles:
        return ""
    lines = [f"- [{t['entry_id']}] {t['title']}" for t in titles]
    return "## Available Scratchpad Topics (ask to load details)\n" + "\n".join(lines)
