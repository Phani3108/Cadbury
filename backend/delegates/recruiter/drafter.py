"""
ResponseDrafter — generates email reply drafts for recruiter opportunities.
Picks template (engage / hold / decline) based on policy decision,
then calls LLM (or produces deterministic mock in test mode).
"""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from memory.models import CareerGoals, JobOpportunity

_PROMPTS_DIR = Path(__file__).parent / "prompts"


def _load_prompt(name: str) -> str:
    return (_PROMPTS_DIR / name).read_text()


# ─── Mock drafts (LLM disabled) ───────────────────────────────────────────────

_MOCK_ENGAGE = """\
Hi {recruiter_name},

Thanks for reaching out about the {role} role at {company}. This sounds genuinely interesting — \
I'm particularly drawn to the {stage} stage and the scope of the position.

A couple of quick questions before we set up a call:
1. What does the remote/hybrid arrangement look like in practice?
2. Can you share the target comp range for this level?

I'm open for a 30-min call. Happy to do {slot_1} or {slot_2} — whichever works for you.

Best,
"""

_MOCK_HOLD = """\
Hi {recruiter_name},

Thanks for thinking of me for the {role} at {company}. The role sounds interesting, \
though I'd love to learn a bit more before committing to a conversation.

Could you share the full JD plus the comp target? That would help me give you a more \
useful answer.

Thanks,
"""

_MOCK_DECLINE = """\
Hi {recruiter_name},

Thank you for reaching out about the {role} position at {company}. I appreciate you thinking of me.

After reviewing the details, I don't think this is the right fit for me at this stage — \
but I'd be happy to reconnect if something more aligned comes up in the future.

Best of luck with the search,
"""


def _mock_draft(response_type: str, opportunity: "JobOpportunity") -> str:
    template = {
        "engage": _MOCK_ENGAGE,
        "hold": _MOCK_HOLD,
        "decline": _MOCK_DECLINE,
    }.get(response_type, _MOCK_HOLD)

    recruiter_name = "there"
    # Try to get first name from the company (best-effort)
    if opportunity.company:
        recruiter_name = opportunity.company.split()[0]

    return template.format(
        recruiter_name=recruiter_name,
        role=opportunity.role,
        company=opportunity.company,
        stage="early",
        slot_1="next Tuesday afternoon",
        slot_2="Thursday morning",
    ).strip()


# ─── LLM draft ────────────────────────────────────────────────────────────────

async def _llm_draft(
    response_type: str,
    opportunity: "JobOpportunity",
    goals: "CareerGoals",
    email_body: str = "",
) -> str:
    from skills import llm_client

    system_prompt = _load_prompt("draft_response.txt")

    user_content = f"""Response type: {response_type}
Candidate tone preference: {goals.communication_tone}
Recruiter name: (unknown — use "Hi there" if unsure)

Original email body:
{email_body or "(not available)"}

Job opportunity:
- Company: {opportunity.company}
- Role: {opportunity.role}
- Location: {opportunity.location}
- Remote policy: {opportunity.remote_policy}
- Comp: {_fmt_comp(opportunity)}
- Match score: {opportunity.match_score:.0%}
- Match breakdown: {opportunity.match_breakdown.model_dump()}
- JD summary: {opportunity.jd_summary or "(not provided)"}
"""

    return await llm_client.chat(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        tier="cheap",
    )


def _fmt_comp(opportunity: "JobOpportunity") -> str:
    lo, hi = opportunity.comp_range_min, opportunity.comp_range_max
    if lo and hi:
        return f"₹{lo:,} – ₹{hi:,}"
    if lo:
        return f"₹{lo:,}+"
    if hi:
        return f"up to ₹{hi:,}"
    return "not disclosed"


# ─── Public interface ─────────────────────────────────────────────────────────

async def draft_response(
    response_type: str,
    opportunity: "JobOpportunity",
    goals: "CareerGoals",
    email_body: str = "",
    llm_enabled: bool = True,
) -> str:
    """
    Generate a draft reply.

    Args:
        response_type: "engage" | "hold" | "decline"
        opportunity:   The scored JobOpportunity
        goals:         The user's CareerGoals (for tone)
        email_body:    Original recruiter email body (for LLM context)
        llm_enabled:   If False, use deterministic mock (for tests/demo)

    Returns:
        Draft email body as a string.
    """
    if llm_enabled:
        try:
            return await _llm_draft(response_type, opportunity, goals, email_body)
        except Exception:
            # Fall back to mock on any LLM error
            pass

    return _mock_draft(response_type, opportunity)
