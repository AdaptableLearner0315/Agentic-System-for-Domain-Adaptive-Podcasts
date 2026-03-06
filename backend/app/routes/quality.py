"""
Quality routes for trace queries and analytics.

Handles:
- GET /{job_id}: Get full quality report for a job
- GET /{job_id}/traces: Get all dimension traces
- GET /{job_id}/trace/{dimension}: Get single trace
- GET /jobs: List jobs with quality scores
- POST /check: CI/CD quality threshold check
- GET /stats: Aggregate quality statistics
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from utils.evaluation_store import get_evaluation_store, EvaluationStore


router = APIRouter()


# =============================================================================
# Response Models
# =============================================================================

class TraceResponse(BaseModel):
    """Single dimension trace."""
    dimension: str
    score: int
    grade: str
    reasoning: Optional[str] = None
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)
    sequence: int
    raw_metrics: Optional[dict] = None
    enhanced: bool = False


class IssueResponse(BaseModel):
    """Quality issue."""
    dimension: str
    severity: str
    message: str


class QualityReportResponse(BaseModel):
    """Full quality report for a job."""
    job_id: str
    mode: str
    prompt: Optional[str] = None
    status: str
    created_at: Optional[str] = None
    completed_at: Optional[str] = None
    overall_score: Optional[int] = None
    overall_grade: Optional[str] = None
    output_dir: Optional[str] = None
    duration_seconds: Optional[float] = None
    traces: List[TraceResponse] = Field(default_factory=list)
    issues: List[IssueResponse] = Field(default_factory=list)


class JobSummary(BaseModel):
    """Summary of a job for list view."""
    id: str
    mode: str
    status: str
    overall_score: Optional[int] = None
    overall_grade: Optional[str] = None
    duration_seconds: Optional[float] = None
    created_at: Optional[str] = None


class JobListResponse(BaseModel):
    """List of jobs."""
    jobs: List[JobSummary]
    total: int


class ThresholdCheckRequest(BaseModel):
    """Request for threshold check."""
    job_id: str
    min_score: int = Field(default=80, ge=0, le=100)


class ThresholdCheckResponse(BaseModel):
    """Result of threshold check."""
    passed: bool
    job_id: str
    overall_score: Optional[int] = None
    overall_grade: Optional[str] = None
    min_score: int
    failing_dimensions: List[dict] = Field(default_factory=list)
    error: Optional[str] = None


class StatsResponse(BaseModel):
    """Aggregate statistics."""
    total_jobs: int
    avg_score: Optional[float] = None
    min_score: Optional[int] = None
    max_score: Optional[int] = None
    avg_duration_seconds: Optional[float] = None
    period_days: int
    mode_filter: Optional[str] = None


# =============================================================================
# Dependency
# =============================================================================

def get_store() -> EvaluationStore:
    """Get evaluation store instance."""
    return get_evaluation_store()


# =============================================================================
# Routes - Static paths MUST come before dynamic /{job_id} paths
# =============================================================================

@router.get(
    "/jobs",
    response_model=JobListResponse,
    summary="List jobs",
    description="List jobs with quality scores. Filter by mode, status, or minimum score."
)
async def list_jobs(
    mode: Optional[str] = Query(None, description="Filter by mode (normal, pro, ultra)"),
    status: Optional[str] = Query(None, description="Filter by status (running, completed, failed)"),
    min_score: Optional[int] = Query(None, ge=0, le=100, description="Minimum overall score"),
    limit: int = Query(50, ge=1, le=200, description="Maximum results"),
):
    """List jobs with optional filters."""
    store = get_store()
    jobs = store.list_jobs(mode=mode, status=status, min_score=min_score, limit=limit)

    return JobListResponse(
        jobs=[
            JobSummary(
                id=j.id,
                mode=j.mode,
                status=j.status,
                overall_score=j.overall_score,
                overall_grade=j.overall_grade,
                duration_seconds=j.duration_seconds,
                created_at=j.created_at,
            )
            for j in jobs
        ],
        total=len(jobs),
    )


@router.post(
    "/check",
    response_model=ThresholdCheckResponse,
    summary="Check quality threshold",
    description="Check if a job meets a quality threshold (for CI/CD pipelines)."
)
async def check_threshold(request: ThresholdCheckRequest):
    """Check if job meets quality threshold."""
    store = get_store()
    result = store.check_threshold(request.job_id, request.min_score)

    return ThresholdCheckResponse(**result)


@router.get(
    "/stats",
    response_model=StatsResponse,
    summary="Get statistics",
    description="Get aggregate quality statistics."
)
async def get_stats(
    mode: Optional[str] = Query(None, description="Filter by mode"),
    days: int = Query(7, ge=1, le=90, description="Number of days to include"),
):
    """Get aggregate quality statistics."""
    store = get_store()
    stats = store.get_stats(mode=mode, days=days)

    return StatsResponse(**stats)


# Dynamic paths with {job_id} must come AFTER static paths
@router.get(
    "/{job_id}",
    response_model=QualityReportResponse,
    summary="Get quality report",
    description="Get full quality report including all traces and issues for a job."
)
async def get_quality_report(job_id: str):
    """Get full quality report for a job."""
    store = get_store()
    report = store.get_full_report(job_id)

    if not report:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    return QualityReportResponse(**report)


@router.get(
    "/{job_id}/traces",
    response_model=List[TraceResponse],
    summary="Get all traces",
    description="Get all dimension traces for a job."
)
async def get_traces(job_id: str):
    """Get all traces for a job."""
    store = get_store()
    traces = store.get_traces(job_id)

    if not traces:
        # Check if job exists
        job = store.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
        return []

    return [
        TraceResponse(
            dimension=t.dimension,
            score=t.score,
            grade=t.grade,
            reasoning=t.reasoning,
            strengths=t.strengths or [],
            weaknesses=t.weaknesses or [],
            suggestions=t.suggestions or [],
            sequence=t.sequence,
            raw_metrics=t.raw_metrics,
            enhanced=t.enhanced,
        )
        for t in traces
    ]


@router.get(
    "/{job_id}/trace/{dimension}",
    response_model=TraceResponse,
    summary="Get single trace",
    description="Get trace for a specific dimension."
)
async def get_trace(job_id: str, dimension: str):
    """Get trace for a specific dimension."""
    store = get_store()
    trace = store.get_trace(job_id, dimension)

    if not trace:
        raise HTTPException(
            status_code=404,
            detail=f"Trace for {dimension} not found in job {job_id}"
        )

    return TraceResponse(
        dimension=trace.dimension,
        score=trace.score,
        grade=trace.grade,
        reasoning=trace.reasoning,
        strengths=trace.strengths or [],
        weaknesses=trace.weaknesses or [],
        suggestions=trace.suggestions or [],
        sequence=trace.sequence,
        raw_metrics=trace.raw_metrics,
        enhanced=trace.enhanced,
    )


@router.get(
    "/{job_id}/issues",
    response_model=List[IssueResponse],
    summary="Get issues",
    description="Get all issues for a job."
)
async def get_issues(
    job_id: str,
    severity: Optional[str] = Query(None, description="Filter by severity (error, warning, info)"),
):
    """Get issues for a job."""
    store = get_store()
    issues = store.get_issues(job_id=job_id, severity=severity)

    return [
        IssueResponse(
            dimension=i.dimension,
            severity=i.severity,
            message=i.message,
        )
        for i in issues
    ]
