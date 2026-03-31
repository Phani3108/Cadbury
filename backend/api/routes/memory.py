from fastapi import APIRouter
from memory.graph import list_opportunities, list_decisions, get_opportunity
from memory.models import JobOpportunity, DecisionLog

router = APIRouter(prefix="/v1/memory", tags=["memory"])


@router.get("/opportunities", response_model=list[JobOpportunity])
async def get_opportunities(limit: int = 100):
    return await list_opportunities(limit)


@router.get("/opportunities/{opportunity_id}", response_model=JobOpportunity)
async def get_opportunity_detail(opportunity_id: str):
    from fastapi import HTTPException
    opp = await get_opportunity(opportunity_id)
    if not opp:
        raise HTTPException(404, "Opportunity not found")
    return opp


@router.get("/decisions", response_model=list[DecisionLog])
async def get_decisions(delegate_id: str | None = None, limit: int = 100):
    return await list_decisions(delegate_id, limit)
