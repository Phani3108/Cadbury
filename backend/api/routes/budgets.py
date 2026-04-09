"""Budget management API routes."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from policy.budget import get_budget, update_budget_limits
from skills.llm_client import get_usage_stats

router = APIRouter(prefix="/v1/budgets", tags=["budgets"])


class BudgetResponse(BaseModel):
    delegate_id: str
    daily_token_limit: int
    daily_cost_limit_usd: float
    tokens_used_today: int
    cost_used_today_usd: float
    total_tokens_all_time: int
    total_cost_all_time_usd: float
    is_over_budget: bool
    token_usage_pct: float
    cost_usage_pct: float


class BudgetUpdate(BaseModel):
    daily_token_limit: Optional[int] = None
    daily_cost_limit_usd: Optional[float] = None


@router.get("/{delegate_id}", response_model=BudgetResponse)
async def get_delegate_budget(delegate_id: str):
    budget = await get_budget(delegate_id)
    token_pct = (
        (budget.tokens_used_today / budget.daily_token_limit * 100)
        if budget.daily_token_limit > 0
        else 0
    )
    cost_pct = (
        (budget.cost_used_today_usd / budget.daily_cost_limit_usd * 100)
        if budget.daily_cost_limit_usd > 0
        else 0
    )
    return BudgetResponse(
        delegate_id=budget.delegate_id,
        daily_token_limit=budget.daily_token_limit,
        daily_cost_limit_usd=budget.daily_cost_limit_usd,
        tokens_used_today=budget.tokens_used_today,
        cost_used_today_usd=budget.cost_used_today_usd,
        total_tokens_all_time=budget.total_tokens_all_time,
        total_cost_all_time_usd=budget.total_cost_all_time_usd,
        is_over_budget=budget.is_over_budget,
        token_usage_pct=round(token_pct, 1),
        cost_usage_pct=round(cost_pct, 1),
    )


@router.put("/{delegate_id}", response_model=BudgetResponse)
async def update_delegate_budget(delegate_id: str, update: BudgetUpdate):
    budget = await update_budget_limits(
        delegate_id,
        daily_token_limit=update.daily_token_limit,
        daily_cost_limit_usd=update.daily_cost_limit_usd,
    )
    token_pct = (
        (budget.tokens_used_today / budget.daily_token_limit * 100)
        if budget.daily_token_limit > 0
        else 0
    )
    cost_pct = (
        (budget.cost_used_today_usd / budget.daily_cost_limit_usd * 100)
        if budget.daily_cost_limit_usd > 0
        else 0
    )
    return BudgetResponse(
        delegate_id=budget.delegate_id,
        daily_token_limit=budget.daily_token_limit,
        daily_cost_limit_usd=budget.daily_cost_limit_usd,
        tokens_used_today=budget.tokens_used_today,
        cost_used_today_usd=budget.cost_used_today_usd,
        total_tokens_all_time=budget.total_tokens_all_time,
        total_cost_all_time_usd=budget.total_cost_all_time_usd,
        is_over_budget=budget.is_over_budget,
        token_usage_pct=round(token_pct, 1),
        cost_usage_pct=round(cost_pct, 1),
    )


@router.get("")
async def list_all_budgets():
    """Return budgets for all known delegates plus global LLM usage."""
    delegate_ids = ["recruiter", "calendar"]
    budgets = []
    for did in delegate_ids:
        budget = await get_budget(did)
        budgets.append({
            "delegate_id": budget.delegate_id,
            "tokens_used_today": budget.tokens_used_today,
            "cost_used_today_usd": round(budget.cost_used_today_usd, 4),
            "daily_token_limit": budget.daily_token_limit,
            "daily_cost_limit_usd": budget.daily_cost_limit_usd,
            "is_over_budget": budget.is_over_budget,
        })
    return {
        "budgets": budgets,
        "global_usage": get_usage_stats(),
    }
