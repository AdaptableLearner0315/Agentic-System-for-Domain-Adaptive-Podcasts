"""
Pydantic models for the Nell API.

This module exports all request/response models and enums used across the API.
"""

from .enums import JobStatus, PipelineMode, GenerationPhase
from .requests import (
    GenerationRequest,
    FileUploadMetadata,
    URLExtractionRequest,
    ConfigUpdateRequest,
)
from .responses import (
    JobResponse,
    JobListResponse,
    ProgressResponse,
    ResultResponse,
    FileResponse,
    FileListResponse,
    ConfigResponse,
    HealthResponse,
    ErrorResponse,
)

__all__ = [
    # Enums
    "JobStatus",
    "PipelineMode",
    "GenerationPhase",
    # Requests
    "GenerationRequest",
    "FileUploadMetadata",
    "URLExtractionRequest",
    "ConfigUpdateRequest",
    # Responses
    "JobResponse",
    "JobListResponse",
    "ProgressResponse",
    "ResultResponse",
    "FileResponse",
    "FileListResponse",
    "ConfigResponse",
    "HealthResponse",
    "ErrorResponse",
]
