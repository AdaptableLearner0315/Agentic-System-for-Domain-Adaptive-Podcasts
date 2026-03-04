"""
FastAPI dependency injection providers.

This module provides dependency injection for services, ensuring
proper initialization and cleanup of shared resources.
"""

from typing import AsyncGenerator
from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncSession

from .config import get_settings, Settings
from .database.connection import get_async_session
from .database.repository import JobRepository
from .services.job_manager import JobManager
from .services.file_service import FileService
from .services.pipeline_service import PipelineService
from .services.conversation_service import ConversationService


# Global service instances (initialized on first use)
_job_manager: JobManager | None = None
_file_service: FileService | None = None
_pipeline_service: PipelineService | None = None
_conversation_service: ConversationService | None = None


def get_job_manager() -> JobManager:
    """
    Get the JobManager singleton instance.

    The JobManager tracks all generation jobs in memory,
    providing state management and job lifecycle handling.

    Returns:
        JobManager instance.
    """
    global _job_manager
    if _job_manager is None:
        _job_manager = JobManager()
    return _job_manager


def get_file_service() -> FileService:
    """
    Get the FileService singleton instance.

    The FileService handles file uploads, storage, and extraction.

    Returns:
        FileService instance.
    """
    global _file_service
    if _file_service is None:
        settings = get_settings()
        _file_service = FileService(
            upload_dir=settings.upload_path,
            max_size_bytes=settings.max_upload_size_bytes
        )
    return _file_service


def get_pipeline_service() -> PipelineService:
    """
    Get the PipelineService singleton instance.

    The PipelineService orchestrates pipeline execution,
    wrapping the existing Normal and Pro pipelines.

    Returns:
        PipelineService instance.
    """
    global _pipeline_service
    if _pipeline_service is None:
        settings = get_settings()
        _pipeline_service = PipelineService(
            output_dir=settings.output_path,
            job_manager=get_job_manager(),
            file_service=get_file_service(),
        )
    return _pipeline_service


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Get an async database session.

    Provides a SQLAlchemy async session for database operations.
    The session is automatically closed when the request completes.

    Yields:
        AsyncSession for database operations.
    """
    session_factory = get_async_session()
    if session_factory is None:
        # Database not initialized yet
        yield None
        return

    async with session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


async def get_job_repository(
    session: AsyncSession = None
) -> AsyncGenerator[JobRepository, None]:
    """
    Get a job repository instance with a database session.

    Provides a JobRepository for database CRUD operations.
    Creates its own session if one is not provided.

    Args:
        session: Optional async session (uses get_db if not provided).

    Yields:
        JobRepository for job persistence operations.
    """
    session_factory = get_async_session()
    if session_factory is None:
        yield None
        return

    async with session_factory() as session:
        try:
            yield JobRepository(session)
        finally:
            await session.close()


def get_conversation_service() -> ConversationService:
    """
    Get the ConversationService singleton instance.

    The ConversationService manages interactive podcast conversations,
    handling chat sessions and Claude integration.

    Returns:
        ConversationService instance.
    """
    global _conversation_service
    if _conversation_service is None:
        _conversation_service = ConversationService()
    return _conversation_service


def reset_services() -> None:
    """
    Reset all service singletons.

    Used for testing to ensure clean state between tests.
    """
    global _job_manager, _file_service, _pipeline_service, _conversation_service
    _job_manager = None
    _file_service = None
    _pipeline_service = None
    _conversation_service = None
