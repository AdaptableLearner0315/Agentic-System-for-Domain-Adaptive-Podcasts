"""
Pytest configuration and shared fixtures.

This module provides fixtures used across all test modules,
including mock services, test clients, and sample data.
"""

import os
import sys
import tempfile
from pathlib import Path
from typing import Generator, AsyncGenerator
from datetime import datetime
import pytest
from unittest.mock import MagicMock, AsyncMock

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.config import Settings, get_settings
from app.dependencies import (
    get_job_manager,
    get_file_service,
    get_pipeline_service,
    reset_services,
)
from app.services.job_manager import JobManager
from app.services.file_service import FileService
from app.services.pipeline_service import PipelineService
from app.models.enums import JobStatus, PipelineMode, GenerationPhase


# =============================================================================
# Configuration Fixtures
# =============================================================================

@pytest.fixture
def test_settings() -> Settings:
    """
    Create test settings with temporary directories.

    Returns:
        Settings instance configured for testing.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        settings = Settings(
            app_name="Nell Test API",
            debug=True,
            upload_dir=os.path.join(tmpdir, "uploads"),
            output_dir=os.path.join(tmpdir, "output"),
            max_upload_size_mb=10,
        )
        yield settings


@pytest.fixture(autouse=True)
def reset_services_fixture():
    """Reset all services between tests."""
    reset_services()
    yield
    reset_services()


# =============================================================================
# Service Fixtures
# =============================================================================

@pytest.fixture
def job_manager() -> JobManager:
    """
    Create a fresh JobManager instance.

    Returns:
        JobManager for testing.
    """
    return JobManager()


@pytest.fixture
def file_service(tmp_path: Path) -> FileService:
    """
    Create a FileService with temporary upload directory.

    Args:
        tmp_path: Pytest temporary path fixture.

    Returns:
        FileService for testing.
    """
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()
    return FileService(upload_dir=upload_dir, max_size_bytes=10 * 1024 * 1024)


@pytest.fixture
def pipeline_service(tmp_path: Path, job_manager: JobManager) -> PipelineService:
    """
    Create a PipelineService with mock dependencies.

    Args:
        tmp_path: Pytest temporary path fixture.
        job_manager: JobManager fixture.

    Returns:
        PipelineService for testing.
    """
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return PipelineService(output_dir=output_dir, job_manager=job_manager)


# =============================================================================
# Client Fixtures
# =============================================================================

@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """
    Create a synchronous test client.

    Yields:
        TestClient for making requests.
    """
    with TestClient(app) as client:
        yield client


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """
    Create an asynchronous test client.

    Yields:
        AsyncClient for making async requests.
    """
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        yield client


# =============================================================================
# Sample Data Fixtures
# =============================================================================

@pytest.fixture
def sample_generation_request() -> dict:
    """
    Sample generation request data.

    Returns:
        Dictionary with valid generation request.
    """
    return {
        "prompt": "The history of electronic music",
        "mode": "normal",
        "guidance": "Make it engaging for beginners",
    }


@pytest.fixture
def sample_pro_request() -> dict:
    """
    Sample Pro mode generation request.

    Returns:
        Dictionary with valid Pro mode request.
    """
    return {
        "prompt": "AI breakthroughs in 2025",
        "mode": "pro",
        "config": {
            "director_review": True,
            "image_count": 8,
        },
    }


@pytest.fixture
def sample_job_response() -> dict:
    """
    Sample job response data.

    Returns:
        Dictionary matching JobResponse schema.
    """
    return {
        "id": "test123",
        "status": JobStatus.PENDING.value,
        "mode": PipelineMode.NORMAL.value,
        "created_at": datetime.utcnow().isoformat(),
        "prompt": "Test prompt",
    }


@pytest.fixture
def sample_progress_response() -> dict:
    """
    Sample progress response data.

    Returns:
        Dictionary matching ProgressResponse schema.
    """
    return {
        "job_id": "test123",
        "phase": GenerationPhase.SCRIPTING.value,
        "message": "Enhancing script...",
        "progress_percent": 25.0,
        "current_step": 1,
        "total_steps": 4,
        "elapsed_seconds": 10.5,
    }


@pytest.fixture
def sample_text_content() -> str:
    """
    Sample text content for file upload.

    Returns:
        Sample transcript text.
    """
    return """
    The history of electronic music is a fascinating journey through
    innovation, creativity, and technological advancement. From the
    early experiments with electronic instruments in the early 20th
    century to the global phenomenon it has become today.
    """


@pytest.fixture
def sample_file(tmp_path: Path, sample_text_content: str) -> Path:
    """
    Create a sample text file for testing.

    Args:
        tmp_path: Pytest temporary path fixture.
        sample_text_content: Sample content fixture.

    Returns:
        Path to created test file.
    """
    file_path = tmp_path / "sample.txt"
    file_path.write_text(sample_text_content)
    return file_path


# =============================================================================
# Mock Fixtures
# =============================================================================

@pytest.fixture
def mock_pipeline():
    """
    Create a mock pipeline for testing.

    Returns:
        MagicMock configured as a pipeline.
    """
    mock = MagicMock()
    mock.run_with_content = AsyncMock(return_value=MagicMock(
        success=True,
        output_path="/output/test.mp4",
        script={"title": "Test", "modules": []},
        tts_files=[],
        bgm_files=[],
        image_files=[],
        duration_seconds=120.0,
        error=None,
    ))
    return mock


@pytest.fixture
def mock_progress_stream():
    """
    Create a mock ProgressStream for testing.

    Returns:
        MagicMock configured as a ProgressStream.
    """
    mock = MagicMock()
    mock.update = MagicMock()
    mock.start = MagicMock()
    mock.complete = MagicMock()
    mock.error = MagicMock()
    return mock


# =============================================================================
# Utility Functions
# =============================================================================

def create_test_job(
    job_manager: JobManager,
    prompt: str = "Test",
    mode: PipelineMode = PipelineMode.NORMAL,
) -> str:
    """
    Create a test job in the job manager.

    Args:
        job_manager: JobManager instance.
        prompt: Job prompt.
        mode: Pipeline mode.

    Returns:
        Created job ID.
    """
    job = job_manager.create_job(
        mode=mode,
        prompt=prompt,
    )
    return job.id


def advance_job_to_running(job_manager: JobManager, job_id: str) -> None:
    """
    Advance a job to running state.

    Args:
        job_manager: JobManager instance.
        job_id: Job to advance.
    """
    job_manager.start_job(job_id)
    job_manager.update_progress(
        job_id=job_id,
        phase=GenerationPhase.SCRIPTING,
        message="Test progress",
        progress_percent=50.0,
    )
