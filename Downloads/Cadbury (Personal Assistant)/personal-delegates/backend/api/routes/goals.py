from fastapi import APIRouter, HTTPException
from memory.graph import get_career_goals, upsert_career_goals
from memory.models import CareerGoals, CareerGoalsUpdate

router = APIRouter(prefix="/v1/user", tags=["goals"])


@router.get("/goals", response_model=CareerGoals)
async def get_goals(user_id: str = "default"):
    return await get_career_goals(user_id)


@router.put("/goals", response_model=CareerGoals)
async def update_goals(updates: CareerGoalsUpdate, user_id: str = "default"):
    current = await get_career_goals(user_id)
    data = current.model_dump()
    patch = updates.model_dump(exclude_none=True)
    data.update(patch)
    updated = CareerGoals.model_validate(data)
    return await upsert_career_goals(updated)
