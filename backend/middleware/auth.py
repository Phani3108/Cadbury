"""
Authentication middleware — API key-based auth on all endpoints.

All endpoints require a valid API key in the Authorization header (Bearer token)
except explicitly whitelisted public routes (health check, SSE events).
"""
from __future__ import annotations

import secrets
from typing import Callable

from fastapi import Request, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from config.settings import get_settings

_bearer_scheme = HTTPBearer(auto_error=False)

# Routes that do NOT require authentication
PUBLIC_ROUTES: set[str] = {
    "/health",
    "/docs",
    "/openapi.json",
    "/redoc",
}

PUBLIC_PREFIXES: tuple[str, ...] = (
    "/v1/events/stream",  # SSE — uses token query param instead
)


def _is_public_route(path: str) -> bool:
    if path in PUBLIC_ROUTES:
        return True
    return any(path.startswith(prefix) for prefix in PUBLIC_PREFIXES)


async def require_auth(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Security(_bearer_scheme),
) -> str:
    """
    FastAPI dependency that enforces API key auth.

    Usage in routes:
        @router.get("/protected", dependencies=[Depends(require_auth)])
        async def protected(): ...

    Or as a global dependency on the app.
    """
    if _is_public_route(request.url.path):
        return "public"

    settings = get_settings()
    api_key = settings.api_key

    # If no API key is configured, auth is disabled (dev mode)
    if not api_key:
        return "no-auth-configured"

    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Missing Authorization header. Use: Authorization: Bearer <api-key>",
        )

    # Constant-time comparison to prevent timing attacks
    if not secrets.compare_digest(credentials.credentials, api_key):
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
        )

    return credentials.credentials


def generate_api_key() -> str:
    """Generate a cryptographically secure API key."""
    return secrets.token_urlsafe(32)
