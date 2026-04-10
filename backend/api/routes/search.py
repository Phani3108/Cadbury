"""Global search — cross-entity keyword search."""

from fastapi import APIRouter
from memory.graph import db

router = APIRouter(prefix="/v1/search", tags=["search"])

# Tables and the columns to search, plus a label for the result
_SEARCHABLE = [
    ("job_opportunities", ["company", "role", "data"], "opportunity"),
    ("recruiter_contacts", ["email", "data"], "contact"),
    ("approval_items", ["data"], "approval"),
    ("delegate_events", ["data"], "event"),
    ("calendar_events", ["title", "data"], "calendar"),
    ("notifications", ["title", "data"], "notification"),
    ("comms_messages", ["sender", "data"], "message"),
    ("memories", ["content"], "memory"),
    ("scratchpad", ["title", "body"], "scratchpad"),
    ("learning_paths", ["title", "data"], "learning"),
    ("health_routines", ["name", "data"], "health_routine"),
    ("health_appointments", ["title", "data"], "health_appointment"),
    ("transactions", ["merchant", "data"], "transaction"),
    ("watch_items", ["name", "data"], "watch_item"),
]


@router.get("")
async def search(q: str, limit: int = 20):
    """Search across all entities. Returns ranked results."""
    if not q or len(q) < 2:
        return []

    results = []
    term = f"%{q}%"
    async with db() as conn:
        for table, columns, entity_type in _SEARCHABLE:
            where_clauses = " OR ".join(f"{col} LIKE ?" for col in columns)
            params = [term] * len(columns)
            try:
                rows = await conn.execute_fetchall(
                    f"SELECT * FROM {table} WHERE {where_clauses} LIMIT 5",
                    params,
                )
                for row in rows:
                    results.append({
                        "type": entity_type,
                        "data": dict(row),
                    })
            except Exception:
                continue  # table might not exist yet

    return results[:limit]
