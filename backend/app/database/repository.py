"""
Job repository for database CRUD operations.

Provides async methods for persisting and retrieving jobs from SQLite.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Tuple

from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from .models import JobModel
from ..models.enums import JobStatus


class JobRepository:
    """
    Repository for job database operations.

    Provides async CRUD operations for job persistence.
    Uses SQLAlchemy async sessions for non-blocking database access.

    Thread Safety:
        This class is NOT thread-safe. Each thread should use its own
        repository instance with its own session. The async session
        factory handles connection pooling safely.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize the repository with a database session.

        Args:
            session: Async SQLAlchemy session.
        """
        self._session = session

    async def create(self, job_model: JobModel) -> JobModel:
        """
        Create a new job in the database.

        Args:
            job_model: The job to persist.

        Returns:
            The persisted job model.
        """
        self._session.add(job_model)
        await self._session.commit()
        await self._session.refresh(job_model)
        return job_model

    async def get(self, job_id: str) -> Optional[JobModel]:
        """
        Get a job by ID.

        Args:
            job_id: The job identifier.

        Returns:
            JobModel if found, None otherwise.
        """
        result = await self._session.execute(
            select(JobModel).where(JobModel.id == job_id)
        )
        return result.scalar_one_or_none()

    async def update(self, job_model: JobModel) -> JobModel:
        """
        Update an existing job in the database.

        Args:
            job_model: The job to update (must already exist).

        Returns:
            The updated job model.
        """
        # Merge handles both insert and update
        merged = await self._session.merge(job_model)
        await self._session.commit()
        return merged

    async def delete(self, job_id: str) -> bool:
        """
        Delete a job from the database.

        Args:
            job_id: The job identifier.

        Returns:
            True if deleted, False if not found.
        """
        result = await self._session.execute(
            delete(JobModel).where(JobModel.id == job_id)
        )
        await self._session.commit()
        return result.rowcount > 0

    async def list_jobs(
        self,
        page: int = 1,
        page_size: int = 20,
        status_filter: Optional[JobStatus] = None,
    ) -> Tuple[List[JobModel], int]:
        """
        List jobs with pagination and optional status filter.

        Args:
            page: Page number (1-indexed).
            page_size: Number of jobs per page.
            status_filter: Optional status to filter by.

        Returns:
            Tuple of (jobs list, total count).
        """
        # Build base query
        query = select(JobModel)
        count_query = select(func.count(JobModel.id))

        if status_filter:
            query = query.where(JobModel.status == status_filter.value)
            count_query = count_query.where(JobModel.status == status_filter.value)

        # Get total count
        total_result = await self._session.execute(count_query)
        total = total_result.scalar() or 0

        # Get paginated results, ordered by created_at descending
        query = (
            query
            .order_by(JobModel.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        result = await self._session.execute(query)
        jobs = list(result.scalars().all())

        return jobs, total

    async def get_recent_completed(self, days: int = 30) -> List[JobModel]:
        """
        Get recently completed jobs for loading into memory on startup.

        Args:
            days: Number of days to look back.

        Returns:
            List of completed jobs within the time window.
        """
        cutoff = datetime.utcnow() - timedelta(days=days)

        result = await self._session.execute(
            select(JobModel)
            .where(JobModel.created_at >= cutoff)
            .where(
                JobModel.status.in_([
                    JobStatus.COMPLETED.value,
                    JobStatus.FAILED.value,
                    JobStatus.CANCELLED.value,
                ])
            )
            .order_by(JobModel.created_at.desc())
        )

        return list(result.scalars().all())

    async def cleanup_old_jobs(self, days: int = 30) -> int:
        """
        Delete jobs older than the specified number of days.

        Args:
            days: Age threshold for deletion.

        Returns:
            Number of jobs deleted.
        """
        cutoff = datetime.utcnow() - timedelta(days=days)

        result = await self._session.execute(
            delete(JobModel).where(JobModel.created_at < cutoff)
        )
        await self._session.commit()

        return result.rowcount
