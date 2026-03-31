"""Tests for recruiter pipeline stages 1-3 using mock email provider."""
import asyncio
import pytest
from memory.models import EventType, OpportunityStatus
from delegates.recruiter.pipeline import RecruiterPipeline
from skills.email.mock import MockEmailProvider


class MockGraph:
    """In-memory graph for testing — no SQLite needed."""

    def __init__(self, goals=None):
        self._goals = goals
        self.contacts = {}
        self.opportunities = {}
        self.events = []

    async def get_career_goals(self, user_id="default"):
        from memory.models import CareerGoals
        return self._goals or CareerGoals(
            target_roles=["Product Manager", "Senior PM"],
            min_comp_usd=70_000,
            preferred_locations=["Bangalore"],
            work_style="remote",
        )

    async def get_or_create_contact(self, email_addr, name, company):
        from memory.models import RecruiterContact
        if email_addr not in self.contacts:
            self.contacts[email_addr] = RecruiterContact(
                email=email_addr, name=name, company=company
            )
        return self.contacts[email_addr]

    async def save_opportunity(self, opp):
        self.opportunities[opp.opportunity_id] = opp
        return opp

    async def save_event(self, event):
        self.events.append(event)
        return event


@pytest.mark.asyncio
async def test_stage_1_ingest_emits_email_received_events():
    graph = MockGraph()
    pipeline = RecruiterPipeline(
        email_provider=MockEmailProvider(),
        graph=graph,
        event_bus=None,
        llm_enabled=False,
    )
    ctx = await pipeline.run()

    email_events = [e for e in ctx.events_emitted if e.event_type == EventType.EMAIL_RECEIVED]
    assert len(email_events) == 3, f"Expected 3 email events, got {len(email_events)}"
    assert len(ctx.emails_ingested) == 3


@pytest.mark.asyncio
async def test_stage_2_extract_creates_opportunities():
    graph = MockGraph()
    pipeline = RecruiterPipeline(
        email_provider=MockEmailProvider(),
        graph=graph,
        event_bus=None,
        llm_enabled=False,
    )
    ctx = await pipeline.run()

    extracted_events = [
        e for e in ctx.events_emitted if e.event_type == EventType.OPPORTUNITY_EXTRACTED
    ]
    assert len(extracted_events) == 3
    assert len(ctx.opportunities) == 3

    # Each opportunity should be persisted
    assert len(graph.opportunities) == 3


@pytest.mark.asyncio
async def test_stage_3_score_assigns_scores():
    graph = MockGraph()
    pipeline = RecruiterPipeline(
        email_provider=MockEmailProvider(),
        graph=graph,
        event_bus=None,
        llm_enabled=False,
    )
    ctx = await pipeline.run()

    scored_events = [
        e for e in ctx.events_emitted if e.event_type == EventType.OPPORTUNITY_SCORED
    ]
    assert len(scored_events) == 3

    for opp in ctx.opportunities:
        assert 0.0 <= opp.match_score <= 1.0
        assert opp.status == OpportunityStatus.SCORED


@pytest.mark.asyncio
async def test_pipeline_event_count():
    """Each email should produce exactly 3 events: EMAIL_RECEIVED + EXTRACTED + SCORED."""
    graph = MockGraph()
    pipeline = RecruiterPipeline(
        email_provider=MockEmailProvider(),
        graph=graph,
        event_bus=None,
        llm_enabled=False,
    )
    ctx = await pipeline.run()

    # 3 emails × 3 events = 9 total
    assert len(ctx.events_emitted) == 9


@pytest.mark.asyncio
async def test_pipeline_no_errors():
    graph = MockGraph()
    pipeline = RecruiterPipeline(
        email_provider=MockEmailProvider(),
        graph=graph,
        event_bus=None,
        llm_enabled=False,
    )
    ctx = await pipeline.run()
    assert ctx.errors == []


@pytest.mark.asyncio
async def test_pipeline_empty_inbox():
    """Empty inbox → no events, no errors."""
    from skills.email.provider import EmailProvider

    class EmptyProvider(EmailProvider):
        async def list_recruiter_emails(self, limit=20):
            return []
        async def send_reply(self, message_id, body):
            return True
        async def mark_read(self, message_id):
            return True

    graph = MockGraph()
    pipeline = RecruiterPipeline(
        email_provider=EmptyProvider(),
        graph=graph,
        event_bus=None,
        llm_enabled=False,
    )
    ctx = await pipeline.run()
    assert len(ctx.emails_ingested) == 0
    assert len(ctx.opportunities) == 0
    assert len(ctx.events_emitted) == 0
    assert ctx.errors == []
