"""
Learning Delegate Pipeline — assess skill gaps, plan learning paths, track progress.

Pipeline: Assess → Plan → Track → Nudge → Report
"""
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

from memory.graph import (
    save_learning_path,
    list_learning_paths,
    get_learning_path,
    get_career_goals,
    save_event,
    save_approval,
)
from memory.models import (
    LearningPath,
    SkillGap,
    DelegateEvent,
    EventType,
    ApprovalItem,
)
from runtime.event_bus import publish_event

logger = logging.getLogger(__name__)

DELEGATE_ID = "learning"

# Common tech skill clusters for gap detection
SKILL_CLUSTERS = {
    "python": ["python", "django", "flask", "fastapi", "asyncio"],
    "javascript": ["javascript", "typescript", "react", "next.js", "node.js"],
    "cloud": ["aws", "azure", "gcp", "kubernetes", "docker", "terraform"],
    "data": ["sql", "postgresql", "mongodb", "redis", "elasticsearch"],
    "ml": ["machine learning", "pytorch", "tensorflow", "llm", "ai"],
    "devops": ["ci/cd", "github actions", "jenkins", "monitoring", "observability"],
    "system_design": ["distributed systems", "microservices", "event-driven", "caching"],
}


@dataclass
class LearningContext:
    skill_gaps: list[SkillGap] = field(default_factory=list)
    paths_created: list[LearningPath] = field(default_factory=list)
    nudges: list[str] = field(default_factory=list)
    events_emitted: list[DelegateEvent] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))


def _detect_skill_gaps(target_roles: list[str], criteria: list[str]) -> list[SkillGap]:
    """Deterministic skill gap analysis based on career goals."""
    gaps = []
    all_criteria_lower = [c.lower() for c in criteria]

    for cluster_name, skills in SKILL_CLUSTERS.items():
        # Check if any skill in this cluster is mentioned in criteria
        mentioned = any(
            any(s in c for s in skills)
            for c in all_criteria_lower
        )
        if not mentioned:
            # This cluster is a gap if roles typically need it
            role_text = " ".join(target_roles).lower()
            relevant = False
            if cluster_name == "python" and any(k in role_text for k in ["backend", "engineer", "developer"]):
                relevant = True
            elif cluster_name == "cloud" and any(k in role_text for k in ["senior", "staff", "lead", "sre"]):
                relevant = True
            elif cluster_name == "system_design" and any(k in role_text for k in ["senior", "staff", "principal"]):
                relevant = True
            elif cluster_name == "ml" and any(k in role_text for k in ["ml", "ai", "data", "machine"]):
                relevant = True

            if relevant:
                gaps.append(SkillGap(
                    skill=cluster_name.replace("_", " ").title(),
                    current_level="beginner",
                    target_level="intermediate",
                    priority="high" if cluster_name in ("cloud", "system_design") else "medium",
                    related_roles=target_roles[:3],
                ))

    return gaps


class LearningPipeline:
    def __init__(self, graph=None, event_bus=None, llm_enabled: bool = False):
        self.graph = graph
        self.event_bus = event_bus
        self.llm_enabled = llm_enabled

    async def run(self) -> LearningContext:
        ctx = LearningContext()
        try:
            await self._stage_1_assess(ctx)
            await self._stage_2_plan(ctx)
            await self._stage_3_track(ctx)
            await self._stage_4_nudge(ctx)
            await self._stage_5_report(ctx)
        except Exception as exc:
            ctx.errors.append(f"Pipeline error: {exc}")
            logger.exception("Learning pipeline error")
        return ctx

    async def _stage_1_assess(self, ctx: LearningContext) -> None:
        """Identify skill gaps based on career goals."""
        goals = await get_career_goals()
        gaps = _detect_skill_gaps(goals.target_roles, goals.must_have_criteria)
        ctx.skill_gaps = gaps

        for gap in gaps:
            event = DelegateEvent(
                delegate_id=DELEGATE_ID,
                event_type=EventType.SKILL_ASSESSED,
                trace_id=ctx.trace_id,
                summary=f"Skill gap: {gap.skill} ({gap.current_level} → {gap.target_level})",
                payload={"skill": gap.skill, "priority": gap.priority,
                         "current": gap.current_level, "target": gap.target_level},
            )
            await save_event(event)
            await publish_event(event)
            ctx.events_emitted.append(event)

    async def _stage_2_plan(self, ctx: LearningContext) -> None:
        """Create or update learning paths for identified gaps."""
        existing = await list_learning_paths()
        existing_skills = {p.title.lower() for p in existing}

        for gap in ctx.skill_gaps:
            if gap.skill.lower() in existing_skills:
                continue

            resources = []
            if self.llm_enabled:
                from skills.llm_client import chat
                rec_text = await chat(
                    messages=[
                        {"role": "system", "content": "Suggest 3 specific learning resources (courses, books, projects) for this skill. Return as JSON array with 'title', 'url', 'type' keys."},
                        {"role": "user", "content": f"Skill: {gap.skill}, Level: {gap.current_level} → {gap.target_level}"},
                    ],
                    delegate_id=DELEGATE_ID,
                )
                try:
                    import json
                    resources = json.loads(rec_text)
                except Exception:
                    resources = [{"title": f"Learn {gap.skill}", "url": "", "type": "course", "completed": False}]
            else:
                resources = [
                    {"title": f"Introduction to {gap.skill}", "url": "", "type": "course", "completed": False},
                    {"title": f"{gap.skill} hands-on project", "url": "", "type": "project", "completed": False},
                    {"title": f"Advanced {gap.skill}", "url": "", "type": "course", "completed": False},
                ]

            path = LearningPath(
                title=gap.skill,
                skill_gaps=[gap],
                resources=resources,
                progress_pct=0.0,
            )
            await save_learning_path(path)
            ctx.paths_created.append(path)

            event = DelegateEvent(
                delegate_id=DELEGATE_ID,
                event_type=EventType.LEARNING_PATH_CREATED,
                trace_id=ctx.trace_id,
                summary=f"Learning path created: {gap.skill} ({len(resources)} resources)",
                payload={"path_id": path.path_id, "skill": gap.skill, "resources": len(resources)},
            )
            await save_event(event)
            await publish_event(event)
            ctx.events_emitted.append(event)

    async def _stage_3_track(self, ctx: LearningContext) -> None:
        """Update progress on existing learning paths."""
        paths = await list_learning_paths()
        for path in paths:
            if not path.resources:
                continue
            completed = sum(1 for r in path.resources if r.get("completed"))
            new_pct = round(completed / len(path.resources) * 100, 1)
            if new_pct != path.progress_pct:
                path.progress_pct = new_pct
                await save_learning_path(path)
                event = DelegateEvent(
                    delegate_id=DELEGATE_ID,
                    event_type=EventType.LEARNING_PROGRESS,
                    trace_id=ctx.trace_id,
                    summary=f"Progress: {path.title} at {new_pct}%",
                    payload={"path_id": path.path_id, "progress": new_pct},
                )
                await save_event(event)
                await publish_event(event)
                ctx.events_emitted.append(event)

    async def _stage_4_nudge(self, ctx: LearningContext) -> None:
        """Generate learning nudges for stale paths."""
        paths = await list_learning_paths()
        now = datetime.now(timezone.utc)

        for path in paths:
            if path.progress_pct >= 100:
                continue
            days_since_update = (now - path.updated_at).days
            if days_since_update >= 3:
                nudge = f"Haven't made progress on '{path.title}' in {days_since_update} days. Time to pick it back up?"
                ctx.nudges.append(nudge)
                event = DelegateEvent(
                    delegate_id=DELEGATE_ID,
                    event_type=EventType.LEARNING_NUDGE,
                    trace_id=ctx.trace_id,
                    summary=nudge,
                    payload={"path_id": path.path_id, "days_stale": days_since_update},
                )
                await save_event(event)
                await publish_event(event)
                ctx.events_emitted.append(event)

    async def _stage_5_report(self, ctx: LearningContext) -> None:
        """Produce summary for the digest."""
        # Report data is consumed by the cross-delegate digest
        pass
