"""API routes for Learning delegate."""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from memory.graph import list_learning_paths, get_learning_path, save_learning_path

router = APIRouter(prefix="/v1/learning", tags=["learning"])


class ResourceCompletion(BaseModel):
    resource_index: int
    completed: bool


@router.get("/paths")
async def get_learning_paths():
    return await list_learning_paths()


@router.get("/paths/{path_id}")
async def get_path(path_id: str):
    path = await get_learning_path(path_id)
    if not path:
        return {"error": "Path not found"}
    return path


@router.post("/assess")
async def run_assessment():
    """Run skill gap assessment based on career goals."""
    from delegates.learning.pipeline import LearningPipeline
    from config.settings import settings

    pipeline = LearningPipeline(llm_enabled=bool(settings.openai_api_key))
    ctx = await pipeline.run()
    return {
        "skill_gaps": [{"skill": g.skill, "priority": g.priority} for g in ctx.skill_gaps],
        "paths_created": len(ctx.paths_created),
        "nudges": ctx.nudges,
        "errors": ctx.errors,
    }


@router.post("/paths/{path_id}/complete-resource")
async def complete_resource(path_id: str, completion: ResourceCompletion):
    """Mark a learning resource as completed."""
    path = await get_learning_path(path_id)
    if not path:
        return {"error": "Path not found"}
    if completion.resource_index < 0 or completion.resource_index >= len(path.resources):
        return {"error": "Invalid resource index"}

    path.resources[completion.resource_index]["completed"] = completion.completed
    completed_count = sum(1 for r in path.resources if r.get("completed"))
    path.progress_pct = round(completed_count / len(path.resources) * 100, 1)
    await save_learning_path(path)

    return {"progress_pct": path.progress_pct, "completed": completed_count, "total": len(path.resources)}
