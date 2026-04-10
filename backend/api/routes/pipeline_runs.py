"""Pipeline runs — list & inspect delegate pipeline executions."""

from fastapi import APIRouter
from memory.graph import list_pipeline_runs, get_pipeline_run

router = APIRouter(prefix="/v1/pipeline-runs", tags=["pipeline-runs"])


@router.get("")
async def list_runs(delegate_id: str | None = None, status: str | None = None, limit: int = 50):
    return await list_pipeline_runs(delegate_id=delegate_id, status=status, limit=limit)


@router.get("/{run_id}")
async def get_run(run_id: str):
    run = await get_pipeline_run(run_id)
    if not run:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Pipeline run not found")
    return run
