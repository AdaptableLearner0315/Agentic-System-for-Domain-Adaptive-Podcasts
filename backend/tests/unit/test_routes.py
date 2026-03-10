"""
Unit tests for API routes.

Tests route handlers, validation, and error responses.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.main import app
from app.models.enums import JobStatus, PipelineMode


class TestHealthEndpoint:
    """Test health check endpoint."""

    def test_health_check(self, client: TestClient):
        """Test health endpoint returns healthy status."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "timestamp" in data


class TestPipelineRoutes:
    """Test pipeline generation routes."""

    def test_generate_with_prompt(self, client: TestClient):
        """Test generation with prompt only."""
        response = client.post(
            "/api/pipelines/generate",
            json={
                "prompt": "History of AI",
                "mode": "normal"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["status"] == "pending"
        assert data["mode"] == "normal"

    def test_generate_with_invalid_mode(self, client: TestClient):
        """Test generation with invalid mode returns 422."""
        response = client.post(
            "/api/pipelines/generate",
            json={
                "prompt": "Test",
                "mode": "invalid"
            }
        )
        assert response.status_code == 422

    def test_generate_without_input(self, client: TestClient):
        """Test generation without prompt or files returns 400."""
        response = client.post(
            "/api/pipelines/generate",
            json={"mode": "normal"}
        )
        assert response.status_code == 400
        assert "must be provided" in response.json()["detail"]

    def test_generate_with_nonexistent_file(self, client: TestClient):
        """Test generation with nonexistent file returns 400."""
        response = client.post(
            "/api/pipelines/generate",
            json={
                "file_ids": ["nonexistent"],
                "mode": "normal"
            }
        )
        assert response.status_code == 400
        assert "not found" in response.json()["detail"]

    def test_list_jobs(self, client: TestClient):
        """Test listing jobs."""
        # Create a job first
        client.post(
            "/api/pipelines/generate",
            json={"prompt": "Test", "mode": "normal"}
        )

        response = client.get("/api/pipelines/")
        assert response.status_code == 200
        data = response.json()
        assert "jobs" in data
        assert "total" in data
        assert len(data["jobs"]) >= 1

    def test_list_jobs_pagination(self, client: TestClient):
        """Test job list pagination."""
        # Create multiple jobs
        for i in range(3):
            client.post(
                "/api/pipelines/generate",
                json={"prompt": f"Test {i}", "mode": "normal"}
            )

        response = client.get("/api/pipelines/?page=1&page_size=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["jobs"]) <= 2

    def test_get_job_status(self, client: TestClient):
        """Test getting job status."""
        # Create a job
        create_response = client.post(
            "/api/pipelines/generate",
            json={"prompt": "Test", "mode": "normal"}
        )
        job_id = create_response.json()["id"]

        response = client.get(f"/api/pipelines/{job_id}/status")
        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == job_id
        assert "phase" in data

    def test_get_nonexistent_job_status(self, client: TestClient):
        """Test getting status of nonexistent job returns 404."""
        response = client.get("/api/pipelines/nonexistent/status")
        assert response.status_code == 404

    def test_get_job_result_not_completed(self, client: TestClient):
        """Test getting result of non-completed job returns 400."""
        create_response = client.post(
            "/api/pipelines/generate",
            json={"prompt": "Test", "mode": "normal"}
        )
        job_id = create_response.json()["id"]

        response = client.get(f"/api/pipelines/{job_id}/result")
        assert response.status_code == 400
        assert "not completed" in response.json()["detail"]

    def test_cancel_job(self, client: TestClient):
        """Test cancelling a job."""
        create_response = client.post(
            "/api/pipelines/generate",
            json={"prompt": "Test", "mode": "normal"}
        )
        job_id = create_response.json()["id"]

        response = client.post(f"/api/pipelines/{job_id}/cancel")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "cancelled"


class TestConfigRoutes:
    """Test configuration routes."""

    def test_get_modes(self, client: TestClient):
        """Test getting available modes."""
        response = client.get("/api/config/modes")
        assert response.status_code == 200
        data = response.json()
        assert "modes" in data
        assert "normal" in data["modes"]
        assert "pro" in data["modes"]
        assert "supported_formats" in data

    def test_get_voices(self, client: TestClient):
        """Test getting available voices."""
        response = client.get("/api/config/voices")
        assert response.status_code == 200
        data = response.json()
        assert "voices" in data
        assert "default" in data

    def test_get_emotions(self, client: TestClient):
        """Test getting supported emotions."""
        response = client.get("/api/config/emotions")
        assert response.status_code == 200
        data = response.json()
        assert "emotions" in data
        assert "wonder" in data["emotions"]

    def test_get_speaker_formats(self, client: TestClient):
        """Test getting speaker formats."""
        response = client.get("/api/config/speaker-formats")
        assert response.status_code == 200
        data = response.json()
        assert "formats" in data
        assert "single" in data["formats"]
        assert "interview" in data["formats"]


class TestFileRoutes:
    """Test file upload routes."""

    def test_upload_text_file(self, client: TestClient, tmp_path):
        """Test uploading a text file."""
        # Create test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("Sample content")

        with open(test_file, "rb") as f:
            response = client.post(
                "/api/files/upload",
                files={"file": ("test.txt", f, "text/plain")}
            )

        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["filename"] == "test.txt"
        assert data["source_type"] == "text"

    def test_upload_unsupported_format(self, client: TestClient):
        """Test uploading unsupported format returns 400."""
        response = client.post(
            "/api/files/upload",
            files={"file": ("test.exe", b"binary", "application/octet-stream")}
        )
        assert response.status_code == 400
        assert "Unsupported" in response.json()["detail"]

    def test_list_files(self, client: TestClient):
        """Test listing uploaded files."""
        response = client.get("/api/files/")
        assert response.status_code == 200
        data = response.json()
        assert "files" in data
        assert "total" in data

    def test_get_nonexistent_file(self, client: TestClient):
        """Test getting nonexistent file returns 404."""
        response = client.get("/api/files/nonexistent")
        assert response.status_code == 404

    def test_delete_nonexistent_file(self, client: TestClient):
        """Test deleting nonexistent file returns 404."""
        response = client.delete("/api/files/nonexistent")
        assert response.status_code == 404

    def test_extract_from_url(self, client: TestClient):
        """Test URL extraction endpoint validation."""
        response = client.post(
            "/api/files/upload-url",
            json={"url": "invalid-url"}
        )
        assert response.status_code == 422


class TestOutputRoutes:
    """Test output download routes."""

    def test_download_nonexistent_job(self, client: TestClient):
        """Test downloading from nonexistent job returns 404."""
        response = client.get("/api/outputs/download/nonexistent")
        assert response.status_code == 404

    def test_stream_nonexistent_job(self, client: TestClient):
        """Test streaming nonexistent job returns 404."""
        response = client.get("/api/outputs/stream/nonexistent")
        assert response.status_code == 404
