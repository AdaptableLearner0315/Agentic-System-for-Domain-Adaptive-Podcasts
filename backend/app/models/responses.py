"""
Pydantic response models for the Nell API.

These models define the structure of API responses,
ensuring consistent JSON output format.
"""

from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
from pydantic import BaseModel, Field

from .enums import JobStatus, PipelineMode, GenerationPhase


# =============================================================================
# Quality Models
# =============================================================================

class QualityScore(BaseModel):
    """
    Quality score for a single dimension.

    Attributes:
        dimension: Name of the quality dimension (script, pacing, voice, etc.)
        score: Numeric score 0-100, None if not yet evaluated
        grade: Letter grade (A, B+, C, etc.), None if not yet evaluated
        status: Evaluation status
        issues: List of issues detected for this dimension
    """
    dimension: str = Field(..., description="Quality dimension name")
    score: Optional[int] = Field(None, ge=0, le=100, description="Score 0-100")
    grade: Optional[str] = Field(None, description="Letter grade (A, B+, C, etc.)")
    status: Literal["pending", "evaluating", "complete", "error"] = Field(
        "pending", description="Evaluation status"
    )
    issues: List[str] = Field(default_factory=list, description="Issues detected")


class QualityTrace(BaseModel):
    """
    Explainable quality trace for a single dimension.

    Provides human-readable reasoning, strengths, weaknesses, and suggestions
    for understanding why a quality score is what it is.

    Attributes:
        dimension: Quality dimension name
        score: Numeric score 0-100
        grade: Letter grade
        reasoning: 1-2 sentence human-readable explanation
        strengths: What's working well (green indicators)
        weaknesses: What's holding the score back (orange indicators)
        suggestions: Pro mode only - actionable fixes
        sequence: Evaluation order (1=first, 8=last)
        raw_metrics: Debug data - measurements that fed into score
        enhanced: True if reasoning was LLM-enhanced (Pro mode)
    """
    dimension: str = Field(..., description="Quality dimension name")
    score: int = Field(0, ge=0, le=100, description="Score 0-100")
    grade: str = Field("F", description="Letter grade")
    reasoning: str = Field("", description="Human-readable explanation")
    strengths: List[str] = Field(default_factory=list, description="What's working well")
    weaknesses: List[str] = Field(default_factory=list, description="Areas for improvement")
    suggestions: List[str] = Field(default_factory=list, description="Pro mode actionable fixes")
    sequence: int = Field(0, ge=0, description="Evaluation order (1=first)")
    raw_metrics: Dict[str, Any] = Field(default_factory=dict, description="Debug metrics")
    enhanced: bool = Field(False, description="True if LLM-enhanced")


class QualityReport(BaseModel):
    """
    Comprehensive quality report for a generation job.

    Attributes:
        overall_score: Weighted overall score 0-100
        overall_grade: Letter grade for overall quality
        scores: List of per-dimension quality scores
        traces: Full explainable traces for each dimension (includes reasoning)
        issues: All detected issues across dimensions
        recommendations: Actionable recommendations for improvement
    """
    overall_score: Optional[int] = Field(None, ge=0, le=100, description="Overall score")
    overall_grade: Optional[str] = Field(None, description="Overall letter grade")
    scores: List[QualityScore] = Field(default_factory=list, description="Per-dimension scores")
    traces: List[QualityTrace] = Field(default_factory=list, description="Explainable quality traces")
    issues: List[str] = Field(default_factory=list, description="All detected issues")
    recommendations: List[str] = Field(default_factory=list, description="Improvement recommendations")


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
        quality: Real-time quality metrics (populated as evaluation progresses)
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
    quality: Optional[QualityReport] = Field(None, description="Real-time quality metrics")


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
        quality_report: Final quality evaluation report
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
    quality_report: Optional[QualityReport] = Field(None, description="Final quality evaluation report")
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


class LogEntry(BaseModel):
    """
    Individual log entry for job execution.

    Attributes:
        timestamp: When the log entry was created
        level: Log level (INFO, ERROR, WARNING)
        message: Log message
        phase: Generation phase when log was created
    """
    timestamp: str
    level: str = Field(..., description="Log level: INFO, ERROR, WARNING")
    message: str
    phase: Optional[str] = None


class JobLogsResponse(BaseModel):
    """
    Execution logs for a job.

    Attributes:
        job_id: Unique job identifier
        status: Current job status
        mode: Pipeline mode used
        created_at: Job creation timestamp
        started_at: Job start timestamp
        completed_at: Job completion timestamp
        error: Error message if job failed
        logs: List of log entries
    """
    job_id: str
    status: str
    mode: str
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None
    logs: List[LogEntry] = Field(default_factory=list)
