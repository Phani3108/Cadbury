"""
Action executors — perform the real-world action after human approval.

Each executor takes an ApprovalItem and executes the corresponding action
(e.g., sending an email reply, creating a calendar event).
"""
from __future__ import annotations

import logging

from config.settings import get_settings
from memory.graph import (
    get_opportunity,
    save_event,
    save_opportunity,
)
from memory.models import (
    DelegateEvent,
    EventType,
    OpportunityStatus,
)
from runtime.event_bus import publish_event, publish_typed_event
from skills.auth.token_store import has_tokens

logger = logging.getLogger(__name__)


async def get_email_provider():
    """Build the appropriate email provider based on available credentials."""
    s = get_settings()

    # Prefer delegated auth (user connected via OAuth)
    if await has_tokens("microsoft"):
        from skills.email.msgraph import MSGraphEmailProvider
        return MSGraphEmailProvider(
            tenant_id=s.msgraph_tenant_id,
            client_id=s.msgraph_client_id,
            client_secret=s.msgraph_client_secret,
            use_delegated=True,
        )

    # Fall back to client-credentials if configured
    if s.msgraph_client_id and s.msgraph_client_secret and s.msgraph_user_email:
        from skills.email.msgraph import MSGraphEmailProvider
        return MSGraphEmailProvider(
            tenant_id=s.msgraph_tenant_id,
            client_id=s.msgraph_client_id,
            client_secret=s.msgraph_client_secret,
            user_email=s.msgraph_user_email,
        )

    # Fall back to mock
    from skills.email.mock import MockEmailProvider
    return MockEmailProvider()


async def execute_send_email(
    approval_id: str,
    delegate_id: str,
    opportunity_id: str | None,
    draft_content: str | None,
    payload: dict,
) -> dict:
    """
    Send the approved email reply.

    Returns a dict with 'sent' (bool) and 'provider' (str).
    """
    if not draft_content:
        logger.warning("No draft content for approval %s — skipping send", approval_id)
        return {"sent": False, "reason": "no_draft_content"}

    # Get the original email message_id from the opportunity
    message_id = payload.get("email_id") or payload.get("message_id")
    if not message_id and opportunity_id:
        opp = await get_opportunity(opportunity_id)
        if opp:
            message_id = opp.email_id

    if not message_id:
        logger.warning("No email message_id for approval %s — cannot send", approval_id)
        return {"sent": False, "reason": "no_message_id"}

    provider = await get_email_provider()
    provider_name = type(provider).__name__

    try:
        sent = await provider.send_reply(message_id, draft_content)
    except Exception:
        logger.exception("Failed to send email for approval %s", approval_id)
        sent = False
    finally:
        if hasattr(provider, "close"):
            await provider.close()

    if sent:
        # Emit RESPONSE_SENT event
        event = DelegateEvent(
            delegate_id=delegate_id,
            event_type=EventType.RESPONSE_SENT,
            summary=f"Email reply sent via {provider_name}",
            payload={
                "approval_id": approval_id,
                "opportunity_id": opportunity_id,
                "message_id": message_id,
                "provider": provider_name,
            },
        )
        await save_event(event)
        await publish_event(event)
        await publish_typed_event("email.sent", {
            "approval_id": approval_id,
            "opportunity_id": opportunity_id,
        })

        # Mark the email as read
        try:
            provider2 = await get_email_provider()
            await provider2.mark_read(message_id)
            if hasattr(provider2, "close"):
                await provider2.close()
        except Exception:
            logger.warning("Failed to mark email %s as read", message_id)

        # Update opportunity status
        if opportunity_id:
            opp = await get_opportunity(opportunity_id)
            if opp:
                opp.status = OpportunityStatus.RESPONDED
                await save_opportunity(opp)

        logger.info("Email sent for approval %s via %s", approval_id, provider_name)

        # Send Telegram notification
        try:
            from skills.notifications.telegram import notify_email_sent
            await notify_email_sent(approval_id, opportunity_id, provider_name)
        except Exception:
            pass

    return {"sent": sent, "provider": provider_name}
