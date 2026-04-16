"""
Personal Delegates Network — FastAPI backend entry point.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

import uvicorn
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config.settings import settings
from memory.graph import init_db
from db import dispose_engine
from middleware.auth import require_auth
from policy.allowlist import init_allowlist
from skills.auth.token_store import init_token_store
from policy.budget import init_budget_store
from runtime.kernel import DelegateRuntime, set_runtime


def _run_migrations():
    """Run Alembic migrations programmatically (upgrade to head)."""
    from alembic.config import Config
    from alembic import command
    from pathlib import Path

    cfg = Config(str(Path(__file__).resolve().parent / "alembic.ini"))
    cfg.set_main_option("script_location", str(Path(__file__).resolve().parent / "migrations"))
    cfg.set_main_option("sqlalchemy.url", settings.database_url)
    command.upgrade(cfg, "head")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    _run_migrations()
    await init_db()  # keep for any runtime init (WAL mode etc.)
    await init_allowlist()
    await init_token_store()
    await init_budget_store()
    runtime = DelegateRuntime()
    set_runtime(runtime)
    await runtime.start()
    print("✓ Database migrated & initialized")
    print("✓ Allowlist loaded")
    print("✓ Delegate runtime started")
    if not settings.api_key:
        print("⚠ No API_KEY set — authentication disabled (dev mode)")
    yield
    # Shutdown
    await runtime.stop()
    await dispose_engine()
    print("✓ Runtime stopped")


app = FastAPI(
    title="Personal Delegates Network",
    description="Consumer-facing AI agent system with specialized delegates per life domain",
    version="0.1.0",
    lifespan=lifespan,
    dependencies=[Depends(require_auth)],
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
from api.routes.goals import router as goals_router
from api.routes.approvals import router as approvals_router
from api.routes.delegates import router as delegates_router
from api.routes.events import router as events_router
from api.routes.memory import router as memory_router
from api.routes.digest import router as digest_router
from api.routes.notifications import router as notifications_router
from api.routes.contacts import router as contacts_router
from api.routes.calendar import router as calendar_router
from api.routes.settings import router as settings_router
from api.routes.oauth import router as oauth_router
from api.routes.budgets import router as budgets_router
from api.routes.comms import router as comms_router
from api.routes.finance import router as finance_router
from api.routes.shopping import router as shopping_router
from api.routes.learning import router as learning_router
from api.routes.health import router as health_router
from api.routes.observability import router as observability_router
from api.routes.pipeline_runs import router as pipeline_runs_router
from api.routes.search import router as search_router
from api.routes.chat import router as chat_router
from api.routes.allowlist import router as allowlist_router
from api.routes.voice import router as voice_router

app.include_router(goals_router)
app.include_router(approvals_router)
app.include_router(delegates_router)
app.include_router(events_router)
app.include_router(memory_router)
app.include_router(digest_router)
app.include_router(notifications_router)
app.include_router(contacts_router)
app.include_router(calendar_router)
app.include_router(settings_router)
app.include_router(oauth_router)
app.include_router(budgets_router)
app.include_router(comms_router)
app.include_router(finance_router)
app.include_router(shopping_router)
app.include_router(learning_router)
app.include_router(health_router)
app.include_router(observability_router)
app.include_router(pipeline_runs_router)
app.include_router(search_router)
app.include_router(chat_router)
app.include_router(allowlist_router)
app.include_router(voice_router)


@app.get("/health")
async def health():
    return {"status": "ok", "env": settings.app_env}


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info",
    )
