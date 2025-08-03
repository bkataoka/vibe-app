import contextlib
from typing import AsyncGenerator, AsyncContextManager
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
    AsyncEngine,
)
from sqlalchemy.orm import DeclarativeBase

from core.config import settings

# Create async engine
engine: AsyncEngine = create_async_engine(
    settings.SQLITE_URL,
    echo=settings.DB_ECHO,  # Set to True to log all SQL queries
    pool_pre_ping=True,  # Enable connection health checks
    pool_size=settings.DB_POOL_SIZE,  # Maximum number of connections
    max_overflow=settings.DB_MAX_OVERFLOW,  # Maximum number of connections above pool_size
    pool_recycle=settings.DB_POOL_RECYCLE,  # Recycle connections after this many seconds
    connect_args={
        "check_same_thread": False,  # Required for SQLite
        "timeout": settings.DB_TIMEOUT,  # Connection timeout in seconds
    }
)

# Create async session factory
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,  # Don't automatically flush changes to DB
)


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


async def init_db() -> None:
    """Initialize database by creating all tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get DB session."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@contextlib.asynccontextmanager
async def get_db_session() -> AsyncContextManager[AsyncSession]:
    """Context manager to get DB session.
    
    Use this when you need more control over the session lifecycle,
    such as in background tasks or WebSocket connections.
    
    Example:
        async with get_db_session() as session:
            result = await session.execute(query)
            await session.commit()
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def dispose_db() -> None:
    """Dispose database engine.
    
    Call this when shutting down the application to properly
    close all database connections.
    """
    await engine.dispose() 