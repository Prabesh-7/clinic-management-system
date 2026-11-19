from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    global _engine

    if _engine is None:
        database_url = get_settings().database_url
        if not database_url:
            raise RuntimeError(
                "DATABASE_URL is not configured. Copy Backend/.env.example "
                "to Backend/.env and set the PostgreSQL connection string."
            )

        if not database_url.startswith("postgresql+asyncpg://"):
            raise RuntimeError(
                "DATABASE_URL must use the postgresql+asyncpg:// async driver."
            )

        _engine = create_async_engine(
            database_url,
            pool_pre_ping=True,
            pool_recycle=1800,
        )

    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    global _session_factory

    if _session_factory is None:
        _session_factory = async_sessionmaker(
            bind=get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )

    return _session_factory


async def get_db() -> AsyncIterator[AsyncSession]:
    async with get_session_factory()() as session:
        yield session


async def close_database() -> None:
    global _engine, _session_factory

    if _engine is not None:
        await _engine.dispose()

    _engine = None
    _session_factory = None
