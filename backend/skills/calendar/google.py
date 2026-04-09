"""Google Calendar provider — uses OAuth2 delegated access via stored tokens."""
from __future__ import annotations

import logging
from datetime import datetime, timezone

import httpx

from skills.calendar.provider import CalendarProvider

logger = logging.getLogger(__name__)

GCAL_BASE = "https://www.googleapis.com/calendar/v3"


class GoogleCalendarProvider(CalendarProvider):
    """CalendarProvider backed by Google Calendar API with OAuth2 refresh tokens."""

    def __init__(self, calendar_id: str = "primary"):
        self._calendar_id = calendar_id
        self._access_token: str | None = None
        self._client = httpx.AsyncClient(timeout=30.0)

    async def _ensure_token(self) -> str:
        """Load or refresh the Google OAuth token from the encrypted store."""
        if self._access_token:
            return self._access_token

        from skills.auth.token_store import load_tokens, save_tokens
        from config.settings import get_settings

        tokens = await load_tokens("google")
        if not tokens or not tokens.get("refresh_token"):
            raise ValueError(
                "No Google tokens found. Connect via /v1/auth/google/login first."
            )

        s = get_settings()
        # Refresh the token
        resp = await self._client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": s.google_client_id,
                "client_secret": s.google_client_secret,
                "grant_type": "refresh_token",
                "refresh_token": tokens["refresh_token"],
            },
        )
        if resp.status_code != 200:
            logger.error("Google token refresh failed: %s", resp.text)
            raise ValueError("Google token refresh failed. Re-connect via /v1/auth/google/login.")

        payload = resp.json()
        self._access_token = payload["access_token"]

        # Persist updated access token
        await save_tokens("google", {
            "access_token": payload["access_token"],
            "refresh_token": tokens["refresh_token"],  # Google doesn't always return a new refresh token
            "expires_in": payload.get("expires_in", 3600),
            "scope": payload.get("scope", ""),
        })

        return self._access_token

    async def _headers(self) -> dict[str, str]:
        token = await self._ensure_token()
        return {"Authorization": f"Bearer {token}"}

    async def get_busy_periods(
        self, start: datetime, end: datetime
    ) -> list[dict]:
        """Query Google Calendar freebusy API."""
        url = f"{GCAL_BASE}/freeBusy"
        body = {
            "timeMin": start.isoformat(),
            "timeMax": end.isoformat(),
            "items": [{"id": self._calendar_id}],
        }

        try:
            resp = await self._client.post(
                url, headers=await self._headers(), json=body
            )
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            logger.error("Google Calendar freeBusy failed: %s", exc)
            return []

        data = resp.json()
        calendar_data = data.get("calendars", {}).get(self._calendar_id, {})
        busy_list = calendar_data.get("busy", [])

        return [
            {
                "start": datetime.fromisoformat(b["start"].replace("Z", "+00:00")),
                "end": datetime.fromisoformat(b["end"].replace("Z", "+00:00")),
            }
            for b in busy_list
        ]

    async def create_event(
        self,
        title: str,
        start: datetime,
        end: datetime,
        attendees: list[str] | None = None,
        tentative: bool = False,
    ) -> dict:
        """Create a Google Calendar event."""
        url = f"{GCAL_BASE}/calendars/{self._calendar_id}/events"
        body: dict = {
            "summary": title,
            "start": {"dateTime": start.isoformat(), "timeZone": "UTC"},
            "end": {"dateTime": end.isoformat(), "timeZone": "UTC"},
            "status": "tentative" if tentative else "confirmed",
        }
        if attendees:
            body["attendees"] = [{"email": a} for a in attendees]

        try:
            resp = await self._client.post(
                url, headers=await self._headers(), json=body
            )
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            logger.error("Google Calendar create event failed: %s", exc)
            raise

        event = resp.json()
        return {
            "event_id": event["id"],
            "title": event.get("summary", title),
            "start": start,
            "end": end,
        }

    async def cancel_event(self, event_id: str) -> bool:
        """Cancel (delete) a Google Calendar event."""
        url = f"{GCAL_BASE}/calendars/{self._calendar_id}/events/{event_id}"
        try:
            resp = await self._client.delete(url, headers=await self._headers())
            return resp.status_code in (200, 204)
        except httpx.HTTPError as exc:
            logger.error("Google Calendar cancel event failed: %s", exc)
            return False

    async def close(self) -> None:
        await self._client.aclose()
