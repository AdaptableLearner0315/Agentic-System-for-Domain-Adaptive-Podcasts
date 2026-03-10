"""
Job state management service.

Tracks all generation jobs in memory, providing state management,
job lifecycle handling, and progress tracking.

Active jobs (PENDING/RUNNING) are stored in memory for fast progress updates.
Terminal jobs (COMPLETED/FAILED/CANCELLED) are persisted to SQLite for history.
"""

import uuid
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Tuple, TYPE_CHECKING
from dataclasses import dataclass, field
import threading

from ..models.enums import JobStatus, PipelineMode, GenerationPhase
from ..models.responses import (
    JobResponse,
    ProgressResponse,
    ResultResponse,
    AssetInfo,
    JobLogsResponse,
    LogEntry,
)
from ..logging_config import get_logger
from ..constants import JOB_ID_LENGTH

logger = get_logger("job_manager")

if TYPE_CHECKING:
    from ..database.repository import JobRepository


@dataclass
class JobState:
    """
    Internal job state representation.

    Attributes:
        id: Unique job identifier
        status: Current job status
        mode: Pipeline mode
        created_at: Creation timestamp
        started_at: When job started running
        completed_at: When job finished
        prompt: Original prompt
        file_ids: Input file IDs
        guidance: User guidance
        config: Pro mode configuration
        progress: Current progress state
        result: Final result (when completed)
        error: Error message (when failed)
        cancel_requested: Whether cancellation was requested
    """
    id: str
    status: JobStatus
    mode: PipelineMode
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    prompt: Optional[str] = None
    file_ids: Optional[List[str]] = None
    guidance: Optional[str] = None
    config: Optional[Dict] = None
    progress: Optional[Dict] = None
    result: Optional[Dict] = None
    error: Optional[str] = None
    cancel_requested: bool = False


class JobManager:
    """
    Manages job state and lifecycle.

    Provides thread-safe access to job state, with methods for
    creating, updating, and querying jobs.

    Hybrid storage strategy:
    - Active jobs (PENDING/RUNNING) → stored in memory for fast progress updates
    - Terminal jobs (COMPLETED/FAILED/CANCELLED) → persisted to SQLite

    Attributes:
        _jobs: Dictionary mapping job IDs to job state
        _lock: Thread lock for safe concurrent access
        _db_enabled: Whether database persistence is enabled
        _pending_persists: Queue of job IDs to persist asynchronously
    """

    def __init__(self):
        """Initialize the job manager."""
        self._jobs: Dict[str, JobState] = {}
        self._lock = threading.RLock()
        self._db_enabled: bool = False
        self._pending_persists: List[str] = []

    def enable_persistence(self) -> None:
        """Enable database persistence after database is initialized."""
        self._db_enabled = True

    def _get_session_factory(self):
        """Get the async session factory for database operations."""
        from ..database.connection import get_async_session
        return get_async_session()

    def create_job(
        self,
        mode: PipelineMode,
        prompt: Optional[str] = None,
        file_ids: Optional[List[str]] = None,
        guidance: Optional[str] = None,
        config: Optional[Dict] = None,
    ) -> JobResponse:
        """
        Create a new generation job.

        Args:
            mode: Pipeline mode (normal or pro).
            prompt: Generation prompt.
            file_ids: Input file IDs.
            guidance: User guidance.
            config: Pro mode configuration.

        Returns:
            JobResponse with the new job details.
        """
        job_id = str(uuid.uuid4())[:JOB_ID_LENGTH]

        job_state = JobState(
            id=job_id,
            status=JobStatus.PENDING,
            mode=mode,
            created_at=datetime.utcnow(),
            prompt=prompt,
            file_ids=file_ids,
            guidance=guidance,
            config=config,
        )

        with self._lock:
            self._jobs[job_id] = job_state

        return self._to_response(job_state)

    def get_job(self, job_id: str) -> Optional[JobResponse]:
        """
        Get job details by ID.

        Args:
            job_id: Unique job identifier.

        Returns:
            JobResponse if found, None otherwise.
        """
        with self._lock:
            job_state = self._jobs.get(job_id)
            if job_state:
                return self._to_response(job_state)
        return None

    def start_job(self, job_id: str) -> Optional[JobResponse]:
        """
        Mark a job as running.

        Args:
            job_id: Unique job identifier.

        Returns:
            Updated JobResponse if found, None otherwise.
        """
        with self._lock:
            job_state = self._jobs.get(job_id)
            if job_state:
                job_state.status = JobStatus.RUNNING
                job_state.started_at = datetime.utcnow()
                return self._to_response(job_state)
        return None

    def complete_job(
        self,
        job_id: str,
        result: Dict,
    ) -> Optional[JobResponse]:
        """
        Mark a job as completed with result.

        The job will be queued for database persistence.

        Args:
            job_id: Unique job identifier.
            result: Pipeline result dictionary.

        Returns:
            Updated JobResponse if found, None otherwise.
        """
        with self._lock:
            job_state = self._jobs.get(job_id)
            if job_state:
                job_state.status = JobStatus.COMPLETED
                job_state.completed_at = datetime.utcnow()
                job_state.result = result
                # Queue for persistence
                self._pending_persists.append(job_id)
                return self._to_response(job_state)
        return None

    def fail_job(
        self,
        job_id: str,
        error: str,
    ) -> Optional[JobResponse]:
        """
        Mark a job as failed with error.

        The job will be queued for database persistence.

        Args:
            job_id: Unique job identifier.
            error: Error message.

        Returns:
            Updated JobResponse if found, None otherwise.
        """
        with self._lock:
            job_state = self._jobs.get(job_id)
            if job_state:
                job_state.status = JobStatus.FAILED
                job_state.completed_at = datetime.utcnow()
                job_state.error = error
                # Queue for persistence
                self._pending_persists.append(job_id)
                return self._to_response(job_state)
        return None

    def cancel_job(self, job_id: str) -> Optional[JobResponse]:
        """
        Mark a job as cancelled.

        The job will be queued for database persistence.

        Args:
            job_id: Unique job identifier.

        Returns:
            Updated JobResponse if found, None otherwise.
        """
        with self._lock:
            job_state = self._jobs.get(job_id)
            if job_state:
                job_state.status = JobStatus.CANCELLED
                job_state.completed_at = datetime.utcnow()
                job_state.cancel_requested = True
                # Queue for persistence
                self._pending_persists.append(job_id)
                return self._to_response(job_state)
        return None

    def request_cancellation(self, job_id: str) -> bool:
        """
        Request cancellation of a job.

        The pipeline should check this flag and stop gracefully.

        Args:
            job_id: Unique job identifier.

        Returns:
            True if job exists and cancellation was requested.
        """
        with self._lock:
            job_state = self._jobs.get(job_id)
            if job_state:
                job_state.cancel_requested = True
                return True
        return False

    def delete_job(self, job_id: str) -> bool:
        """
        Delete a job from storage.

        Args:
            job_id: Unique job identifier.

        Returns:
            True if job was found and deleted, False otherwise.
        """
        with self._lock:
            if job_id in self._jobs:
                del self._jobs[job_id]
                return True
        return False

    def is_cancellation_requested(self, job_id: str) -> bool:
        """
        Check if cancellation was requested for a job.

        Args:
            job_id: Unique job identifier.

        Returns:
            True if cancellation was requested.
        """
        with self._lock:
            job_state = self._jobs.get(job_id)
            return job_state.cancel_requested if job_state else False

    def update_progress(
        self,
        job_id: str,
        phase: GenerationPhase,
        message: str,
        progress_percent: float = 0.0,
        current_step: int = 0,
        total_steps: int = 0,
        eta_seconds: Optional[float] = None,
        preview: Optional[str] = None,
        details: Optional[Dict] = None,
    ) -> Optional[ProgressResponse]:
        """
        Update job progress.

        Args:
            job_id: Unique job identifier.
            phase: Current generation phase.
            message: Status message.
            progress_percent: Overall progress (0-100).
            current_step: Current step number.
            total_steps: Total steps.
            eta_seconds: Estimated time remaining.
            preview: Preview content.
            details: Additional details.

        Returns:
            Updated ProgressResponse if job exists.
        """
        with self._lock:
            job_state = self._jobs.get(job_id)
            if job_state:
                elapsed = 0.0
                if job_state.started_at:
                    elapsed = (datetime.utcnow() - job_state.started_at).total_seconds()

                job_state.progress = {
                    "phase": phase,
                    "message": message,
                    "progress_percent": progress_percent,
                    "current_step": current_step,
                    "total_steps": total_steps,
                    "eta_seconds": eta_seconds,
                    "preview": preview,
                    "details": details or {},
                    "elapsed_seconds": elapsed,
                }

                return ProgressResponse(
                    job_id=job_id,
                    phase=phase,
                    message=message,
                    progress_percent=progress_percent,
                    current_step=current_step,
                    total_steps=total_steps,
                    eta_seconds=eta_seconds,
                    preview=preview,
                    elapsed_seconds=elapsed,
                    details=details,
                )
        return None

    def get_progress(self, job_id: str) -> Optional[ProgressResponse]:
        """
        Get current progress for a job.

        Args:
            job_id: Unique job identifier.

        Returns:
            ProgressResponse if job exists and has progress.
        """
        with self._lock:
            job_state = self._jobs.get(job_id)
            if job_state:
                if job_state.progress:
                    return ProgressResponse(
                        job_id=job_id,
                        phase=job_state.progress["phase"],
                        message=job_state.progress["message"],
                        progress_percent=job_state.progress["progress_percent"],
                        current_step=job_state.progress["current_step"],
                        total_steps=job_state.progress["total_steps"],
                        eta_seconds=job_state.progress.get("eta_seconds"),
                        preview=job_state.progress.get("preview"),
                        elapsed_seconds=job_state.progress.get("elapsed_seconds", 0),
                        details=job_state.progress.get("details"),
                    )
                else:
                    # Return initial progress
                    return ProgressResponse(
                        job_id=job_id,
                        phase=GenerationPhase.INITIALIZING,
                        message="Job queued",
                        progress_percent=0,
                        current_step=0,
                        total_steps=0,
                        elapsed_seconds=0,
                    )
        return None

    def get_result(self, job_id: str) -> Optional[ResultResponse]:
        """
        Get result for a completed job.

        Args:
            job_id: Unique job identifier.

        Returns:
            ResultResponse if job is completed with result.
        """
        with self._lock:
            job_state = self._jobs.get(job_id)
            if job_state and job_state.result:
                result = job_state.result
                return ResultResponse(
                    job_id=job_id,
                    success=result.get("success", False),
                    output_path=result.get("output_path"),
                    audio_output_path=result.get("audio_output_path"),
                    video_url=f"/api/outputs/stream/{job_id}" if result.get("output_path") else None,
                    audio_url=f"/api/outputs/download/{job_id}?file_type=audio" if result.get("audio_output_path") else None,
                    duration_seconds=result.get("duration_seconds"),
                    script=result.get("script"),
                    tts_assets=[
                        AssetInfo(**a) for a in result.get("tts_files", [])
                        if a.get("path")  # Filter out assets with None path
                    ],
                    bgm_assets=[
                        AssetInfo(**a) for a in result.get("bgm_files", [])
                        if a.get("path")  # Filter out assets with None path
                    ],
                    image_assets=[
                        AssetInfo(**a) for a in result.get("image_files", [])
                        if a.get("path")  # Filter out assets with None path
                    ],
                    review_history=result.get("review_history"),
                    config_used=result.get("config_used"),
                    quality_report=result.get("quality_report"),
                    error=result.get("error"),
                )
            elif job_state and job_state.status == JobStatus.FAILED:
                return ResultResponse(
                    job_id=job_id,
                    success=False,
                    error=job_state.error,
                )
        return None

    def get_running_jobs(self) -> List[str]:
        """
        Get IDs of all currently running jobs.

        Returns:
            List of job IDs with RUNNING status.
        """
        with self._lock:
            return [
                job_id for job_id, job in self._jobs.items()
                if job.status == JobStatus.RUNNING
            ]

    def get_job_logs(self, job_id: str) -> Optional[JobLogsResponse]:
        """
        Build execution logs from job progress and state.

        Args:
            job_id: Unique job identifier.

        Returns:
            JobLogsResponse with logs if job exists, None otherwise.
        """
        with self._lock:
            job_state = self._jobs.get(job_id)
            if not job_state:
                return None

            logs: List[LogEntry] = []

            # Log job creation
            logs.append(LogEntry(
                timestamp=job_state.created_at.isoformat(),
                level="INFO",
                message=f"Job created in {job_state.mode.value} mode",
                phase="initializing",
            ))

            if job_state.prompt:
                prompt_preview = (
                    job_state.prompt[:100] + "..."
                    if len(job_state.prompt) > 100
                    else job_state.prompt
                )
                logs.append(LogEntry(
                    timestamp=job_state.created_at.isoformat(),
                    level="INFO",
                    message=f"Prompt: {prompt_preview}",
                    phase="initializing",
                ))

            # Log job start
            if job_state.started_at:
                logs.append(LogEntry(
                    timestamp=job_state.started_at.isoformat(),
                    level="INFO",
                    message="Job started",
                    phase="initializing",
                ))

            # Log progress updates
            if job_state.progress:
                progress = job_state.progress
                phase = progress.get("phase")
                message = progress.get("message", "")
                progress_pct = progress.get("progress_percent", 0)
                elapsed = progress.get("elapsed_seconds", 0)

                # Create a timestamp based on start time + elapsed
                if job_state.started_at:
                    from datetime import timedelta
                    progress_time = job_state.started_at + timedelta(seconds=elapsed)
                    logs.append(LogEntry(
                        timestamp=progress_time.isoformat(),
                        level="INFO",
                        message=f"[{progress_pct:.0f}%] {message}",
                        phase=phase.value if hasattr(phase, 'value') else str(phase),
                    ))

                # Log any details
                details = progress.get("details", {})
                if details:
                    # Log parallel asset status if available
                    for key, value in details.items():
                        if isinstance(value, dict) and "done" in value:
                            done = value.get("done", 0)
                            total = value.get("total", 0)
                            if total > 0:
                                logs.append(LogEntry(
                                    timestamp=progress_time.isoformat() if job_state.started_at else job_state.created_at.isoformat(),
                                    level="INFO",
                                    message=f"{key}: {done}/{total} completed",
                                    phase=phase.value if hasattr(phase, 'value') else str(phase),
                                ))

            # Log completion or failure
            if job_state.completed_at:
                if job_state.status == JobStatus.COMPLETED:
                    logs.append(LogEntry(
                        timestamp=job_state.completed_at.isoformat(),
                        level="INFO",
                        message="Job completed successfully",
                        phase="complete",
                    ))
                    if job_state.result:
                        duration = job_state.result.get("duration_seconds")
                        if duration:
                            logs.append(LogEntry(
                                timestamp=job_state.completed_at.isoformat(),
                                level="INFO",
                                message=f"Output duration: {duration:.1f} seconds",
                                phase="complete",
                            ))
                elif job_state.status == JobStatus.FAILED:
                    logs.append(LogEntry(
                        timestamp=job_state.completed_at.isoformat(),
                        level="ERROR",
                        message=f"Job failed: {job_state.error or 'Unknown error'}",
                        phase="error",
                    ))
                elif job_state.status == JobStatus.CANCELLED:
                    logs.append(LogEntry(
                        timestamp=job_state.completed_at.isoformat(),
                        level="WARNING",
                        message="Job cancelled by user",
                        phase="error",
                    ))

            return JobLogsResponse(
                job_id=job_id,
                status=job_state.status.value,
                mode=job_state.mode.value,
                created_at=job_state.created_at.isoformat(),
                started_at=job_state.started_at.isoformat() if job_state.started_at else None,
                completed_at=job_state.completed_at.isoformat() if job_state.completed_at else None,
                error=job_state.error,
                logs=logs,
            )

    def list_jobs(
        self,
        page: int = 1,
        page_size: int = 20,
        status_filter: Optional[JobStatus] = None,
    ) -> Tuple[List[JobResponse], int]:
        """
        List jobs with pagination.

        Args:
            page: Page number (1-indexed).
            page_size: Jobs per page.
            status_filter: Filter by status.

        Returns:
            Tuple of (jobs list, total count).
        """
        with self._lock:
            # Filter jobs
            jobs = list(self._jobs.values())
            if status_filter:
                jobs = [j for j in jobs if j.status == status_filter]

            # Sort by created_at descending
            jobs.sort(key=lambda j: j.created_at, reverse=True)

            # Paginate
            total = len(jobs)
            start = (page - 1) * page_size
            end = start + page_size
            page_jobs = jobs[start:end]

            return [self._to_response(j) for j in page_jobs], total

    def _to_response(self, job_state: JobState) -> JobResponse:
        """
        Convert internal JobState to JobResponse.

        Args:
            job_state: Internal job state.

        Returns:
            JobResponse for API output.
        """
        progress = None
        if job_state.progress:
            progress = ProgressResponse(
                job_id=job_state.id,
                phase=job_state.progress["phase"],
                message=job_state.progress["message"],
                progress_percent=job_state.progress["progress_percent"],
                current_step=job_state.progress["current_step"],
                total_steps=job_state.progress["total_steps"],
                eta_seconds=job_state.progress.get("eta_seconds"),
                preview=job_state.progress.get("preview"),
                elapsed_seconds=job_state.progress.get("elapsed_seconds", 0),
            )

        result = None
        if job_state.result:
            result = self.get_result(job_state.id)

        return JobResponse(
            id=job_state.id,
            status=job_state.status,
            mode=job_state.mode,
            created_at=job_state.created_at,
            started_at=job_state.started_at,
            completed_at=job_state.completed_at,
            prompt=job_state.prompt,
            file_ids=job_state.file_ids,
            guidance=job_state.guidance,
            progress=progress,
            result=result,
            error=job_state.error,
        )

    # -------------------------------------------------------------------------
    # Database Persistence Methods
    # -------------------------------------------------------------------------

    async def persist_pending_jobs(self) -> int:
        """
        Persist all pending jobs to the database.

        Should be called periodically or after job completion.

        Returns:
            Number of jobs persisted.
        """
        if not self._db_enabled:
            return 0

        session_factory = self._get_session_factory()
        if not session_factory:
            return 0

        # Get pending job IDs atomically
        with self._lock:
            job_ids = self._pending_persists.copy()
            self._pending_persists.clear()

        if not job_ids:
            return 0

        persisted = 0
        async with session_factory() as session:
            from ..database.repository import JobRepository
            repository = JobRepository(session)

            for job_id in job_ids:
                try:
                    await self._persist_job(job_id, repository)
                    persisted += 1
                except Exception as e:
                    logger.warning("Failed to persist job %s: %s", job_id, e)
                    # Re-queue for retry
                    with self._lock:
                        if job_id not in self._pending_persists:
                            self._pending_persists.append(job_id)

        return persisted

    async def _persist_job(self, job_id: str, repository: "JobRepository") -> bool:
        """
        Persist a single job to the database.

        Args:
            job_id: The job ID to persist.
            repository: Repository instance with active session.

        Returns:
            True if successful, False otherwise.
        """
        with self._lock:
            job_state = self._jobs.get(job_id)
            if not job_state:
                return False

        # Import here to avoid circular imports
        from ..database.models import JobModel

        job_model = JobModel.from_job_state(job_state)
        await repository.update(job_model)
        return True

    async def load_jobs_from_db(self, days: int = 30) -> int:
        """
        Load recent jobs from database into memory.

        Should be called during application startup.

        Args:
            days: Number of days of history to load.

        Returns:
            Number of jobs loaded.
        """
        if not self._db_enabled:
            return 0

        session_factory = self._get_session_factory()
        if not session_factory:
            return 0

        try:
            async with session_factory() as session:
                from ..database.repository import JobRepository
                repository = JobRepository(session)

                job_models = await repository.get_recent_completed(days=days)
                loaded = 0

                with self._lock:
                    for model in job_models:
                        # Only load if not already in memory
                        if model.id not in self._jobs:
                            self._jobs[model.id] = model.to_job_state()
                            loaded += 1

                return loaded
        except Exception as e:
            logger.error("Failed to load jobs from database: %s", e)
            return 0

    async def get_job_from_db(self, job_id: str) -> Optional[JobResponse]:
        """
        Get a job from database (fallback when not in memory).

        Args:
            job_id: The job ID to retrieve.

        Returns:
            JobResponse if found in database, None otherwise.
        """
        if not self._db_enabled:
            return None

        session_factory = self._get_session_factory()
        if not session_factory:
            return None

        try:
            async with session_factory() as session:
                from ..database.repository import JobRepository
                repository = JobRepository(session)

                job_model = await repository.get(job_id)
                if job_model:
                    job_state = job_model.to_job_state()
                    # Cache in memory
                    with self._lock:
                        self._jobs[job_id] = job_state
                    return self._to_response(job_state)
        except Exception as e:
            logger.error("Failed to load job %s from database: %s", job_id, e)

        return None

    async def persist_all_jobs(self) -> int:
        """
        Persist all in-memory jobs to database.

        Should be called during graceful shutdown.

        Returns:
            Number of jobs persisted.
        """
        if not self._db_enabled:
            return 0

        session_factory = self._get_session_factory()
        if not session_factory:
            return 0

        # Get all terminal jobs
        with self._lock:
            terminal_jobs = [
                job_id for job_id, job in self._jobs.items()
                if job.status in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED)
            ]

        if not terminal_jobs:
            return 0

        persisted = 0
        async with session_factory() as session:
            from ..database.repository import JobRepository
            repository = JobRepository(session)

            for job_id in terminal_jobs:
                try:
                    await self._persist_job(job_id, repository)
                    persisted += 1
                except Exception as e:
                    logger.error("Failed to persist job %s on shutdown: %s", job_id, e)

        return persisted
