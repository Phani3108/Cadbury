"""Allowlist admin — trust boundary for delegate actions.

Wraps the helpers in `policy.allowlist` so the frontend can see, add, and
remove entries without DB access.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from config.settings import get_settings
from policy.allowlist import (
    list_allowlist,
    add_to_allowlist,
    remove_from_allowlist,
    is_allowed,
)

router = APIRouter(prefix="/v1/allowlist", tags=["allowlist"])


class AllowlistEntry(BaseModel):
    identifier: str = Field(..., min_length=1, max_length=320)
    service: str = "email"


def _env_seed_set() -> set[str]:
    raw = (get_settings().allowlist or "").strip()
    return {e.strip().lower() for e in raw.split(",") if e.strip()}


@router.get("")
async def list_entries():
    """Return every allowlist row, annotated with whether it came from env."""
    rows = await list_allowlist()
    env_seeded = _env_seed_set()
    return [
        {**row, "source": "env" if row["identifier"] in env_seeded else "user"}
        for row in rows
    ]


@router.post("")
async def add_entry(entry: AllowlistEntry):
    identifier = entry.identifier.strip().lower()
    if not identifier:
        raise HTTPException(status_code=400, detail="Identifier required")
    await add_to_allowlist(identifier, service=entry.service)
    return {"identifier": identifier, "service": entry.service, "added": True}


@router.delete("/{identifier}")
async def delete_entry(identifier: str):
    identifier = identifier.strip().lower()
    if identifier in _env_seed_set():
        raise HTTPException(
            status_code=400,
            detail="Entry is seeded from the ALLOWLIST env var — remove it there first.",
        )
    if not await is_allowed(identifier):
        raise HTTPException(status_code=404, detail="Entry not found")
    await remove_from_allowlist(identifier)
    return {"identifier": identifier, "removed": True}
