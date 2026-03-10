"""
Database connection management.

Provides async SQLAlchemy engine and session factory for SQLite persistence.
"""

from pathlib import Path
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base

from ..config import get_settings

# SQLAlchemy declarative base for models
Base = declarative_base()

# Global engine instance (initialized on startup)
_engine = None
_async_session_factory = None


def get_async_engine():
    """
    Get the async SQLAlchemy engine.

    Returns:
        AsyncEngine instance or None if not initialized.
    """
    return _engine


def get_async_session() -> async_sessionmaker[AsyncSession]:
    """
    Get the async session factory.

    Returns:
        Async session factory or None if not initialized.
    """
    return _async_session_factory


async def init_db() -> None:
    """
    Initialize the database connection and create tables.

    Creates the database file and directory if they don't exist,
    initializes the async engine, and creates all tables.
    """
    global _engine, _async_session_factory

    settings = get_settings()

    # Ensure database directory exists
    db_path = settings.database_path
    db_path.parent.mkdir(parents=True, exist_ok=True)

    # Create async engine
    _engine = create_async_engine(
        settings.database_url,
        echo=settings.db_echo,
        future=True,
    )

    # Create session factory
    _async_session_factory = async_sessionmaker(
        _engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    # Create tables
    async with _engine.begin() as conn:
        # Import models to register them with Base
        from . import models  # noqa: F401

        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """
    Close the database connection.

    Should be called on application shutdown.
    """
    global _engine, _async_session_factory

    if _engine:
        await _engine.dispose()
        _engine = None
        _async_session_factory = None
