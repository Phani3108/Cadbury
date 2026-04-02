"""
SQLite-backed memory graph.
Stores: CareerGoals, RecruiterContact, JobOpportunity, ApprovalItem, DelegateEvent, DecisionLog.
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
    DecisionLog,
    DelegateEvent,
    JobOpportunity,
    MatchBreakdown,
    Notification,
    RecruiterContact,
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
