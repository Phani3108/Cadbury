"""
Personal Delegates Network — FastAPI backend entry point.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config.settings import settings
from memory.graph import init_db
from runtime.kernel import DelegateRuntime, set_runtime


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    runtime = DelegateRuntime()
    set_runtime(runtime)
    await runtime.start()
    print("✓ Database initialized")
    print("✓ Delegate runtime started")
    yield
    # Shutdown
    await runtime.stop()
    print("✓ Runtime stopped")


app = FastAPI(
    title="Personal Delegates Network",
    description="Consumer-facing AI agent system with specialized delegates per life domain",
    version="0.1.0",
    lifespan=lifespan,
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

app.include_router(goals_router)
app.include_router(approvals_router)
app.include_router(delegates_router)
app.include_router(events_router)
app.include_router(memory_router)
app.include_router(digest_router)
app.include_router(notifications_router)
app.include_router(contacts_router)
app.include_router(calendar_router)


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
