"""
OAuth2 Authorization Code Flow endpoints for Microsoft and Google.

Supports:
- Microsoft Graph (email + calendar) with PKCE
- Google Calendar with PKCE

Flow: Frontend redirects to /v1/auth/{provider}/login → external consent
      → redirect back to /v1/auth/{provider}/callback → tokens stored encrypted
"""
from __future__ import annotations

import hashlib
import secrets
import base64
import logging
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse

from config.settings import get_settings
from skills.auth.token_store import (
    save_tokens,
    load_tokens,
    delete_tokens,
    has_tokens,
    init_token_store,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/v1/auth", tags=["auth"])

# In-memory PKCE state (per-session). For production, store in Redis/session.
_pending_auth: dict[str, dict] = {}


# ─── Microsoft OAuth2 ───────────────────────────────────────────────────────

MS_AUTH_URL = "https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize"
MS_TOKEN_URL = "https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"
MS_SCOPES = "offline_access Mail.Read Mail.Send Calendars.ReadWrite User.Read"


def _pkce_pair() -> tuple[str, str]:
    """Generate PKCE code_verifier and code_challenge."""
    verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(verifier.encode()).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
    return verifier, challenge


@router.get("/microsoft/login")
async def microsoft_login(request: Request):
    """Redirect user to Microsoft consent screen."""
    s = get_settings()
    if not s.msgraph_client_id:
        raise HTTPException(400, "Microsoft OAuth not configured (MSGRAPH_CLIENT_ID missing)")

    verifier, challenge = _pkce_pair()
    state = secrets.token_urlsafe(32)
    _pending_auth[state] = {"verifier": verifier, "provider": "microsoft"}

    tenant = s.msgraph_tenant_id or "common"
    callback = str(request.url_for("microsoft_callback"))

    params = {
        "client_id": s.msgraph_client_id,
        "response_type": "code",
        "redirect_uri": callback,
        "scope": MS_SCOPES,
        "state": state,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
        "response_mode": "query",
    }
    return RedirectResponse(f"{MS_AUTH_URL.format(tenant=tenant)}?{urlencode(params)}")


@router.get("/microsoft/callback")
async def microsoft_callback(code: str = "", state: str = "", error: str = ""):
    """Handle Microsoft OAuth callback, exchange code for tokens."""
    if error:
        raise HTTPException(400, f"Microsoft auth error: {error}")
    if state not in _pending_auth:
        raise HTTPException(400, "Invalid or expired state parameter")

    pending = _pending_auth.pop(state)
    s = get_settings()
    tenant = s.msgraph_tenant_id or "common"
    callback_url = f"{s.frontend_url.rstrip('/')}/api/auth/microsoft/callback"

    # For local dev, use the backend URL derived from the original request
    # In production, the callback should be the backend URL registered in Azure AD
    data = {
        "client_id": s.msgraph_client_id,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": callback_url,
        "code_verifier": pending["verifier"],
    }
    # Include client_secret if set (required for web apps, not for SPA/mobile)
    if s.msgraph_client_secret:
        data["client_secret"] = s.msgraph_client_secret

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(MS_TOKEN_URL.format(tenant=tenant), data=data)

    if resp.status_code != 200:
        logger.error("Microsoft token exchange failed: %s", resp.text)
        raise HTTPException(502, "Failed to exchange authorization code")

    token_data = resp.json()
    await save_tokens("microsoft", {
        "access_token": token_data["access_token"],
        "refresh_token": token_data.get("refresh_token", ""),
        "expires_in": token_data.get("expires_in", 3600),
        "scope": token_data.get("scope", ""),
    })

    logger.info("Microsoft OAuth tokens saved successfully")
    # Redirect back to frontend settings page
    return RedirectResponse(f"{s.frontend_url}/settings?connected=microsoft")


# ─── Google OAuth2 ───────────────────────────────────────────────────────────

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_SCOPES = "https://www.googleapis.com/auth/calendar https://www.googleapis.com/auth/calendar.events"


@router.get("/google/login")
async def google_login(request: Request):
    """Redirect user to Google consent screen."""
    s = get_settings()
    if not s.google_client_id:
        raise HTTPException(400, "Google OAuth not configured (GOOGLE_CLIENT_ID missing)")

    verifier, challenge = _pkce_pair()
    state = secrets.token_urlsafe(32)
    _pending_auth[state] = {"verifier": verifier, "provider": "google"}

    callback = str(request.url_for("google_callback"))

    params = {
        "client_id": s.google_client_id,
        "response_type": "code",
        "redirect_uri": callback,
        "scope": GOOGLE_SCOPES,
        "state": state,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
        "access_type": "offline",
        "prompt": "consent",
    }
    return RedirectResponse(f"{GOOGLE_AUTH_URL}?{urlencode(params)}")


@router.get("/google/callback")
async def google_callback(code: str = "", state: str = "", error: str = ""):
    """Handle Google OAuth callback, exchange code for tokens."""
    if error:
        raise HTTPException(400, f"Google auth error: {error}")
    if state not in _pending_auth:
        raise HTTPException(400, "Invalid or expired state parameter")

    pending = _pending_auth.pop(state)
    s = get_settings()
    callback_url = str(f"{s.frontend_url.rstrip('/')}/api/auth/google/callback")

    data = {
        "client_id": s.google_client_id,
        "client_secret": s.google_client_secret,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": callback_url,
        "code_verifier": pending["verifier"],
    }

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(GOOGLE_TOKEN_URL, data=data)

    if resp.status_code != 200:
        logger.error("Google token exchange failed: %s", resp.text)
        raise HTTPException(502, "Failed to exchange authorization code")

    token_data = resp.json()
    await save_tokens("google", {
        "access_token": token_data["access_token"],
        "refresh_token": token_data.get("refresh_token", ""),
        "expires_in": token_data.get("expires_in", 3600),
        "scope": token_data.get("scope", ""),
    })

    logger.info("Google OAuth tokens saved successfully")
    return RedirectResponse(f"{s.frontend_url}/settings?connected=google")


# ─── Status & Disconnect ────────────────────────────────────────────────────

@router.get("/status")
async def auth_status():
    """Return connection status for all providers."""
    return {
        "microsoft": await has_tokens("microsoft"),
        "google": await has_tokens("google"),
    }


@router.post("/{provider}/disconnect")
async def disconnect_provider(provider: str):
    """Remove stored tokens for a provider."""
    if provider not in ("microsoft", "google"):
        raise HTTPException(400, "Unknown provider")
    removed = await delete_tokens(provider)
    return {"disconnected": removed, "provider": provider}
