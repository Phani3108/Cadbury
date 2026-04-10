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
    DecisionLog,
    DelegateEvent,
    EventType,
    JobOpportunity,
    Notification,
    NotificationType,
    OpportunityStatus,
    RecruiterContact,
    RemotePolicy,
)
from runtime.tracker import tracked_pipeline
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

    @tracked_pipeline("recruiter")
    async def run(self) -> PipelineContext:
        """Execute all pipeline stages, return the completed context."""
        ctx = PipelineContext()
        await self._stage_1_ingest(ctx)
        await self._stage_2_extract(ctx)
        await self._stage_3_score(ctx)
        await self._stage_4_policy(ctx)
        await self._stage_5_draft(ctx)
        await self._stage_6_act(ctx)
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
                # Thread tracking: check if this thread already has an opportunity
                if email.thread_id:
                    existing = await self.graph.get_opportunity_by_thread(email.thread_id)
                    if existing:
                        # Update existing opportunity with fresh email context
                        existing.jd_text = email.body
                        existing.updated_at = datetime.now(timezone.utc)
                        await self.graph.save_opportunity(existing)
                        ctx.opportunities.append(existing)
                        continue

                opportunity = await self._extract_opportunity(email)
                if opportunity is None:
                    continue

                # Store thread_id and full email body for downstream use
                opportunity.thread_id = email.thread_id
                opportunity.jd_text = email.body
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


    # ─── Stage 4: POLICY CHECK ────────────────────────────────────────────────

    async def _stage_4_policy(self, ctx: PipelineContext) -> None:
        """
        Run PolicyEngine against each opportunity to determine response type.
        Blocks opportunities that fall below the hard block threshold via policy;
        tags the rest with a response_type ('engage' | 'hold' | 'decline').
        """
        if not ctx.opportunities:
            return

        from policy.engine import PolicyEngine
        engine = PolicyEngine("recruiter")

        for opportunity in ctx.opportunities:
            score = opportunity.match_score
            response_type = engine.get_response_type(score)
            zone = engine.check("send_engagement_reply" if response_type == "engage" else "send_polite_decline", score)

            rules_checked = [
                f"min_score_for_engagement:{engine.policy.thresholds.min_score_for_engagement}",
                f"auto_decline_below:{engine.policy.thresholds.auto_decline_below}",
                f"zone:{zone}",
            ]

            if zone == "block":
                opportunity.status = OpportunityStatus.REJECTED
                await self.graph.save_opportunity(opportunity)

                event = DelegateEvent(
                    delegate_id="recruiter",
                    event_type=EventType.POLICY_BLOCKED,
                    trace_id=ctx.trace_id,
                    summary=f"Policy blocked: {opportunity.company} — score {score:.0%}",
                    payload={
                        "opportunity_id": opportunity.opportunity_id,
                        "score": score,
                        "response_type": response_type,
                        "zone": zone,
                    },
                    policy_rules_checked=rules_checked,
                )
                await self.graph.save_event(event)
                if self.event_bus:
                    await self.event_bus.publish_event(event)
                ctx.emit(event)
                continue

            # Tag for downstream stages (store on context via a side dict)
            ctx._opportunity_response_types = getattr(ctx, "_opportunity_response_types", {})
            ctx._opportunity_response_types[opportunity.opportunity_id] = response_type
            ctx._opportunity_rules = getattr(ctx, "_opportunity_rules", {})
            ctx._opportunity_rules[opportunity.opportunity_id] = rules_checked

    # ─── Stage 5: DRAFT ───────────────────────────────────────────────────────

    async def _stage_5_draft(self, ctx: PipelineContext) -> None:
        """Generate a draft email reply for each non-blocked opportunity."""
        if not ctx.opportunities:
            return

        response_types = getattr(ctx, "_opportunity_response_types", {})
        if not response_types:
            return

        goals = await self.graph.get_career_goals()
        if goals is None:
            from memory.models import CareerGoals as _CG
            goals = _CG()

        from delegates.recruiter import drafter

        for opportunity in ctx.opportunities:
            response_type = response_types.get(opportunity.opportunity_id)
            if response_type is None:
                continue  # blocked — skip

            try:
                draft_text = await drafter.draft_response(
                    response_type=response_type,
                    opportunity=opportunity,
                    goals=goals,
                    email_body=opportunity.jd_text or "",
                    llm_enabled=self.llm_enabled,
                )
            except Exception as exc:
                ctx.errors.append(f"Draft failed for {opportunity.opportunity_id}: {exc}")
                draft_text = ""

            opportunity.status = OpportunityStatus.DRAFT_CREATED
            await self.graph.save_opportunity(opportunity)

            event = DelegateEvent(
                delegate_id="recruiter",
                event_type=EventType.DRAFT_CREATED,
                trace_id=ctx.trace_id,
                summary=f"Draft {response_type} for {opportunity.company} — {opportunity.role}",
                payload={
                    "opportunity_id": opportunity.opportunity_id,
                    "response_type": response_type,
                    "draft_preview": draft_text[:120] + "…" if len(draft_text) > 120 else draft_text,
                },
            )
            await self.graph.save_event(event)
            if self.event_bus:
                await self.event_bus.publish_event(event)
            ctx.emit(event)

            # Stash draft text for Stage 6
            ctx._opportunity_drafts = getattr(ctx, "_opportunity_drafts", {})
            ctx._opportunity_drafts[opportunity.opportunity_id] = draft_text

    # ─── Stage 6: ACT (Human-in-the-Loop gate) ────────────────────────────────

    async def _stage_6_act(self, ctx: PipelineContext) -> None:
        """
        Create ApprovalItem for each drafted opportunity, OR auto-decline if the
        score is below the auto_decline_threshold.
        """
        if not ctx.opportunities:
            return

        response_types = getattr(ctx, "_opportunity_response_types", {})
        drafts = getattr(ctx, "_opportunity_drafts", {})
        rules_map = getattr(ctx, "_opportunity_rules", {})

        if not response_types:
            return

        from policy.engine import PolicyEngine
        engine = PolicyEngine("recruiter")

        for opportunity in ctx.opportunities:
            response_type = response_types.get(opportunity.opportunity_id)
            if response_type is None:
                continue

            draft_text = drafts.get(opportunity.opportunity_id, "")
            rules_checked = rules_map.get(opportunity.opportunity_id, [])

            action_labels = {
                "engage": "Send engagement reply",
                "hold": "Send hold reply (more info requested)",
                "decline": "Send polite decline",
            }

            # Check if this can be auto-declined
            action_name = "send_polite_decline" if response_type == "decline" else f"send_{response_type}_reply"
            if engine.can_auto_act(action_name, opportunity.match_score):
                # Auto-decline: send immediately without approval
                await self.email_provider.send_reply(opportunity.email_id or "", draft_text)
                opportunity.status = OpportunityStatus.RESPONDED
                await self.graph.save_opportunity(opportunity)

                event = DelegateEvent(
                    delegate_id="recruiter",
                    event_type=EventType.AUTO_DECLINED,
                    trace_id=ctx.trace_id,
                    summary=f"Auto-declined: {opportunity.company} — {opportunity.role} ({opportunity.match_score:.0%})",
                    payload={
                        "opportunity_id": opportunity.opportunity_id,
                        "response_type": response_type,
                        "match_score": opportunity.match_score,
                    },
                    policy_rules_checked=rules_checked,
                )
                await self.graph.save_event(event)
                if self.event_bus:
                    await self.event_bus.publish_event(event)
                ctx.emit(event)

                # Log decision as auto-acted
                await self.graph.log_decision(DecisionLog(
                    delegate_id="recruiter",
                    event_id=event.event_id,
                    action_taken=f"auto_declined:{opportunity.opportunity_id}",
                    reasoning=f"Score {opportunity.match_score:.0%} below auto-decline threshold",
                    human_approved=None,
                    policy_check={"rules_checked": rules_checked, "response_type": response_type},
                ))

                # Create notification for auto-decline
                await self.graph.save_notification(Notification(
                    type=NotificationType.AUTO_ACTED,
                    title=f"Auto-declined: {opportunity.company}",
                    body=f"{opportunity.role} — {opportunity.match_score:.0%} match",
                    link=f"/opportunities/{opportunity.opportunity_id}",
                ))
                continue

            # Otherwise, create ApprovalItem for human review
            from memory.models import ApprovalItem as _AI
            approval = _AI(
                delegate_id="recruiter",
                event_id=ctx.events_emitted[-1].event_id if ctx.events_emitted else "",
                opportunity_id=opportunity.opportunity_id,
                action=action_name,
                action_label=action_labels.get(response_type, "Send reply"),
                context_summary=(
                    f"{opportunity.company} · {opportunity.role} · "
                    f"{opportunity.location} · {opportunity.match_score:.0%} match"
                ),
                draft_content=draft_text,
                risk_score=1.0 - opportunity.match_score,
                reasoning=(
                    f"Score {opportunity.match_score:.0%} → response type '{response_type}'. "
                    f"Policy rules: {', '.join(rules_checked)}"
                ),
                policy_check={
                    "rules_checked": rules_checked,
                    "response_type": response_type,
                    "match_score": opportunity.match_score,
                    "match_breakdown": opportunity.match_breakdown.model_dump(),
                },
            )
            await self.graph.save_approval(approval)

            opportunity.status = OpportunityStatus.APPROVAL_PENDING
            await self.graph.save_opportunity(opportunity)

            event = DelegateEvent(
                delegate_id="recruiter",
                event_type=EventType.APPROVAL_REQUESTED,
                trace_id=ctx.trace_id,
                summary=f"Approval needed: {action_labels.get(response_type, 'Send reply')} — {opportunity.company}",
                payload={
                    "approval_id": approval.approval_id,
                    "opportunity_id": opportunity.opportunity_id,
                    "response_type": response_type,
                    "action_label": approval.action_label,
                },
                requires_approval=True,
                policy_rules_checked=rules_checked,
            )
            await self.graph.save_event(event)
            if self.event_bus:
                await self.event_bus.publish_event(event)
                await self.event_bus.publish_typed_event(
                    "approval.new", approval.model_dump(mode="json")
                )
            ctx.emit(event)

            # Create notification for new approval
            await self.graph.save_notification(Notification(
                type=NotificationType.NEW_APPROVAL,
                title=f"Review needed: {opportunity.company}",
                body=f"{opportunity.role} — {opportunity.match_score:.0%} match",
                link=f"/approvals",
            ))

            # Calendar pre-block for high-match engagements
            if response_type == "engage" and opportunity.match_score >= 0.80:
                cal_event = DelegateEvent(
                    delegate_id="recruiter",
                    event_type=EventType.CALENDAR_PREBLOCK_REQUESTED,
                    trace_id=ctx.trace_id,
                    summary=f"Calendar pre-block requested for {opportunity.company}",
                    payload={
                        "opportunity_id": opportunity.opportunity_id,
                        "company": opportunity.company,
                        "role": opportunity.role,
                        "contact_id": opportunity.contact_id,
                    },
                )
                await self.graph.save_event(cal_event)
                if self.event_bus:
                    await self.event_bus.publish_event(cal_event)
                ctx.emit(cal_event)


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
