from __future__ import annotations
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..services.orchestrator import load_summary
from ..services.remediation import harden_run

router = APIRouter()

class HardenResult(BaseModel):
    run_id: str
    agent: str
    environment: str
    files_changed: list[str]
    git_branch: str | None = None
    commit: str | None = None
    next_steps: str

@router.post("/runs/{run_id}/harden", response_model=HardenResult)
def harden(run_id: str):
    try:
        summary = load_summary(run_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Run not found")
    try:
        plan = harden_run(run_id, summary.agent, summary.environment)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Harden failed: {e}")
    return plan
