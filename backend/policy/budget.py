"""
Per-delegate budget enforcement.

Tracks LLM token/cost usage per delegate and enforces daily limits.
When a delegate exceeds its budget, LLM calls are blocked and the
delegate is auto-paused.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone

from memory.graph import db

logger = logging.getLogger(__name__)

# Approximate costs per 1M tokens (USD)
MODEL_COST_PER_1M = {
    "gpt-4o-mini": {"prompt": 0.15, "completion": 0.60},
    "gpt-4o": {"prompt": 2.50, "completion": 10.00},
}
DEFAULT_COST = {"prompt": 1.00, "completion": 3.00}


@dataclass
class DelegateBudget:
    delegate_id: str
    daily_token_limit: int = 500_000       # Max tokens per day (0 = unlimited)
    daily_cost_limit_usd: float = 1.00     # Max cost per day in USD (0 = unlimited)
    tokens_used_today: int = 0
    cost_used_today_usd: float = 0.0
    total_tokens_all_time: int = 0
    total_cost_all_time_usd: float = 0.0
    last_reset: str = ""
    is_over_budget: bool = False


async def init_budget_store() -> None:
    """Create delegate_budgets table."""
    async with db() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS delegate_budgets (
                delegate_id          TEXT PRIMARY KEY,
                daily_token_limit    INTEGER NOT NULL DEFAULT 500000,
                daily_cost_limit_usd REAL NOT NULL DEFAULT 1.0,
                tokens_used_today    INTEGER NOT NULL DEFAULT 0,
                cost_used_today_usd  REAL NOT NULL DEFAULT 0.0,
                total_tokens         INTEGER NOT NULL DEFAULT 0,
                total_cost_usd       REAL NOT NULL DEFAULT 0.0,
                last_reset           TEXT NOT NULL DEFAULT ''
            )
        """)
        await conn.commit()


async def get_budget(delegate_id: str) -> DelegateBudget:
    """Get current budget for a delegate. Creates default if missing."""
    await _maybe_reset(delegate_id)
    async with db() as conn:
        rows = await conn.execute_fetchall(
            "SELECT * FROM delegate_budgets WHERE delegate_id = ?",
            (delegate_id,),
        )
        if rows:
            r = rows[0]
            budget = DelegateBudget(
                delegate_id=r["delegate_id"],
                daily_token_limit=r["daily_token_limit"],
                daily_cost_limit_usd=r["daily_cost_limit_usd"],
                tokens_used_today=r["tokens_used_today"],
                cost_used_today_usd=r["cost_used_today_usd"],
                total_tokens_all_time=r["total_tokens"],
                total_cost_all_time_usd=r["total_cost_usd"],
                last_reset=r["last_reset"],
            )
            budget.is_over_budget = _check_over_budget(budget)
            return budget

        # Create default budget
        now = datetime.now(timezone.utc).isoformat()
        await conn.execute(
            """
            INSERT INTO delegate_budgets
            (delegate_id, daily_token_limit, daily_cost_limit_usd, tokens_used_today,
             cost_used_today_usd, total_tokens, total_cost_usd, last_reset)
            VALUES (?, 500000, 1.0, 0, 0.0, 0, 0.0, ?)
            """,
            (delegate_id, now),
        )
        await conn.commit()
        return DelegateBudget(delegate_id=delegate_id, last_reset=now)


async def update_budget_limits(
    delegate_id: str,
    daily_token_limit: int | None = None,
    daily_cost_limit_usd: float | None = None,
) -> DelegateBudget:
    """Update budget limits for a delegate."""
    budget = await get_budget(delegate_id)
    async with db() as conn:
        if daily_token_limit is not None:
            await conn.execute(
                "UPDATE delegate_budgets SET daily_token_limit = ? WHERE delegate_id = ?",
                (daily_token_limit, delegate_id),
            )
            budget.daily_token_limit = daily_token_limit
        if daily_cost_limit_usd is not None:
            await conn.execute(
                "UPDATE delegate_budgets SET daily_cost_limit_usd = ? WHERE delegate_id = ?",
                (daily_cost_limit_usd, delegate_id),
            )
            budget.daily_cost_limit_usd = daily_cost_limit_usd
        await conn.commit()
    budget.is_over_budget = _check_over_budget(budget)
    return budget


async def record_usage(
    delegate_id: str,
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
) -> DelegateBudget:
    """Record token usage for a delegate and check budget limits."""
    total_tokens = prompt_tokens + completion_tokens
    costs = MODEL_COST_PER_1M.get(model, DEFAULT_COST)
    cost_usd = (
        prompt_tokens * costs["prompt"] / 1_000_000
        + completion_tokens * costs["completion"] / 1_000_000
    )

    await _maybe_reset(delegate_id)
    # Ensure budget row exists
    await get_budget(delegate_id)

    async with db() as conn:
        await conn.execute(
            """
            UPDATE delegate_budgets SET
                tokens_used_today = tokens_used_today + ?,
                cost_used_today_usd = cost_used_today_usd + ?,
                total_tokens = total_tokens + ?,
                total_cost_usd = total_cost_usd + ?
            WHERE delegate_id = ?
            """,
            (total_tokens, cost_usd, total_tokens, cost_usd, delegate_id),
        )
        await conn.commit()

    budget = await get_budget(delegate_id)

    # Auto-pause if over budget
    if budget.is_over_budget:
        logger.warning(
            "Delegate %s is OVER BUDGET (tokens: %d/%d, cost: $%.4f/$%.2f) — auto-pausing",
            delegate_id,
            budget.tokens_used_today,
            budget.daily_token_limit,
            budget.cost_used_today_usd,
            budget.daily_cost_limit_usd,
        )
        from runtime.kernel import get_runtime
        runtime = get_runtime()
        if runtime and not runtime.is_paused(delegate_id):
            await runtime.pause(delegate_id)
            # Notify via Telegram
            try:
                from skills.notifications.telegram import send_telegram_message
                await send_telegram_message(
                    f"⚠️ <b>Budget exceeded</b>\n\n"
                    f"Delegate <b>{delegate_id}</b> has been auto-paused.\n"
                    f"Tokens: {budget.tokens_used_today:,}/{budget.daily_token_limit:,}\n"
                    f"Cost: ${budget.cost_used_today_usd:.4f}/${budget.daily_cost_limit_usd:.2f}\n\n"
                    f"<i>Budget resets at midnight UTC. Adjust in /settings.</i>"
                )
            except Exception:
                pass

    return budget


async def check_budget(delegate_id: str) -> bool:
    """Return True if the delegate is within budget. False = over limit."""
    budget = await get_budget(delegate_id)
    return not budget.is_over_budget


async def reset_daily_budgets() -> int:
    """Reset all daily counters. Called by the scheduler at midnight UTC."""
    async with db() as conn:
        now = datetime.now(timezone.utc).isoformat()
        cursor = await conn.execute(
            "UPDATE delegate_budgets SET tokens_used_today = 0, cost_used_today_usd = 0.0, last_reset = ?",
            (now,),
        )
        await conn.commit()
        count = cursor.rowcount

    # Resume any delegates that were auto-paused due to budget
    from runtime.kernel import get_runtime
    runtime = get_runtime()
    if runtime:
        for delegate_id in list(runtime._paused):
            budget = await get_budget(delegate_id)
            if not budget.is_over_budget:
                await runtime.resume(delegate_id)
                logger.info("Auto-resumed delegate %s after budget reset", delegate_id)

    logger.info("Reset daily budgets for %d delegates", count)
    return count


# ─── Internal helpers ─────────────────────────────────────────────────────────

def _check_over_budget(budget: DelegateBudget) -> bool:
    """Check if a budget has exceeded any of its daily limits."""
    if budget.daily_token_limit > 0 and budget.tokens_used_today >= budget.daily_token_limit:
        return True
    if budget.daily_cost_limit_usd > 0 and budget.cost_used_today_usd >= budget.daily_cost_limit_usd:
        return True
    return False


async def _maybe_reset(delegate_id: str) -> None:
    """Auto-reset if we've crossed midnight UTC since last reset."""
    async with db() as conn:
        rows = await conn.execute_fetchall(
            "SELECT last_reset FROM delegate_budgets WHERE delegate_id = ?",
            (delegate_id,),
        )
        if not rows:
            return
        last_reset = rows[0]["last_reset"]
        if not last_reset:
            return

        try:
            last_dt = datetime.fromisoformat(last_reset)
            now = datetime.now(timezone.utc)
            if last_dt.date() < now.date():
                await conn.execute(
                    "UPDATE delegate_budgets SET tokens_used_today = 0, cost_used_today_usd = 0.0, last_reset = ? WHERE delegate_id = ?",
                    (now.isoformat(), delegate_id),
                )
                await conn.commit()
        except Exception:
            pass
