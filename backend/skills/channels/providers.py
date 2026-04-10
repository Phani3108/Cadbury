"""
Unified channel interface for multi-channel messaging.

Provides a common interface for sending and receiving messages
across Telegram, WhatsApp, Slack, and SMS channels.
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Optional

import httpx

from config.settings import get_settings
from memory.models import CommsMessage, MessageChannel

logger = logging.getLogger(__name__)


class ChannelProvider(ABC):
    """Base class for all channel providers."""

    @abstractmethod
    async def send_message(self, to: str, text: str) -> bool:
        """Send a message to a recipient."""
        ...

    @abstractmethod
    async def format_digest(self, summary: str) -> str:
        """Format a digest message for this channel."""
        ...


class TelegramChannel(ChannelProvider):
    """Telegram Bot API channel."""

    def __init__(self):
        s = get_settings()
        self.bot_token = s.telegram_bot_token
        self.default_chat_id = s.telegram_chat_id

    async def send_message(self, to: str = "", text: str = "") -> bool:
        chat_id = to or self.default_chat_id
        if not self.bot_token or not chat_id:
            logger.warning("Telegram not configured")
            return False
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(url, json={
                    "chat_id": chat_id, "text": text, "parse_mode": "HTML"
                }, timeout=10.0)
                return resp.status_code == 200
        except Exception:
            logger.exception("Telegram send failed")
            return False

    async def format_digest(self, summary: str) -> str:
        return f"<b>📋 Daily Digest</b>\n\n{summary}"


class WhatsAppChannel(ChannelProvider):
    """WhatsApp Business API channel (via Meta Cloud API)."""

    def __init__(self):
        s = get_settings()
        self.access_token = s.whatsapp_access_token
        self.phone_number_id = s.whatsapp_phone_number_id

    async def send_message(self, to: str = "", text: str = "") -> bool:
        if not self.access_token or not self.phone_number_id or not to:
            logger.warning("WhatsApp not configured")
            return False
        url = f"https://graph.facebook.com/v18.0/{self.phone_number_id}/messages"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": text},
        }
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(url, json=payload, headers=headers, timeout=10.0)
                return resp.status_code == 200
        except Exception:
            logger.exception("WhatsApp send failed")
            return False

    async def format_digest(self, summary: str) -> str:
        # WhatsApp doesn't support HTML — plain text with emojis
        return f"📋 *Daily Digest*\n\n{summary}"


class SlackChannel(ChannelProvider):
    """Slack Bot channel (via Web API)."""

    def __init__(self):
        s = get_settings()
        self.bot_token = s.slack_bot_token
        self.default_channel = s.slack_default_channel

    async def send_message(self, to: str = "", text: str = "") -> bool:
        channel = to or self.default_channel
        if not self.bot_token or not channel:
            logger.warning("Slack not configured")
            return False
        url = "https://slack.com/api/chat.postMessage"
        headers = {"Authorization": f"Bearer {self.bot_token}"}
        payload = {"channel": channel, "text": text, "mrkdwn": True}
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(url, json=payload, headers=headers, timeout=10.0)
                data = resp.json()
                return data.get("ok", False)
        except Exception:
            logger.exception("Slack send failed")
            return False

    async def format_digest(self, summary: str) -> str:
        return f":clipboard: *Daily Digest*\n\n{summary}"


class SMSChannel(ChannelProvider):
    """Twilio SMS channel."""

    def __init__(self):
        s = get_settings()
        self.account_sid = s.twilio_account_sid
        self.auth_token = s.twilio_auth_token
        self.from_number = s.twilio_from_number

    async def send_message(self, to: str = "", text: str = "") -> bool:
        if not self.account_sid or not self.auth_token or not to:
            logger.warning("SMS (Twilio) not configured")
            return False
        url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Messages.json"
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    url,
                    data={"To": to, "From": self.from_number, "Body": text[:1600]},
                    auth=(self.account_sid, self.auth_token),
                    timeout=10.0,
                )
                return resp.status_code in (200, 201)
        except Exception:
            logger.exception("SMS send failed")
            return False

    async def format_digest(self, summary: str) -> str:
        # SMS — keep it ultra short
        return f"Cadbury Digest:\n{summary[:140]}"


def get_channel(channel: MessageChannel) -> ChannelProvider:
    """Factory for channel providers."""
    providers = {
        MessageChannel.TELEGRAM: TelegramChannel,
        MessageChannel.WHATSAPP: WhatsAppChannel,
        MessageChannel.SLACK: SlackChannel,
        MessageChannel.SMS: SMSChannel,
    }
    cls = providers.get(channel)
    if not cls:
        raise ValueError(f"Unknown channel: {channel}")
    return cls()


async def send_to_all_configured_channels(text: str) -> dict[str, bool]:
    """Send a message to all configured channels. Returns {channel: success}."""
    results = {}
    s = get_settings()

    if s.telegram_bot_token and s.telegram_chat_id:
        ch = TelegramChannel()
        formatted = await ch.format_digest(text)
        results["telegram"] = await ch.send_message(text=formatted)

    if s.whatsapp_access_token and s.whatsapp_phone_number_id:
        ch = WhatsAppChannel()
        formatted = await ch.format_digest(text)
        results["whatsapp"] = await ch.send_message(to=s.whatsapp_default_to, text=formatted)

    if s.slack_bot_token and s.slack_default_channel:
        ch = SlackChannel()
        formatted = await ch.format_digest(text)
        results["slack"] = await ch.send_message(text=formatted)

    if s.twilio_account_sid and s.twilio_from_number:
        ch = SMSChannel()
        formatted = await ch.format_digest(text)
        results["sms"] = await ch.send_message(to=s.sms_default_to, text=formatted)

    return results
