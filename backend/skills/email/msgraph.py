"""Microsoft Graph API email provider implementation."""
from __future__ import annotations

import logging
import time
from datetime import datetime, timezone

import httpx

from .provider import EmailProvider, RawEmail

logger = logging.getLogger(__name__)

TOKEN_URL = "https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
GRAPH_BASE = "https://graph.microsoft.com/v1.0"


class MSGraphEmailProvider(EmailProvider):
    """EmailProvider backed by Microsoft Graph API using client-credentials OAuth2."""

    def __init__(
        self,
        tenant_id: str,
        client_id: str,
        client_secret: str,
        user_email: str,
    ) -> None:
        self._tenant_id = tenant_id
        self._client_id = client_id
        self._client_secret = client_secret
        self._user_email = user_email

        self._access_token: str | None = None
        self._token_expires_at: float = 0.0
        self._client = httpx.AsyncClient(timeout=30.0)

    # ------------------------------------------------------------------
    # OAuth2 token management
    # ------------------------------------------------------------------

    async def _ensure_token(self) -> str:
        """Return a valid access token, refreshing if expired."""
        if self._access_token and time.monotonic() < self._token_expires_at:
            return self._access_token

        url = TOKEN_URL.format(tenant_id=self._tenant_id)
        data = {
            "client_id": self._client_id,
            "client_secret": self._client_secret,
            "scope": "https://graph.microsoft.com/.default",
            "grant_type": "client_credentials",
        }

        resp = await self._client.post(url, data=data)
        resp.raise_for_status()
        payload = resp.json()

        self._access_token = payload["access_token"]
        # Expire 60 s early to avoid edge-case clock drift
        expires_in: int = payload.get("expires_in", 3600)
        self._token_expires_at = time.monotonic() + expires_in - 60
        logger.debug("Acquired new MS Graph token (expires_in=%d)", expires_in)
        return self._access_token

    async def _headers(self) -> dict[str, str]:
        token = await self._ensure_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    # ------------------------------------------------------------------
    # EmailProvider implementation
    # ------------------------------------------------------------------

    async def list_recruiter_emails(self, limit: int = 20) -> list[RawEmail]:
        """Fetch unread messages from the user's mailbox, newest first."""
        url = f"{GRAPH_BASE}/users/{self._user_email}/messages"
        params = {
            "$filter": "isRead eq false",
            "$top": str(limit),
            "$orderby": "receivedDateTime desc",
            "$select": "id,subject,body,from,receivedDateTime,conversationId",
        }

        try:
            resp = await self._client.get(
                url, headers=await self._headers(), params=params
            )
            resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            logger.error(
                "Graph list messages failed: %s %s",
                exc.response.status_code,
                exc.response.text,
            )
            return []
        except httpx.HTTPError as exc:
            logger.error("Graph list messages network error: %s", exc)
            return []

        messages: list[RawEmail] = []
        for msg in resp.json().get("value", []):
            try:
                from_field = msg.get("from", {}).get("emailAddress", {})
                received_str = msg.get("receivedDateTime", "")
                received_at = (
                    datetime.fromisoformat(received_str.replace("Z", "+00:00"))
                    if received_str
                    else datetime.now(timezone.utc)
                )

                messages.append(
                    RawEmail(
                        message_id=msg["id"],
                        sender_name=from_field.get("name", ""),
                        sender_email=from_field.get("address", ""),
                        subject=msg.get("subject", ""),
                        body=msg.get("body", {}).get("content", ""),
                        received_at=received_at,
                        thread_id=msg.get("conversationId"),
                    )
                )
            except (KeyError, ValueError) as exc:
                logger.warning("Skipping malformed message: %s", exc)

        logger.info("Fetched %d unread messages from Graph API", len(messages))
        return messages

    async def send_reply(self, message_id: str, body: str) -> bool:
        """Reply to a message by its Graph message ID."""
        url = f"{GRAPH_BASE}/users/{self._user_email}/messages/{message_id}/reply"
        payload = {
            "message": {
                "body": {
                    "contentType": "Text",
                    "content": body,
                },
            },
        }

        try:
            resp = await self._client.post(
                url, headers=await self._headers(), json=payload
            )
            resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            logger.error(
                "Graph send_reply failed: %s %s",
                exc.response.status_code,
                exc.response.text,
            )
            return False
        except httpx.HTTPError as exc:
            logger.error("Graph send_reply network error: %s", exc)
            return False

        logger.info("Replied to message %s", message_id)
        return True

    async def mark_read(self, message_id: str) -> bool:
        """Mark a single message as read."""
        url = f"{GRAPH_BASE}/users/{self._user_email}/messages/{message_id}"
        payload = {"isRead": True}

        try:
            resp = await self._client.patch(
                url, headers=await self._headers(), json=payload
            )
            resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            logger.error(
                "Graph mark_read failed: %s %s",
                exc.response.status_code,
                exc.response.text,
            )
            return False
        except httpx.HTTPError as exc:
            logger.error("Graph mark_read network error: %s", exc)
            return False

        logger.debug("Marked message %s as read", message_id)
        return True

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._client.aclose()
