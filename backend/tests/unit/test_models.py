"""
Unit tests for Pydantic models.

Tests model validation, serialization, and edge cases.
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from app.models.enums import JobStatus, PipelineMode, GenerationPhase
from app.models.requests import (
    GenerationRequest,
    ProConfigRequest,
    URLExtractionRequest,
    FileUploadMetadata,
)
from app.models.responses import (
    JobResponse,
    ProgressResponse,
    ResultResponse,
    FileResponse,
    HealthResponse,
    ErrorResponse,
)


class TestEnums:
    """Test enum definitions and values."""

    def test_job_status_values(self):
        """Test JobStatus enum has all expected values."""
        assert JobStatus.PENDING.value == "pending"
        assert JobStatus.RUNNING.value == "running"
        assert JobStatus.COMPLETED.value == "completed"
        assert JobStatus.FAILED.value == "failed"
        assert JobStatus.CANCELLED.value == "cancelled"

    def test_pipeline_mode_values(self):
        """Test PipelineMode enum has expected values."""
        assert PipelineMode.NORMAL.value == "normal"
        assert PipelineMode.PRO.value == "pro"

    def test_generation_phase_values(self):
        """Test GenerationPhase enum has all phases."""
        phases = [
            "initializing", "analyzing", "scripting",
            "generating_tts", "generating_bgm", "generating_images",
            "mixing_audio", "assembling_video", "complete", "error"
        ]
        for phase in phases:
            assert GenerationPhase(phase).value == phase


class TestGenerationRequest:
    """Test GenerationRequest model validation."""

    def test_valid_prompt_only(self):
        """Test valid request with only prompt."""
        request = GenerationRequest(
            prompt="History of AI",
            mode="normal"
        )
        assert request.prompt == "History of AI"
        assert request.mode == "normal"
        assert request.file_ids is None

    def test_valid_files_only(self):
        """Test valid request with only file_ids."""
        request = GenerationRequest(
            file_ids=["abc123"],
            mode="pro"
        )
        assert request.file_ids == ["abc123"]
        assert request.prompt is None

    def test_valid_hybrid(self):
        """Test valid hybrid request."""
        request = GenerationRequest(
            prompt="Key insights",
            file_ids=["abc123"],
            guidance="For beginners",
            mode="pro"
        )
        assert request.prompt == "Key insights"
        assert request.file_ids == ["abc123"]
        assert request.guidance == "For beginners"

    def test_mode_normalization(self):
        """Test mode is normalized to lowercase."""
        request = GenerationRequest(prompt="Test", mode="NORMAL")
        assert request.mode == "normal"

        request = GenerationRequest(prompt="Test", mode="Pro")
        assert request.mode == "pro"

    def test_invalid_mode_rejected(self):
        """Test invalid mode raises validation error."""
        with pytest.raises(ValidationError) as exc:
            GenerationRequest(prompt="Test", mode="invalid")
        assert "mode must be 'normal' or 'pro'" in str(exc.value)

    def test_config_optional(self):
        """Test config is optional and accepts dict."""
        request = GenerationRequest(
            prompt="Test",
            mode="pro",
            config={"director_review": True}
        )
        assert request.config == {"director_review": True}


class TestProConfigRequest:
    """Test ProConfigRequest model validation."""

    def test_all_optional(self):
        """Test all fields are optional."""
        config = ProConfigRequest()
        assert config.director_review is None
        assert config.max_review_rounds is None

    def test_valid_values(self):
        """Test valid configuration values."""
        config = ProConfigRequest(
            director_review=True,
            max_review_rounds=3,
            approval_threshold=7,
            image_count=16
        )
        assert config.director_review is True
        assert config.max_review_rounds == 3

    def test_max_review_rounds_range(self):
        """Test max_review_rounds validation."""
        with pytest.raises(ValidationError):
            ProConfigRequest(max_review_rounds=0)

        with pytest.raises(ValidationError):
            ProConfigRequest(max_review_rounds=10)

    def test_image_count_range(self):
        """Test image_count validation."""
        with pytest.raises(ValidationError):
            ProConfigRequest(image_count=0)

        with pytest.raises(ValidationError):
            ProConfigRequest(image_count=50)


class TestURLExtractionRequest:
    """Test URLExtractionRequest model validation."""

    def test_valid_url(self):
        """Test valid URL accepted."""
        request = URLExtractionRequest(url="https://example.com/article")
        assert request.url == "https://example.com/article"

    def test_http_url_accepted(self):
        """Test HTTP URL accepted."""
        request = URLExtractionRequest(url="http://example.com")
        assert request.url == "http://example.com"

    def test_invalid_url_rejected(self):
        """Test invalid URL rejected."""
        with pytest.raises(ValidationError) as exc:
            URLExtractionRequest(url="not-a-url")
        assert "URL must start with" in str(exc.value)

    def test_description_optional(self):
        """Test description is optional."""
        request = URLExtractionRequest(url="https://example.com")
        assert request.description is None


class TestJobResponse:
    """Test JobResponse model."""

    def test_minimal_response(self):
        """Test minimal required fields."""
        response = JobResponse(
            id="test123",
            status=JobStatus.PENDING,
            mode=PipelineMode.NORMAL,
            created_at=datetime.utcnow()
        )
        assert response.id == "test123"
        assert response.status == JobStatus.PENDING
        assert response.progress is None
        assert response.result is None

    def test_full_response(self):
        """Test response with all fields."""
        now = datetime.utcnow()
        progress = ProgressResponse(
            job_id="test123",
            phase=GenerationPhase.SCRIPTING,
            message="Processing",
            progress_percent=50.0,
            current_step=2,
            total_steps=4,
            elapsed_seconds=30.0
        )
        response = JobResponse(
            id="test123",
            status=JobStatus.RUNNING,
            mode=PipelineMode.PRO,
            created_at=now,
            started_at=now,
            prompt="Test prompt",
            progress=progress
        )
        assert response.progress.progress_percent == 50.0


class TestProgressResponse:
    """Test ProgressResponse model."""

    def test_minimal_response(self):
        """Test minimal required fields."""
        response = ProgressResponse(
            job_id="test123",
            phase=GenerationPhase.INITIALIZING,
            message="Starting",
            elapsed_seconds=0.0
        )
        assert response.progress_percent == 0.0
        assert response.current_step == 0
        assert response.eta_seconds is None

    def test_progress_percent_range(self):
        """Test progress_percent validation."""
        with pytest.raises(ValidationError):
            ProgressResponse(
                job_id="test",
                phase=GenerationPhase.SCRIPTING,
                message="Test",
                progress_percent=-1,
                elapsed_seconds=0
            )

        with pytest.raises(ValidationError):
            ProgressResponse(
                job_id="test",
                phase=GenerationPhase.SCRIPTING,
                message="Test",
                progress_percent=101,
                elapsed_seconds=0
            )


class TestResultResponse:
    """Test ResultResponse model."""

    def test_success_response(self):
        """Test successful result response."""
        response = ResultResponse(
            job_id="test123",
            success=True,
            output_path="/output/video.mp4",
            duration_seconds=120.5
        )
        assert response.success is True
        assert response.error is None

    def test_failure_response(self):
        """Test failure result response."""
        response = ResultResponse(
            job_id="test123",
            success=False,
            error="Pipeline failed: out of memory"
        )
        assert response.success is False
        assert response.output_path is None


class TestHealthResponse:
    """Test HealthResponse model."""

    def test_default_values(self):
        """Test default values are set."""
        response = HealthResponse(version="1.0.0")
        assert response.status == "healthy"
        assert response.timestamp is not None


class TestErrorResponse:
    """Test ErrorResponse model."""

    def test_basic_error(self):
        """Test basic error response."""
        response = ErrorResponse(
            error="not_found",
            message="Job not found"
        )
        assert response.error == "not_found"
        assert response.details is None

    def test_error_with_details(self):
        """Test error with details."""
        response = ErrorResponse(
            error="validation_error",
            message="Invalid request",
            details={"field": "mode", "reason": "invalid value"}
        )
        assert response.details["field"] == "mode"
