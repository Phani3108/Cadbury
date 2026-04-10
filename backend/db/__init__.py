"""
SQLAlchemy async engine + session factory.
Supports both SQLite (aiosqlite) and PostgreSQL (asyncpg) via DATABASE_URL.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from config.settings import settings

_engine = None
_session_factory = None


def get_engine():
    global _engine
    if _engine is None:
        url = settings.database_url
        connect_args = {}
        if url.startswith("sqlite"):
            connect_args = {"check_same_thread": False}
        _engine = create_async_engine(
            url,
            echo=settings.debug and settings.app_env == "development",
            connect_args=connect_args,
            pool_pre_ping=True,
        )
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _session_factory


async def get_session() -> AsyncSession:
    """Dependency for FastAPI routes."""
    factory = get_session_factory()
    async with factory() as session:
        yield session


async def dispose_engine():
    global _engine, _session_factory
    if _engine:
        await _engine.dispose()
        _engine = None
        _session_factory = None
