"""API routes for Finance delegate."""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from memory.graph import list_transactions, list_subscriptions, save_subscription
from memory.models import Transaction, Subscription, TransactionCategory

router = APIRouter(prefix="/v1/finance", tags=["finance"])


class TransactionInput(BaseModel):
    amount: float
    merchant: str
    category: str = "other"
    notes: str = ""


@router.get("/transactions")
async def get_transactions(limit: int = 100):
    return await list_transactions(limit=limit)


@router.post("/transactions")
async def add_transaction(tx_input: TransactionInput):
    """Manually add a transaction and run finance pipeline."""
    from delegates.finance.pipeline import FinancePipeline
    from config.settings import settings

    tx = Transaction(
        amount=tx_input.amount,
        merchant=tx_input.merchant,
        category=TransactionCategory(tx_input.category) if tx_input.category != "other" else TransactionCategory.OTHER,
        notes=tx_input.notes,
    )
    pipeline = FinancePipeline(llm_enabled=bool(settings.openai_api_key))
    ctx = await pipeline.run([tx])
    return {
        "ingested": len(ctx.transactions_ingested),
        "recurring_detected": len(ctx.recurring_detected),
        "alerts": ctx.alerts,
        "recommendations": ctx.recommendations,
        "errors": ctx.errors,
    }


@router.get("/subscriptions")
async def get_subscriptions(status: str | None = None):
    return await list_subscriptions(status=status)


@router.post("/subscriptions/{subscription_id}/cancel")
async def cancel_subscription(subscription_id: str):
    subs = await list_subscriptions()
    for sub in subs:
        if sub.subscription_id == subscription_id:
            sub.status = "cancelled"
            await save_subscription(sub)
            return {"status": "cancelled", "merchant": sub.merchant}
    return {"error": "Subscription not found"}
