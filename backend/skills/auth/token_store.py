"""
OAuth2 token store — encrypted at rest in SQLite.

Tokens are encrypted using Fernet symmetric encryption derived from
settings.secret_key. This ensures refresh tokens aren't stored in plaintext.
"""
from __future__ import annotations

import base64
import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Optional

from config.settings import get_settings
from memory.graph import db

logger = logging.getLogger(__name__)


def _derive_key() -> bytes:
    """Derive a 32-byte Fernet key from the app's secret_key."""
    secret = get_settings().secret_key.encode()
    digest = hashlib.sha256(secret).digest()
    return base64.urlsafe_b64encode(digest)


def _encrypt(plaintext: str) -> str:
    """Encrypt a string and return base64-encoded ciphertext."""
    from cryptography.fernet import Fernet
    f = Fernet(_derive_key())
    return f.encrypt(plaintext.encode()).decode()


def _decrypt(ciphertext: str) -> str:
    """Decrypt base64-encoded ciphertext to a string."""
    from cryptography.fernet import Fernet
    f = Fernet(_derive_key())
    return f.decrypt(ciphertext.encode()).decode()


async def init_token_store() -> None:
    """Create the oauth_tokens table if not exists."""
    async with db() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS oauth_tokens (
                provider    TEXT PRIMARY KEY,
                token_data  TEXT NOT NULL,
                updated_at  TEXT NOT NULL
            )
        """)
        await conn.commit()


async def save_tokens(provider: str, token_data: dict) -> None:
    """Encrypt and save OAuth tokens for a provider (e.g. 'microsoft', 'google')."""
    encrypted = _encrypt(json.dumps(token_data))
    now = datetime.now(timezone.utc).isoformat()
    async with db() as conn:
        await conn.execute(
            """
            INSERT INTO oauth_tokens (provider, token_data, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(provider) DO UPDATE SET
                token_data = excluded.token_data,
                updated_at = excluded.updated_at
            """,
            (provider, encrypted, now),
        )
        await conn.commit()
    logger.info("Saved OAuth tokens for provider=%s", provider)


async def load_tokens(provider: str) -> Optional[dict]:
    """Load and decrypt OAuth tokens for a provider. Returns None if not found."""
    async with db() as conn:
        rows = await conn.execute_fetchall(
            "SELECT token_data FROM oauth_tokens WHERE provider = ?",
            (provider,),
        )
        if not rows:
            return None
    try:
        return json.loads(_decrypt(rows[0]["token_data"]))
    except Exception:
        logger.exception("Failed to decrypt tokens for provider=%s", provider)
        return None


async def delete_tokens(provider: str) -> bool:
    """Remove stored tokens for a provider (disconnect)."""
    async with db() as conn:
        cursor = await conn.execute(
            "DELETE FROM oauth_tokens WHERE provider = ?", (provider,)
        )
        await conn.commit()
        return cursor.rowcount > 0


async def has_tokens(provider: str) -> bool:
    """Check if tokens exist for a provider."""
    async with db() as conn:
        rows = await conn.execute_fetchall(
            "SELECT 1 FROM oauth_tokens WHERE provider = ? LIMIT 1",
            (provider,),
        )
        return len(rows) > 0
