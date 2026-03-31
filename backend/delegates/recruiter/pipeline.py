"""
Recruiter Delegate — 6-stage pipeline.
Week 2 implements Stages 1-3 (Ingest, Extract, Score).
Stages 4-6 (Policy, Draft, Act) are stubs for Week 3.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

from memory.graph import MemoryGraph
from memory.models import (
    CareerGoals,
    DelegateEvent,
    EventType,
    JobOpportunity,
    OpportunityStatus,
    RecruiterContact,
    RemotePolicy,
)
from skills.email.provider import EmailProvider, RawEmail

if TYPE_CHECKING:
    pass

_PROMPTS_DIR = Path(__file__).parent / "prompts"


def _load_prompt(name: str) -> str:
    return (_PROMPTS_DIR / name).read_text()


@dataclass
class PipelineContext:
    """Mutable state carried through all pipeline stages for a single pipeline run."""
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    emails_ingested: list[RawEmail] = field(default_factory=list)
    opportunities: list[JobOpportunity] = field(default_factory=list)
    events_emitted: list[DelegateEvent] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def emit(self, event: DelegateEvent) -> DelegateEvent:
        self.events_emitted.append(event)
        return event


class RecruiterPipeline:
    """
    Orchestrates the recruiter delegate's 6-stage processing pipeline.
    Each stage is an async method that reads/writes PipelineContext.
    """

    def __init__(
        self,
        email_provider: EmailProvider,
        graph: MemoryGraph,
        event_bus=None,  # optional — publish events to SSE subscribers
        llm_enabled: bool = True,
    ):
        self.email_provider = email_provider
        self.graph = graph
        self.event_bus = event_bus
        self.llm_enabled = llm_enabled

    async def run(self) -> PipelineContext:
        """Execute all pipeline stages, return the completed context."""
        ctx = PipelineContext()
        await self._stage_1_ingest(ctx)
        await self._stage_2_extract(ctx)
        await self._stage_3_score(ctx)
        # Stages 4-6 in Week 3
        return ctx

    # ─── Stage 1: INGEST ──────────────────────────────────────────────────────

    async def _stage_1_ingest(self, ctx: PipelineContext) -> None:
        """Fetch recruiter emails and persist contact records."""
        emails = await self.email_provider.list_recruiter_emails()
        for email in emails:
            # Persist/update recruiter contact
            await self.graph.get_or_create_contact(
                name=email.sender_name,
                email_addr=email.sender_email,
                company=_extract_company_from_email(email),
            )

            event = DelegateEvent(
                delegate_id="recruiter",
                event_type=EventType.EMAIL_RECEIVED,
                trace_id=ctx.trace_id,
                summary=f"Email from {email.sender_name} ({email.sender_email}): {email.subject}",
                payload={
                    "message_id": email.message_id,
                    "sender_name": email.sender_name,
                    "sender_email": email.sender_email,
                    "subject": email.subject,
                    "received_at": email.received_at.isoformat(),
                },
            )
            await self.graph.save_event(event)
            if self.event_bus:
                await self.event_bus.publish_event(event)
            ctx.emit(event)

        ctx.emails_ingested = emails

    # ─── Stage 2: EXTRACT ─────────────────────────────────────────────────────

    async def _stage_2_extract(self, ctx: PipelineContext) -> None:
        """Extract structured JobOpportunity from each email."""
        if not ctx.emails_ingested:
            return

        for email in ctx.emails_ingested:
            try:
                opportunity = await self._extract_opportunity(email)
                if opportunity is None:
                    continue

                await self.graph.save_opportunity(opportunity)

                event = DelegateEvent(
                    delegate_id="recruiter",
                    event_type=EventType.OPPORTUNITY_EXTRACTED,
                    trace_id=ctx.trace_id,
                    summary=f"Extracted: {opportunity.role} at {opportunity.company}",
                    payload={
                        "opportunity_id": opportunity.opportunity_id,
                        "company": opportunity.company,
                        "role": opportunity.role,
                        "location": opportunity.location,
                        "remote_policy": opportunity.remote_policy,
                        "comp_range_min": opportunity.comp_range_min,
                        "comp_range_max": opportunity.comp_range_max,
                    },
                )
                await self.graph.save_event(event)
                if self.event_bus:
                    await self.event_bus.publish_event(event)
                ctx.emit(event)
                ctx.opportunities.append(opportunity)

            except Exception as exc:
                ctx.errors.append(f"Extract failed for {email.message_id}: {exc}")

    async def _extract_opportunity(self, email: RawEmail) -> JobOpportunity | None:
        """Use LLM (or heuristics in mock mode) to extract opportunity from email."""
        if self.llm_enabled:
            from skills import llm_client
            system_prompt = _load_prompt("extract_jd.txt")
            result = await llm_client.extract_json(
                system_prompt=system_prompt,
                user_content=f"Subject: {email.subject}\n\n{email.body}",
            )
            if not result.get("is_recruiter_email", True):
                return None
        else:
            # Mock extraction — parse directly from email fields for testing
            result = _mock_extract(email)

        # Map contact
        contact = await self.graph.get_or_create_contact(
            name=email.sender_name,
            email_addr=email.sender_email,
            company=result.get("company", ""),
        )

        remote_map = {
            "remote": RemotePolicy.REMOTE,
            "hybrid": RemotePolicy.HYBRID,
            "onsite": RemotePolicy.ONSITE,
        }
        remote_policy = remote_map.get(
            (result.get("remote_policy") or "unknown").lower(),
            RemotePolicy.UNKNOWN,
        )

        return JobOpportunity(
            contact_id=contact.contact_id,
            company=result.get("company") or email.sender_email.split("@")[-1],
            role=result.get("role") or email.subject,
            comp_range_min=result.get("comp_range_min"),
            comp_range_max=result.get("comp_range_max"),
            equity=result.get("equity"),
            location=result.get("location") or "",
            remote_policy=remote_policy,
            jd_summary=result.get("jd_summary") or "",
            email_subject=email.subject,
            email_id=email.message_id,
            status=OpportunityStatus.EXTRACTED,
        )

    # ─── Stage 3: SCORE ───────────────────────────────────────────────────────

    async def _stage_3_score(self, ctx: PipelineContext) -> None:
        """Score each extracted opportunity against career goals."""
        if not ctx.opportunities:
            return

        goals = await self.graph.get_career_goals()
        if goals is None:
            goals = CareerGoals()

        from delegates.recruiter import scorer

        for opportunity in ctx.opportunities:
            overall_score, breakdown = scorer.score(opportunity, goals)
            opportunity.match_score = overall_score
            opportunity.match_breakdown = breakdown
            opportunity.status = OpportunityStatus.SCORED
            opportunity.updated_at = datetime.now(timezone.utc)

            await self.graph.save_opportunity(opportunity)

            event = DelegateEvent(
                delegate_id="recruiter",
                event_type=EventType.OPPORTUNITY_SCORED,
                trace_id=ctx.trace_id,
                summary=f"{opportunity.company} — {opportunity.role}: {overall_score:.0%} match",
                payload={
                    "opportunity_id": opportunity.opportunity_id,
                    "match_score": overall_score,
                    "breakdown": breakdown.model_dump(),
                },
            )
            await self.graph.save_event(event)
            if self.event_bus:
                await self.event_bus.publish_event(event)
            ctx.emit(event)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _extract_company_from_email(email: RawEmail) -> str:
    """Best-effort company name from email domain."""
    domain = email.sender_email.split("@")[-1].split(".")[0]
    return domain.capitalize()


def _mock_extract(email: RawEmail) -> dict:
    """Rule-based extraction for testing without LLM."""
    body = email.body.lower()
    subject = email.subject.lower()

    # Detect remote policy
    if "remote-first" in body or "fully remote" in body or "remote" in subject:
        remote = "remote"
    elif "hybrid" in body:
        remote = "hybrid"
    else:
        remote = "onsite"

    # Rough comp extraction — look for ₹ or lakh patterns
    comp_min = None
    comp_max = None
    import re
    lakh_pattern = re.findall(r"₹\s*(\d+\.?\d*)\s*[lL]", email.body)
    if lakh_pattern and len(lakh_pattern) >= 2:
        comp_min = int(float(lakh_pattern[0]) * 100_000)
        comp_max = int(float(lakh_pattern[1]) * 100_000)
    elif lakh_pattern:
        comp_min = int(float(lakh_pattern[0]) * 100_000)

    # Location
    for city in ["bangalore", "mumbai", "delhi", "hyderabad", "chennai", "pune"]:
        if city in body:
            location = city.capitalize()
            break
    else:
        location = "Remote" if remote == "remote" else ""

    return {
        "company": _extract_company_from_email(email),
        "role": email.subject.split("-")[0].strip() if "-" in email.subject else email.subject,
        "comp_range_min": comp_min,
        "comp_range_max": comp_max,
        "equity": None,
        "location": location,
        "remote_policy": remote,
        "jd_summary": email.body[:200].strip(),
        "is_recruiter_email": True,
    }
