"""
SQLAlchemy models for database persistence.

Defines the Job table model with methods to convert to/from JobState.
"""

import json
from datetime import datetime
from typing import Optional, Dict, List, Any

from sqlalchemy import String, Text, Boolean, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column

from .connection import Base
from ..models.enums import JobStatus, PipelineMode


class JobModel(Base):
    """
    SQLAlchemy model for persisted jobs.

    Stores completed/failed/cancelled jobs in SQLite for history persistence.
    Active jobs (pending/running) remain in memory for fast progress updates.
    """

    __tablename__ = "jobs"

    # Primary key
    id: Mapped[str] = mapped_column(String(8), primary_key=True)

    # Status and mode
    status: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    mode: Mapped[str] = mapped_column(String(10), nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Input data
    prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    file_ids_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    guidance: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    config_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Progress and result
    progress_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    result_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Error and cancellation
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    cancel_requested: Mapped[bool] = mapped_column(Boolean, default=False)

    # Indexes for common queries
    __table_args__ = (
        Index("idx_jobs_status_created", "status", "created_at"),
    )

    @property
    def file_ids(self) -> Optional[List[str]]:
        """Deserialize file_ids from JSON."""
        if self.file_ids_json:
            return json.loads(self.file_ids_json)
        return None

    @file_ids.setter
    def file_ids(self, value: Optional[List[str]]) -> None:
        """Serialize file_ids to JSON."""
        self.file_ids_json = json.dumps(value) if value else None

    @property
    def config(self) -> Optional[Dict[str, Any]]:
        """Deserialize config from JSON."""
        if self.config_json:
            return json.loads(self.config_json)
        return None

    @config.setter
    def config(self, value: Optional[Dict[str, Any]]) -> None:
        """Serialize config to JSON."""
        self.config_json = json.dumps(value) if value else None

    @property
    def progress(self) -> Optional[Dict[str, Any]]:
        """Deserialize progress from JSON."""
        if self.progress_json:
            return json.loads(self.progress_json)
        return None

    @progress.setter
    def progress(self, value: Optional[Dict[str, Any]]) -> None:
        """Serialize progress to JSON."""
        self.progress_json = json.dumps(value) if value else None

    @property
    def result(self) -> Optional[Dict[str, Any]]:
        """Deserialize result from JSON."""
        if self.result_json:
            return json.loads(self.result_json)
        return None

    @result.setter
    def result(self, value: Optional[Dict[str, Any]]) -> None:
        """Serialize result to JSON."""
        self.result_json = json.dumps(value) if value else None

    @classmethod
    def from_job_state(cls, job_state: "JobState") -> "JobModel":
        """
        Create a JobModel from a JobState dataclass.

        Args:
            job_state: The in-memory job state to convert.

        Returns:
            JobModel instance ready for database insertion.
        """
        model = cls(
            id=job_state.id,
            status=job_state.status.value,
            mode=job_state.mode.value,
            created_at=job_state.created_at,
            started_at=job_state.started_at,
            completed_at=job_state.completed_at,
            prompt=job_state.prompt,
            guidance=job_state.guidance,
            error=job_state.error,
            cancel_requested=job_state.cancel_requested,
        )
        # Use setters for JSON fields
        model.file_ids = job_state.file_ids
        model.config = job_state.config
        model.progress = job_state.progress
        model.result = job_state.result
        return model

    def to_job_state(self) -> "JobState":
        """
        Convert this JobModel to a JobState dataclass.

        Returns:
            JobState instance for in-memory use.
        """
        from ..services.job_manager import JobState

        return JobState(
            id=self.id,
            status=JobStatus(self.status),
            mode=PipelineMode(self.mode),
            created_at=self.created_at,
            started_at=self.started_at,
            completed_at=self.completed_at,
            prompt=self.prompt,
            file_ids=self.file_ids,
            guidance=self.guidance,
            config=self.config,
            progress=self.progress,
            result=self.result,
            error=self.error,
            cancel_requested=self.cancel_requested,
        )
