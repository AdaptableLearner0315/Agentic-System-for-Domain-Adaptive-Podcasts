"""
SQLAlchemy models for database persistence.

Defines the Job, Series, and Episode table models with methods to
convert to/from in-memory state objects.
"""

import json
from datetime import datetime
from typing import Optional, Dict, List, Any

from sqlalchemy import String, Text, Boolean, DateTime, Integer, Float, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

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


class SeriesModel(Base):
    """
    SQLAlchemy model for podcast series.

    Stores series metadata, outline, style DNA, and continuity state.
    Episodes are stored in a separate table with foreign key relationship.
    """

    __tablename__ = "series"

    # Primary key (UUID format)
    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    # Status
    status: Mapped[str] = mapped_column(String(20), nullable=False, index=True)

    # User input
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    guidance: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    mode: Mapped[str] = mapped_column(String(10), nullable=False, default="normal")

    # Series configuration
    series_type: Mapped[str] = mapped_column(String(20), nullable=False, default="documentary")
    episode_length: Mapped[str] = mapped_column(String(10), nullable=False, default="short")
    episode_count: Mapped[int] = mapped_column(Integer, nullable=False)

    # Title and description (from outline)
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # JSON fields for complex data
    outline_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    style_dna_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    continuity_state_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    assets_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Asset path
    assets_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    # Relationship to episodes
    # Using lazy="selectin" for async compatibility
    episodes: Mapped[List["EpisodeModel"]] = relationship(
        "EpisodeModel",
        back_populates="series",
        cascade="all, delete-orphan",
        order_by="EpisodeModel.episode_number",
        lazy="selectin"
    )

    # Indexes
    __table_args__ = (
        Index("idx_series_status_created", "status", "created_at"),
    )

    @property
    def outline(self) -> Optional[Dict[str, Any]]:
        """Deserialize outline from JSON."""
        if self.outline_json:
            return json.loads(self.outline_json)
        return None

    @outline.setter
    def outline(self, value: Optional[Dict[str, Any]]) -> None:
        """Serialize outline to JSON."""
        self.outline_json = json.dumps(value) if value else None

    @property
    def style_dna(self) -> Optional[Dict[str, Any]]:
        """Deserialize style_dna from JSON."""
        if self.style_dna_json:
            return json.loads(self.style_dna_json)
        return None

    @style_dna.setter
    def style_dna(self, value: Optional[Dict[str, Any]]) -> None:
        """Serialize style_dna to JSON."""
        self.style_dna_json = json.dumps(value) if value else None

    @property
    def continuity_state(self) -> Optional[Dict[str, Any]]:
        """Deserialize continuity_state from JSON."""
        if self.continuity_state_json:
            return json.loads(self.continuity_state_json)
        return None

    @continuity_state.setter
    def continuity_state(self, value: Optional[Dict[str, Any]]) -> None:
        """Serialize continuity_state to JSON."""
        self.continuity_state_json = json.dumps(value) if value else None

    @property
    def assets(self) -> Optional[Dict[str, Any]]:
        """Deserialize assets from JSON."""
        if self.assets_json:
            return json.loads(self.assets_json)
        return None

    @assets.setter
    def assets(self, value: Optional[Dict[str, Any]]) -> None:
        """Serialize assets to JSON."""
        self.assets_json = json.dumps(value) if value else None


class EpisodeModel(Base):
    """
    SQLAlchemy model for individual episodes within a series.

    Stores episode-specific data including status, content, and output paths.
    """

    __tablename__ = "episodes"

    # Primary key
    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    # Foreign key to series
    series_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("series.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Episode info
    episode_number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")

    # Job tracking
    job_id: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)

    # Content
    previously_on: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    cliffhanger: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    cliffhanger_type: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    teaser: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # JSON fields
    callbacks_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    script_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Output paths
    output_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    audio_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationship back to series
    series: Mapped["SeriesModel"] = relationship("SeriesModel", back_populates="episodes")

    # Indexes
    __table_args__ = (
        Index("idx_episodes_series_number", "series_id", "episode_number"),
    )

    @property
    def callbacks(self) -> Optional[Dict[str, Any]]:
        """Deserialize callbacks from JSON."""
        if self.callbacks_json:
            return json.loads(self.callbacks_json)
        return None

    @callbacks.setter
    def callbacks(self, value: Optional[Dict[str, Any]]) -> None:
        """Serialize callbacks to JSON."""
        self.callbacks_json = json.dumps(value) if value else None

    @property
    def script(self) -> Optional[Dict[str, Any]]:
        """Deserialize script from JSON."""
        if self.script_json:
            return json.loads(self.script_json)
        return None

    @script.setter
    def script(self, value: Optional[Dict[str, Any]]) -> None:
        """Serialize script to JSON."""
        self.script_json = json.dumps(value) if value else None
