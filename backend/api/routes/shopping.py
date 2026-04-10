"""API routes for Shopping delegate."""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from memory.graph import list_watch_items, save_watch_item, get_watch_item
from memory.models import WatchItem

router = APIRouter(prefix="/v1/shopping", tags=["shopping"])


class WatchItemInput(BaseModel):
    name: str
    target_price: float | None = None
    url: str = ""
    retailer: str = ""


class PriceUpdate(BaseModel):
    item_id: str
    price: float


@router.get("/watchlist")
async def get_watchlist(status: str | None = None):
    return await list_watch_items(status=status)


@router.post("/watchlist")
async def add_watch_item(item: WatchItemInput):
    watch_item = WatchItem(
        name=item.name,
        target_price=item.target_price,
        url=item.url,
        retailer=item.retailer,
    )
    await save_watch_item(watch_item)
    return watch_item


@router.post("/watchlist/{item_id}/update-price")
async def update_price(item_id: str, update: PriceUpdate):
    """Update price and run shopping pipeline."""
    from delegates.shopping.pipeline import ShoppingPipeline

    pipeline = ShoppingPipeline()
    ctx = await pipeline.run(price_updates={item_id: update.price})
    return {
        "items_checked": len(ctx.items_checked),
        "price_drops": ctx.price_drops,
        "deals": ctx.deals,
        "errors": ctx.errors,
    }


@router.delete("/watchlist/{item_id}")
async def remove_watch_item(item_id: str):
    item = await get_watch_item(item_id)
    if item:
        item.status = "removed"
        await save_watch_item(item)
        return {"status": "removed"}
    return {"error": "Item not found"}
