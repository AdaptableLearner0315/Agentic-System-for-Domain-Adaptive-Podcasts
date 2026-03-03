"""
Pipeline routes for podcast generation.

Handles:
- POST /generate: Start a new generation job
- GET /{id}/status: Get job progress
- GET /{id}/result: Get completed job result
- POST /{id}/cancel: Cancel a running job
- GET /: List all jobs
"""

import asyncio
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends

from ..models.requests import GenerationRequest
from ..models.responses import (
    JobResponse,
    JobListResponse,
    ProgressResponse,
    ResultResponse,
    ErrorResponse,
)
from ..models.enums import JobStatus, PipelineMode
from ..dependencies import get_job_manager, get_pipeline_service, get_file_service
from ..services.job_manager import JobManager
from ..services.pipeline_service import PipelineService
from ..services.file_service import FileService

router = APIRouter()


@router.post(
    "/generate",
    response_model=JobResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        503: {"model": ErrorResponse, "description": "Service unavailable"},
    },
    summary="Start podcast generation",
    description="""
    Start a new podcast generation job.

    Supports three input modes:
    1. **Generation**: Provide only `prompt` to generate original content
    2. **Enhancement**: Provide only `file_ids` to enhance existing content
    3. **Hybrid**: Provide both `prompt` and `file_ids` to generate content informed by files

    The job runs asynchronously. Use the returned job ID to track progress via
    the `/status` endpoint or WebSocket connection.
    """,
)
async def start_generation(
    request: GenerationRequest,
    job_manager: JobManager = Depends(get_job_manager),
    pipeline_service: PipelineService = Depends(get_pipeline_service),
    file_service: FileService = Depends(get_file_service),
) -> JobResponse:
    """
    Start a new podcast generation job.

    Args:
        request: Generation request with prompt and/or file_ids.
        job_manager: Job management service.
        pipeline_service: Pipeline execution service.
        file_service: File management service.

    Returns:
        JobResponse with the new job ID and initial status.

    Raises:
        HTTPException: If request is invalid or service is unavailable.
    """
    # Validate that at least one input is provided
    if not request.prompt and not request.file_ids:
        raise HTTPException(
            status_code=400,
            detail="Either 'prompt' or 'file_ids' must be provided"
        )

    # Validate file_ids if provided
    if request.file_ids:
        for file_id in request.file_ids:
            if not file_service.file_exists(file_id):
                raise HTTPException(
                    status_code=400,
                    detail=f"File not found: {file_id}"
                )

    # Check concurrent job limit
    running_jobs = job_manager.get_running_jobs()
    if len(running_jobs) >= 3:  # Max concurrent jobs
        raise HTTPException(
            status_code=503,
            detail="Maximum concurrent jobs reached. Please wait for a job to complete."
        )

    # Create the job
    job = job_manager.create_job(
        mode=PipelineMode(request.mode),
        prompt=request.prompt,
        file_ids=request.file_ids,
        guidance=request.guidance,
        config=request.config,
    )

    # Start generation as asyncio task (enables cancellation + timeout)
    task = asyncio.create_task(
        pipeline_service.run_job(job_id=job.id, request=request)
    )
    pipeline_service._running_tasks[job.id] = task

    return job


@router.get(
    "/{job_id}/status",
    response_model=ProgressResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Job not found"},
    },
    summary="Get job progress",
    description="Get the current progress of a generation job.",
)
async def get_job_status(
    job_id: str,
    job_manager: JobManager = Depends(get_job_manager),
) -> ProgressResponse:
    """
    Get the current progress of a generation job.

    Args:
        job_id: Unique job identifier.
        job_manager: Job management service.

    Returns:
        ProgressResponse with current phase and progress percentage.

    Raises:
        HTTPException: If job is not found.
    """
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")

    progress = job_manager.get_progress(job_id)
    return progress


@router.get(
    "/{job_id}/result",
    response_model=ResultResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Job not found"},
        400: {"model": ErrorResponse, "description": "Job not completed"},
    },
    summary="Get job result",
    description="Get the final result of a completed generation job.",
)
async def get_job_result(
    job_id: str,
    job_manager: JobManager = Depends(get_job_manager),
) -> ResultResponse:
    """
    Get the final result of a completed generation job.

    Args:
        job_id: Unique job identifier.
        job_manager: Job management service.

    Returns:
        ResultResponse with output paths and generated assets.

    Raises:
        HTTPException: If job is not found or not completed.
    """
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")

    if job.status not in (JobStatus.COMPLETED, JobStatus.FAILED):
        raise HTTPException(
            status_code=400,
            detail=f"Job is not completed. Current status: {job.status}"
        )

    result = job_manager.get_result(job_id)
    if not result:
        raise HTTPException(status_code=404, detail="Result not available")

    return result


@router.post(
    "/{job_id}/cancel",
    response_model=JobResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Job not found"},
        400: {"model": ErrorResponse, "description": "Job cannot be cancelled"},
    },
    summary="Cancel a job",
    description="Cancel a running or pending generation job.",
)
async def cancel_job(
    job_id: str,
    job_manager: JobManager = Depends(get_job_manager),
    pipeline_service: PipelineService = Depends(get_pipeline_service),
) -> JobResponse:
    """
    Cancel a running or pending generation job.

    Args:
        job_id: Unique job identifier.
        job_manager: Job management service.
        pipeline_service: Pipeline execution service.

    Returns:
        Updated JobResponse with cancelled status.

    Raises:
        HTTPException: If job is not found or cannot be cancelled.
    """
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")

    if job.status not in (JobStatus.PENDING, JobStatus.RUNNING):
        raise HTTPException(
            status_code=400,
            detail=f"Job cannot be cancelled. Current status: {job.status}"
        )

    # Cancel the job
    await pipeline_service.cancel_job(job_id)
    job = job_manager.cancel_job(job_id)

    return job


@router.delete(
    "/{job_id}",
    responses={
        404: {"model": ErrorResponse, "description": "Job not found"},
    },
    summary="Delete a job",
    description="Delete a generation job from history.",
)
async def delete_job(
    job_id: str,
    job_manager: JobManager = Depends(get_job_manager),
) -> dict:
    """
    Delete a generation job from history.

    Args:
        job_id: Unique job identifier.
        job_manager: Job management service.

    Returns:
        Confirmation message.

    Raises:
        HTTPException: If job is not found.
    """
    success = job_manager.delete_job(job_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")

    return {"message": "Job deleted", "id": job_id}


@router.get(
    "/",
    response_model=JobListResponse,
    summary="List all jobs",
    description="Get a list of all generation jobs with pagination.",
)
async def list_jobs(
    page: int = 1,
    page_size: int = 20,
    status: Optional[str] = None,
    job_manager: JobManager = Depends(get_job_manager),
) -> JobListResponse:
    """
    Get a list of all generation jobs.

    Args:
        page: Page number (starting from 1).
        page_size: Number of jobs per page.
        status: Filter by job status.
        job_manager: Job management service.

    Returns:
        JobListResponse with paginated job list.
    """
    # Validate status filter
    status_filter = None
    if status:
        try:
            status_filter = JobStatus(status.lower())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status: {status}"
            )

    jobs, total = job_manager.list_jobs(
        page=page,
        page_size=page_size,
        status_filter=status_filter,
    )

    return JobListResponse(
        jobs=jobs,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{job_id}",
    response_model=JobResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Job not found"},
    },
    summary="Get job details",
    description="Get full details of a specific generation job.",
)
async def get_job(
    job_id: str,
    job_manager: JobManager = Depends(get_job_manager),
) -> JobResponse:
    """
    Get full details of a specific generation job.

    Args:
        job_id: Unique job identifier.
        job_manager: Job management service.

    Returns:
        JobResponse with full job details.

    Raises:
        HTTPException: If job is not found.
    """
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")

    return job
