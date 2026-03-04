"""
Pydantic response models for the Nell API.

These models define the structure of API responses,
ensuring consistent JSON output format.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

from .enums import JobStatus, PipelineMode, GenerationPhase


class HealthResponse(BaseModel):
    """
    Health check response.

    Attributes:
        status: Service status
        version: API version
        timestamp: Current server time
    """
    status: str = Field("healthy", description="Service status")
    version: str = Field(..., description="API version")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ErrorResponse(BaseModel):
    """
    Standard error response.

    Attributes:
        error: Error type/code
        message: Human-readable error message
        details: Additional error details
    """
    error: str = Field(..., description="Error type or code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional details")


class ProgressResponse(BaseModel):
    """
    Real-time progress update for a generation job.

    Attributes:
        job_id: Unique job identifier
        phase: Current generation phase
        message: Human-readable status message
        progress_percent: Overall progress (0-100)
        current_step: Current step number
        total_steps: Total number of steps
        eta_seconds: Estimated time remaining
        preview: Preview content (e.g., script excerpt)
        elapsed_seconds: Time elapsed since start
    """
    job_id: str = Field(..., description="Unique job identifier")
    phase: GenerationPhase = Field(..., description="Current generation phase")
    message: str = Field(..., description="Status message")
    progress_percent: float = Field(0.0, ge=0, le=100)
    current_step: int = Field(0, ge=0)
    total_steps: int = Field(0, ge=0)
    eta_seconds: Optional[float] = Field(None, ge=0)
    preview: Optional[str] = Field(None, description="Preview content")
    elapsed_seconds: float = Field(0.0, ge=0)
    details: Optional[Dict[str, Any]] = None


class AssetInfo(BaseModel):
    """
    Information about a generated asset (TTS, BGM, or image).

    Attributes:
        id: Asset identifier
        filename: Asset filename
        path: File path relative to output directory
        type: Asset type (tts, bgm, image)
        metadata: Additional asset metadata
    """
    id: str
    filename: str
    path: str
    type: str
    duration_seconds: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


class ResultResponse(BaseModel):
    """
    Final result of a completed generation job.

    Attributes:
        job_id: Unique job identifier
        success: Whether generation succeeded
        output_path: Path to final video file
        audio_output_path: Path to final audio file (MP3)
        video_url: URL to download/stream video
        duration_seconds: Total video duration
        script: Enhanced script data
        assets: Generated assets (TTS, BGM, images)
        review_history: Director review history (Pro mode)
        config_used: Configuration used for generation
    """
    job_id: str
    success: bool
    output_path: Optional[str] = None
    audio_output_path: Optional[str] = None
    video_url: Optional[str] = None
    audio_url: Optional[str] = None
    duration_seconds: Optional[float] = None
    script: Optional[Dict[str, Any]] = None
    tts_assets: List[AssetInfo] = Field(default_factory=list)
    bgm_assets: List[AssetInfo] = Field(default_factory=list)
    image_assets: List[AssetInfo] = Field(default_factory=list)
    review_history: Optional[List[Dict[str, Any]]] = None
    config_used: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class JobResponse(BaseModel):
    """
    Information about a generation job.

    Attributes:
        id: Unique job identifier
        status: Current job status
        mode: Pipeline mode used
        created_at: Job creation timestamp
        started_at: Job start timestamp
        completed_at: Job completion timestamp
        prompt: Original prompt (if provided)
        file_ids: Input file IDs (if provided)
        progress: Current progress (if running)
        result: Final result (if completed)
    """
    id: str = Field(..., description="Unique job identifier")
    status: JobStatus = Field(..., description="Current job status")
    mode: PipelineMode = Field(..., description="Pipeline mode")
    created_at: datetime = Field(..., description="Creation timestamp")
    started_at: Optional[datetime] = Field(None, description="Start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    prompt: Optional[str] = None
    file_ids: Optional[List[str]] = None
    guidance: Optional[str] = None
    progress: Optional[ProgressResponse] = None
    result: Optional[ResultResponse] = None
    error: Optional[str] = None


class JobListResponse(BaseModel):
    """
    List of generation jobs.

    Attributes:
        jobs: List of job summaries
        total: Total number of jobs
        page: Current page number
        page_size: Number of jobs per page
    """
    jobs: List[JobResponse]
    total: int
    page: int = 1
    page_size: int = 20


class FileResponse(BaseModel):
    """
    Information about an uploaded file.

    Attributes:
        id: Unique file identifier
        filename: Original filename
        content_type: MIME type
        size_bytes: File size in bytes
        uploaded_at: Upload timestamp
        source_type: Detected source type
        extracted_text: Preview of extracted text
    """
    id: str
    filename: str
    content_type: Optional[str] = None
    size_bytes: int
    uploaded_at: datetime
    source_type: str
    extracted_text: Optional[str] = Field(
        None,
        description="Preview of extracted text (first 500 chars)"
    )


class FileListResponse(BaseModel):
    """
    List of uploaded files.

    Attributes:
        files: List of file information
        total: Total number of files
    """
    files: List[FileResponse]
    total: int


class ModeConfig(BaseModel):
    """
    Configuration for a pipeline mode.

    Attributes:
        name: Mode name
        description: Mode description
        features: List of features enabled
        estimated_duration: Estimated generation time
    """
    name: str
    description: str
    features: List[str]
    estimated_duration: str


class ConfigResponse(BaseModel):
    """
    System configuration response.

    Attributes:
        modes: Available pipeline modes
        supported_formats: Supported input file formats
        max_file_size_mb: Maximum upload file size
    """
    modes: Dict[str, ModeConfig]
    supported_formats: List[str]
    max_file_size_mb: int = 100
