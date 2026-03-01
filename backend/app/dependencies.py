"""
FastAPI dependency injection providers.

This module provides dependency injection for services, ensuring
proper initialization and cleanup of shared resources.
"""

from typing import AsyncGenerator
from functools import lru_cache

from .config import get_settings, Settings
from .services.job_manager import JobManager
from .services.file_service import FileService
from .services.pipeline_service import PipelineService


# Global service instances (initialized on first use)
_job_manager: JobManager | None = None
_file_service: FileService | None = None
_pipeline_service: PipelineService | None = None


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


async def get_db() -> AsyncGenerator:
    """
    Placeholder for database session dependency.

    Currently not used as jobs are stored in memory.
    Add database implementation here if persistence is needed.

    Yields:
        Database session (placeholder).
    """
    # Placeholder for future database integration
    yield None


def reset_services() -> None:
    """
    Reset all service singletons.

    Used for testing to ensure clean state between tests.
    """
    global _job_manager, _file_service, _pipeline_service
    _job_manager = None
    _file_service = None
    _pipeline_service = None
