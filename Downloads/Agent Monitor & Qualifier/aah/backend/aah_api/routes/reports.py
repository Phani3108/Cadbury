from __future__ import annotations
from fastapi import APIRouter, HTTPException, Response
from ..services.orchestrator import load_report_html

router = APIRouter()

@router.get("/runs/{run_id}/report")
def get_report(run_id: str):
    try:
        html = load_report_html(run_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Report not found")
    return Response(content=html, media_type="text/html")
