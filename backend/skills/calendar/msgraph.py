"""MS Graph Calendar provider — uses delegated OAuth2 tokens."""
from __future__ import annotations

import logging
from datetime import datetime, timezone

import httpx

from skills.calendar.provider import CalendarProvider

logger = logging.getLogger(__name__)

GRAPH_BASE = "https://graph.microsoft.com/v1.0"


class MSGraphCalendarProvider(CalendarProvider):
    """CalendarProvider backed by Microsoft Graph Calendar API."""

    def __init__(self):
        self._access_token: str | None = None
        self._client = httpx.AsyncClient(timeout=30.0)

    async def _ensure_token(self) -> str:
        if self._access_token:
            return self._access_token

        from skills.auth.token_store import load_tokens, save_tokens
        from config.settings import get_settings

        tokens = await load_tokens("microsoft")
        if not tokens or not tokens.get("refresh_token"):
            raise ValueError("No Microsoft tokens. Connect via /v1/auth/microsoft/login first.")

        s = get_settings()
        tenant = s.msgraph_tenant_id or "common"
        resp = await self._client.post(
            f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token",
            data={
                "client_id": s.msgraph_client_id,
                "grant_type": "refresh_token",
                "refresh_token": tokens["refresh_token"],
                "scope": "offline_access Calendars.ReadWrite",
                **({"client_secret": s.msgraph_client_secret} if s.msgraph_client_secret else {}),
            },
        )
        if resp.status_code != 200:
            raise ValueError("Microsoft token refresh failed.")

        payload = resp.json()
        self._access_token = payload["access_token"]
        await save_tokens("microsoft", {
            "access_token": payload["access_token"],
            "refresh_token": payload.get("refresh_token", tokens["refresh_token"]),
            "expires_in": payload.get("expires_in", 3600),
            "scope": payload.get("scope", ""),
        })
        return self._access_token

    async def _headers(self) -> dict[str, str]:
        token = await self._ensure_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    async def get_busy_periods(self, start: datetime, end: datetime) -> list[dict]:
        """Get busy periods using Graph CalendarView."""
        url = f"{GRAPH_BASE}/me/calendarView"
        params = {
            "startDateTime": start.isoformat(),
            "endDateTime": end.isoformat(),
            "$select": "start,end,showAs",
        }

        try:
            resp = await self._client.get(url, headers=await self._headers(), params=params)
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            logger.error("Graph calendarView failed: %s", exc)
            return []

        events = resp.json().get("value", [])
        return [
            {
                "start": datetime.fromisoformat(e["start"]["dateTime"].replace("Z", "+00:00")),
                "end": datetime.fromisoformat(e["end"]["dateTime"].replace("Z", "+00:00")),
            }
            for e in events
            if e.get("showAs") in ("busy", "tentative", "oof", None)
        ]

    async def create_event(
        self,
        title: str,
        start: datetime,
        end: datetime,
        attendees: list[str] | None = None,
        tentative: bool = False,
    ) -> dict:
        """Create a calendar event via MS Graph."""
        url = f"{GRAPH_BASE}/me/events"
        body: dict = {
            "subject": title,
            "start": {"dateTime": start.isoformat(), "timeZone": "UTC"},
            "end": {"dateTime": end.isoformat(), "timeZone": "UTC"},
            "showAs": "tentative" if tentative else "busy",
        }
        if attendees:
            body["attendees"] = [
                {"emailAddress": {"address": a}, "type": "required"}
                for a in attendees
            ]

        try:
            resp = await self._client.post(url, headers=await self._headers(), json=body)
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            logger.error("Graph create event failed: %s", exc)
            raise

        event = resp.json()
        return {
            "event_id": event["id"],
            "title": event.get("subject", title),
            "start": start,
            "end": end,
        }

    async def cancel_event(self, event_id: str) -> bool:
        url = f"{GRAPH_BASE}/me/events/{event_id}"
        try:
            resp = await self._client.delete(url, headers=await self._headers())
            return resp.status_code in (200, 204)
        except httpx.HTTPError:
            return False
