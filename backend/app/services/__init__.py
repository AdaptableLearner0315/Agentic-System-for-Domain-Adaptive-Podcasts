"""
Service layer for the Nell Podcast API.

Services handle business logic and integrate with existing pipelines:
- JobManager: Tracks job state and lifecycle
- PipelineService: Orchestrates pipeline execution
- FileService: Handles file uploads and extraction
- ProgressAdapter: Bridges ProgressStream to WebSocket
"""

from .job_manager import JobManager
from .file_service import FileService
from .pipeline_service import PipelineService
from .progress_adapter import ProgressAdapter

__all__ = ["JobManager", "FileService", "PipelineService", "ProgressAdapter"]
