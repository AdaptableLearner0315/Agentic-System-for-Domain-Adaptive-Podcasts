"""
Integration tests for the full pipeline flow.

Tests end-to-end job lifecycle from creation to completion.
"""

import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock

from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.models.enums import JobStatus, GenerationPhase


class TestFullPipelineFlow:
    """Test complete pipeline execution flow."""

    def test_normal_mode_job_lifecycle(self, client: TestClient):
        """Test complete Normal mode job lifecycle."""
        # 1. Create job
        create_response = client.post(
            "/api/pipelines/generate",
            json={
                "prompt": "The history of electronic music",
                "mode": "normal"
            }
        )
        assert create_response.status_code == 200
        job_data = create_response.json()
        job_id = job_data["id"]
        assert job_data["status"] == "pending"

        # 2. Check initial status
        status_response = client.get(f"/api/pipelines/{job_id}/status")
        assert status_response.status_code == 200
        status = status_response.json()
        assert status["job_id"] == job_id

        # 3. Get job details
        job_response = client.get(f"/api/pipelines/{job_id}")
        assert job_response.status_code == 200
        job = job_response.json()
        assert job["prompt"] == "The history of electronic music"
        assert job["mode"] == "normal"

    def test_pro_mode_job_lifecycle(self, client: TestClient):
        """Test complete Pro mode job lifecycle."""
        # 1. Create job with config
        create_response = client.post(
            "/api/pipelines/generate",
            json={
                "prompt": "AI breakthroughs in 2025",
                "mode": "pro",
                "guidance": "For general audience",
                "config": {
                    "director_review": True,
                    "image_count": 8
                }
            }
        )
        assert create_response.status_code == 200
        job_data = create_response.json()
        job_id = job_data["id"]
        assert job_data["mode"] == "pro"

        # 2. Verify job details include config
        job_response = client.get(f"/api/pipelines/{job_id}")
        assert job_response.status_code == 200
        job = job_response.json()
        assert job["guidance"] == "For general audience"

    def test_file_upload_and_generation(self, client: TestClient, tmp_path):
        """Test file upload followed by generation."""
        # 1. Upload file
        test_file = tmp_path / "transcript.txt"
        test_file.write_text("This is a sample transcript about technology.")

        with open(test_file, "rb") as f:
            upload_response = client.post(
                "/api/files/upload",
                files={"file": ("transcript.txt", f, "text/plain")}
            )
        assert upload_response.status_code == 200
        file_id = upload_response.json()["id"]

        # 2. Create job with uploaded file
        create_response = client.post(
            "/api/pipelines/generate",
            json={
                "file_ids": [file_id],
                "mode": "normal"
            }
        )
        assert create_response.status_code == 200
        job = create_response.json()
        assert file_id in job["file_ids"]

        # 3. Cleanup - delete file
        delete_response = client.delete(f"/api/files/{file_id}")
        assert delete_response.status_code == 200

    def test_hybrid_mode_generation(self, client: TestClient, tmp_path):
        """Test hybrid mode with prompt and files."""
        # 1. Upload reference file
        test_file = tmp_path / "reference.txt"
        test_file.write_text("Reference content about quantum computing.")

        with open(test_file, "rb") as f:
            upload_response = client.post(
                "/api/files/upload",
                files={"file": ("reference.txt", f, "text/plain")}
            )
        file_id = upload_response.json()["id"]

        # 2. Create hybrid job
        create_response = client.post(
            "/api/pipelines/generate",
            json={
                "prompt": "Key insights from this research",
                "file_ids": [file_id],
                "guidance": "For beginners",
                "mode": "pro"
            }
        )
        assert create_response.status_code == 200
        job = create_response.json()
        assert job["prompt"] == "Key insights from this research"
        assert job["file_ids"] == [file_id]

    def test_job_cancellation_flow(self, client: TestClient):
        """Test job cancellation during execution."""
        # 1. Create job
        create_response = client.post(
            "/api/pipelines/generate",
            json={
                "prompt": "Long content generation",
                "mode": "pro"
            }
        )
        job_id = create_response.json()["id"]

        # 2. Cancel job
        cancel_response = client.post(f"/api/pipelines/{job_id}/cancel")
        assert cancel_response.status_code == 200
        cancelled_job = cancel_response.json()
        assert cancelled_job["status"] == "cancelled"

        # 3. Verify job status
        status_response = client.get(f"/api/pipelines/{job_id}")
        assert status_response.json()["status"] == "cancelled"

    def test_multiple_concurrent_jobs(self, client: TestClient):
        """Test handling multiple concurrent jobs."""
        job_ids = []

        # Create multiple jobs
        for i in range(3):
            response = client.post(
                "/api/pipelines/generate",
                json={
                    "prompt": f"Topic {i}",
                    "mode": "normal"
                }
            )
            assert response.status_code == 200
            job_ids.append(response.json()["id"])

        # Verify all jobs exist
        list_response = client.get("/api/pipelines/")
        jobs = list_response.json()["jobs"]
        listed_ids = [j["id"] for j in jobs]

        for job_id in job_ids:
            assert job_id in listed_ids


class TestErrorHandling:
    """Test error handling in pipeline flow."""

    def test_invalid_request_format(self, client: TestClient):
        """Test handling of invalid JSON."""
        response = client.post(
            "/api/pipelines/generate",
            content="not json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422

    def test_missing_required_input(self, client: TestClient):
        """Test error when neither prompt nor files provided."""
        response = client.post(
            "/api/pipelines/generate",
            json={"mode": "normal"}
        )
        assert response.status_code == 400

    def test_invalid_file_id(self, client: TestClient):
        """Test error when file ID doesn't exist."""
        response = client.post(
            "/api/pipelines/generate",
            json={
                "file_ids": ["nonexistent-file-id"],
                "mode": "normal"
            }
        )
        assert response.status_code == 400
        assert "not found" in response.json()["detail"].lower()

    def test_double_cancellation(self, client: TestClient):
        """Test cancelling an already cancelled job."""
        # Create and cancel job
        create_response = client.post(
            "/api/pipelines/generate",
            json={"prompt": "Test", "mode": "normal"}
        )
        job_id = create_response.json()["id"]

        # First cancellation
        client.post(f"/api/pipelines/{job_id}/cancel")

        # Second cancellation should fail
        response = client.post(f"/api/pipelines/{job_id}/cancel")
        assert response.status_code == 400


class TestConfigurationEndpoints:
    """Test configuration endpoint integration."""

    def test_mode_config_matches_generation(self, client: TestClient):
        """Test that mode config matches what's accepted in generation."""
        # Get modes
        config_response = client.get("/api/config/modes")
        modes = config_response.json()["modes"]

        # Verify both modes work in generation
        for mode in ["normal", "pro"]:
            assert mode in modes
            response = client.post(
                "/api/pipelines/generate",
                json={"prompt": "Test", "mode": mode}
            )
            assert response.status_code == 200

    def test_supported_formats_match_upload(self, client: TestClient, tmp_path):
        """Test that advertised formats work for upload."""
        config_response = client.get("/api/config/modes")
        formats = config_response.json()["supported_formats"]

        # Test text format (one of the supported ones)
        if ".txt" in formats:
            test_file = tmp_path / "test.txt"
            test_file.write_text("Content")
            with open(test_file, "rb") as f:
                response = client.post(
                    "/api/files/upload",
                    files={"file": ("test.txt", f, "text/plain")}
                )
            assert response.status_code == 200
