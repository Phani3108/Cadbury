"""
Allowlist — hard gate on who can trigger delegate actions.

The allowlist is a set of identifiers (emails, phone numbers, chat IDs) that
are permitted to interact with the system. It is loaded from the ALLOWLIST
environment variable (comma-separated) and persisted in SQLite for runtime
modifications via the settings UI.

The LLM cannot modify this list. Only the authenticated owner can.
"""
from __future__ import annotations

import logging
from typing import Optional

import aiosqlite

from config.settings import get_settings

logger = logging.getLogger(__name__)

_DB_PATH: Optional[str] = None


def _get_db_path() -> str:
    global _DB_PATH
    if _DB_PATH is None:
        settings = get_settings()
        _DB_PATH = settings.database_url.replace("sqlite+aiosqlite:///", "")
    return _DB_PATH


async def _ensure_table() -> None:
    async with aiosqlite.connect(_get_db_path()) as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS allowlist (
                identifier TEXT PRIMARY KEY,
                service    TEXT NOT NULL DEFAULT 'email',
                added_at   TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
        await conn.commit()


async def init_allowlist() -> None:
    """Seed allowlist from ALLOWLIST env var (comma-separated)."""
    await _ensure_table()
    settings = get_settings()
    if not settings.allowlist:
        return

    entries = [e.strip() for e in settings.allowlist.split(",") if e.strip()]
    async with aiosqlite.connect(_get_db_path()) as conn:
        for entry in entries:
            await conn.execute(
                "INSERT OR IGNORE INTO allowlist (identifier) VALUES (?)",
                (entry.lower(),),
            )
        await conn.commit()
    logger.info("Allowlist seeded with %d entries from env", len(entries))


async def is_allowed(identifier: str) -> bool:
    """Check if an identifier is in the allowlist."""
    await _ensure_table()
    async with aiosqlite.connect(_get_db_path()) as conn:
        cursor = await conn.execute(
            "SELECT 1 FROM allowlist WHERE identifier = ?",
            (identifier.lower(),),
        )
        return await cursor.fetchone() is not None


async def add_to_allowlist(identifier: str, service: str = "email") -> None:
    """Add an identifier to the allowlist. Requires authenticated owner."""
    await _ensure_table()
    async with aiosqlite.connect(_get_db_path()) as conn:
        await conn.execute(
            "INSERT OR IGNORE INTO allowlist (identifier, service) VALUES (?, ?)",
            (identifier.lower(), service),
        )
        await conn.commit()
    logger.info("Added %s to allowlist (service=%s)", identifier, service)


async def remove_from_allowlist(identifier: str) -> None:
    """Remove an identifier from the allowlist."""
    await _ensure_table()
    async with aiosqlite.connect(_get_db_path()) as conn:
        await conn.execute(
            "DELETE FROM allowlist WHERE identifier = ?",
            (identifier.lower(),),
        )
        await conn.commit()
    logger.info("Removed %s from allowlist", identifier)


async def list_allowlist() -> list[dict]:
    """Return all allowlist entries."""
    await _ensure_table()
    async with aiosqlite.connect(_get_db_path()) as conn:
        conn.row_factory = aiosqlite.Row
        cursor = await conn.execute(
            "SELECT identifier, service, added_at FROM allowlist ORDER BY added_at"
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]
