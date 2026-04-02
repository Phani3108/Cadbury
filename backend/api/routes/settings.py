"""
Settings API — manage integration credentials and configuration.
Stores overrides in SQLite so they persist across restarts.
"""
from __future__ import annotations
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
import aiosqlite
from config.settings import settings

router = APIRouter(prefix="/v1/settings", tags=["settings"])

# ── DB helpers ──────────────────────────────────────────────
DB_PATH = settings.database_url.replace("sqlite+aiosqlite:///", "")

async def _ensure_table():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS settings_overrides (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT DEFAULT (datetime('now'))
            )
        """)
        await db.commit()

async def _get_override(key: str) -> Optional[str]:
    await _ensure_table()
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT value FROM settings_overrides WHERE key = ?", (key,))
        row = await cursor.fetchone()
        return row[0] if row else None

async def _set_override(key: str, value: str):
    await _ensure_table()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO settings_overrides (key, value, updated_at)
            VALUES (?, ?, datetime('now'))
            ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at
        """, (key, value))
        await db.commit()

async def _delete_override(key: str):
    await _ensure_table()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM settings_overrides WHERE key = ?", (key,))
        await db.commit()

def _effective(key: str, override: Optional[str], env_val: str) -> str:
    """Return override if set, else env value."""
    return override if override else env_val

def _mask(value: str) -> str:
    """Mask a secret, showing last 4 chars."""
    if not value or len(value) < 8:
        return "••••" if value else ""
    return "••••••••" + value[-4:]


# ── Models ──────────────────────────────────────────────────

class IntegrationStatus(BaseModel):
    key: str
    label: str
    description: str
    configured: bool
    masked_value: str  # e.g. "••••••••sk-4f"
    source: str  # "env" | "override" | "none"
    required: bool
    category: str

class SettingsOverview(BaseModel):
    integrations: list[IntegrationStatus]

class UpdateSettingRequest(BaseModel):
    key: str
    value: str

class UpdateSettingResponse(BaseModel):
    key: str
    success: bool
    masked_value: str

class ConnectionTestResult(BaseModel):
    key: str
    success: bool
    message: str


# ── Integration definitions ─────────────────────────────────

INTEGRATIONS = [
    {
        "key": "openai_api_key",
        "label": "OpenAI API Key",
        "description": "Powers LLM extraction, scoring explanations, and draft generation. Get your key at platform.openai.com.",
        "required": True,
        "category": "ai",
    },
    {
        "key": "openai_model_cheap",
        "label": "OpenAI Model (Fast)",
        "description": "Model used for extraction and quick tasks. Default: gpt-4o-mini",
        "required": False,
        "category": "ai",
    },
    {
        "key": "openai_model_heavy",
        "label": "OpenAI Model (Heavy)",
        "description": "Model used for complex scoring and drafting. Default: gpt-4o",
        "required": False,
        "category": "ai",
    },
    {
        "key": "msgraph_tenant_id",
        "label": "Microsoft 365 Tenant ID",
        "description": "Azure AD tenant ID for email integration. Found in Azure Portal → App registrations.",
        "required": False,
        "category": "email",
    },
    {
        "key": "msgraph_client_id",
        "label": "Microsoft 365 Client ID",
        "description": "Application (client) ID from your Azure AD app registration.",
        "required": False,
        "category": "email",
    },
    {
        "key": "msgraph_client_secret",
        "label": "Microsoft 365 Client Secret",
        "description": "Client secret for MS Graph API authentication.",
        "required": False,
        "category": "email",
    },
    {
        "key": "msgraph_user_email",
        "label": "Microsoft 365 Email Address",
        "description": "The email mailbox to monitor for recruiter messages.",
        "required": False,
        "category": "email",
    },
    {
        "key": "apollo_api_key",
        "label": "Apollo.io API Key",
        "description": "Enriches company data (employee count, funding, industry). Optional — JD parsing and Wikipedia work without it.",
        "required": False,
        "category": "enrichment",
    },
    {
        "key": "redis_url",
        "label": "Redis URL",
        "description": "Redis connection for event streaming. Default: redis://localhost:6379",
        "required": False,
        "category": "infrastructure",
    },
    {
        "key": "email_poll_interval_seconds",
        "label": "Email Poll Interval",
        "description": "How often (in seconds) the recruiter pipeline checks for new emails. Default: 900 (15 minutes).",
        "required": False,
        "category": "general",
    },
    {
        "key": "calendar_preblock_threshold",
        "label": "Calendar Pre-block Threshold",
        "description": "Score above which the recruiter delegate automatically requests a calendar hold. Default: 0.80",
        "required": False,
        "category": "general",
    },
]


# ── Endpoints ───────────────────────────────────────────────

@router.get("", response_model=SettingsOverview)
async def get_settings():
    """Return all integration settings with masked values and status."""
    results = []
    for integ in INTEGRATIONS:
        key = integ["key"]
        env_val = getattr(settings, key, "")
        override = await _get_override(key)
        effective = _effective(key, override, str(env_val))

        is_secret = "key" in key.lower() or "secret" in key.lower() or "password" in key.lower()
        masked = _mask(effective) if is_secret else effective

        source = "override" if override else ("env" if env_val else "none")

        results.append(IntegrationStatus(
            key=key,
            label=integ["label"],
            description=integ["description"],
            configured=bool(effective),
            masked_value=masked,
            source=source,
            required=integ["required"],
            category=integ["category"],
        ))

    return SettingsOverview(integrations=results)


@router.put("")
async def update_setting(req: UpdateSettingRequest) -> UpdateSettingResponse:
    """Save or update a setting override."""
    valid_keys = {i["key"] for i in INTEGRATIONS}
    if req.key not in valid_keys:
        from fastapi import HTTPException
        raise HTTPException(400, f"Unknown setting key: {req.key}")

    if req.value.strip():
        await _set_override(req.key, req.value.strip())
    else:
        await _delete_override(req.key)

    effective = req.value.strip() or str(getattr(settings, req.key, ""))
    is_secret = "key" in req.key.lower() or "secret" in req.key.lower()
    masked = _mask(effective) if is_secret else effective

    return UpdateSettingResponse(key=req.key, success=True, masked_value=masked)


@router.delete("/{key}")
async def delete_setting(key: str):
    """Remove a setting override, reverting to env/default value."""
    await _delete_override(key)
    return {"key": key, "deleted": True}


@router.post("/test/{key}", response_model=ConnectionTestResult)
async def test_connection(key: str):
    """Test if an integration is working."""
    if key == "openai_api_key":
        override = await _get_override("openai_api_key")
        api_key = override or settings.openai_api_key
        if not api_key:
            return ConnectionTestResult(key=key, success=False, message="No API key configured")
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    "https://api.openai.com/v1/models",
                    headers={"Authorization": f"Bearer {api_key}"},
                    timeout=10.0,
                )
                if resp.status_code == 200:
                    return ConnectionTestResult(key=key, success=True, message="Connected to OpenAI successfully")
                else:
                    return ConnectionTestResult(key=key, success=False, message=f"OpenAI returned status {resp.status_code}")
        except Exception as e:
            return ConnectionTestResult(key=key, success=False, message=f"Connection failed: {str(e)}")

    elif key == "msgraph_client_id":
        override_tid = await _get_override("msgraph_tenant_id") or settings.msgraph_tenant_id
        override_cid = await _get_override("msgraph_client_id") or settings.msgraph_client_id
        override_cs = await _get_override("msgraph_client_secret") or settings.msgraph_client_secret
        if not all([override_tid, override_cid, override_cs]):
            return ConnectionTestResult(key=key, success=False, message="Tenant ID, Client ID, and Client Secret are all required")
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"https://login.microsoftonline.com/{override_tid}/oauth2/v2.0/token",
                    data={
                        "client_id": override_cid,
                        "client_secret": override_cs,
                        "scope": "https://graph.microsoft.com/.default",
                        "grant_type": "client_credentials",
                    },
                    timeout=10.0,
                )
                if resp.status_code == 200:
                    return ConnectionTestResult(key=key, success=True, message="Microsoft 365 authentication successful")
                else:
                    return ConnectionTestResult(key=key, success=False, message=f"Auth failed: {resp.json().get('error_description', 'Unknown error')}")
        except Exception as e:
            return ConnectionTestResult(key=key, success=False, message=f"Connection failed: {str(e)}")

    elif key == "apollo_api_key":
        override = await _get_override("apollo_api_key") or settings.apollo_api_key
        if not override:
            return ConnectionTestResult(key=key, success=False, message="No API key configured")
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    "https://api.apollo.io/api/v1/auth/health",
                    headers={"X-Api-Key": override},
                    timeout=10.0,
                )
                if resp.status_code == 200:
                    return ConnectionTestResult(key=key, success=True, message="Apollo.io connection successful")
                else:
                    return ConnectionTestResult(key=key, success=False, message=f"Apollo returned status {resp.status_code}")
        except Exception as e:
            return ConnectionTestResult(key=key, success=False, message=f"Connection failed: {str(e)}")

    elif key == "redis_url":
        redis_url = await _get_override("redis_url") or settings.redis_url
        try:
            import redis.asyncio as aioredis
            r = aioredis.from_url(redis_url)
            await r.ping()
            await r.aclose()
            return ConnectionTestResult(key=key, success=True, message="Redis connection successful")
        except Exception as e:
            return ConnectionTestResult(key=key, success=False, message=f"Redis connection failed: {str(e)}")

    else:
        return ConnectionTestResult(key=key, success=False, message="Connection test not available for this setting")
