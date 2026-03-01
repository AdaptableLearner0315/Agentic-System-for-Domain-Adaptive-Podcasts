"""
Unit tests for service layer.

Tests JobManager, FileService, and PipelineService logic.
"""

import pytest
import asyncio
import subprocess
from pathlib import Path
from datetime import datetime
from io import BytesIO
from unittest.mock import MagicMock, AsyncMock, patch

from app.services.job_manager import JobManager
from app.services.file_service import FileService
from app.services.pipeline_service import PipelineService
from app.models.enums import JobStatus, PipelineMode, GenerationPhase


class TestJobManager:
    """Test JobManager service."""

    def test_create_job(self, job_manager: JobManager):
        """Test job creation."""
        job = job_manager.create_job(
            mode=PipelineMode.NORMAL,
            prompt="Test prompt"
        )
        assert job.id is not None
        assert job.status == JobStatus.PENDING
        assert job.mode == PipelineMode.NORMAL
        assert job.prompt == "Test prompt"

    def test_create_job_with_files(self, job_manager: JobManager):
        """Test job creation with file IDs."""
        job = job_manager.create_job(
            mode=PipelineMode.PRO,
            file_ids=["file1", "file2"],
            guidance="For experts"
        )
        assert job.file_ids == ["file1", "file2"]
        assert job.guidance == "For experts"

    def test_get_job(self, job_manager: JobManager):
        """Test getting a job by ID."""
        created = job_manager.create_job(
            mode=PipelineMode.NORMAL,
            prompt="Test"
        )
        retrieved = job_manager.get_job(created.id)
        assert retrieved is not None
        assert retrieved.id == created.id

    def test_get_nonexistent_job(self, job_manager: JobManager):
        """Test getting a nonexistent job returns None."""
        result = job_manager.get_job("nonexistent")
        assert result is None

    def test_start_job(self, job_manager: JobManager):
        """Test starting a job."""
        job = job_manager.create_job(mode=PipelineMode.NORMAL, prompt="Test")
        started = job_manager.start_job(job.id)
        assert started.status == JobStatus.RUNNING
        assert started.started_at is not None

    def test_complete_job(self, job_manager: JobManager):
        """Test completing a job with result."""
        job = job_manager.create_job(mode=PipelineMode.NORMAL, prompt="Test")
        job_manager.start_job(job.id)

        result = {
            "success": True,
            "output_path": "/output/video.mp4",
            "duration_seconds": 120.0,
        }
        completed = job_manager.complete_job(job.id, result)

        assert completed.status == JobStatus.COMPLETED
        assert completed.completed_at is not None

    def test_fail_job(self, job_manager: JobManager):
        """Test failing a job with error."""
        job = job_manager.create_job(mode=PipelineMode.NORMAL, prompt="Test")
        job_manager.start_job(job.id)

        failed = job_manager.fail_job(job.id, "Out of memory")

        assert failed.status == JobStatus.FAILED
        assert failed.error == "Out of memory"

    def test_cancel_job(self, job_manager: JobManager):
        """Test cancelling a job."""
        job = job_manager.create_job(mode=PipelineMode.NORMAL, prompt="Test")
        job_manager.start_job(job.id)

        cancelled = job_manager.cancel_job(job.id)

        assert cancelled.status == JobStatus.CANCELLED

    def test_request_cancellation(self, job_manager: JobManager):
        """Test requesting cancellation."""
        job = job_manager.create_job(mode=PipelineMode.NORMAL, prompt="Test")
        job_manager.start_job(job.id)

        assert not job_manager.is_cancellation_requested(job.id)

        result = job_manager.request_cancellation(job.id)

        assert result is True
        assert job_manager.is_cancellation_requested(job.id)

    def test_update_progress(self, job_manager: JobManager):
        """Test updating job progress."""
        job = job_manager.create_job(mode=PipelineMode.NORMAL, prompt="Test")
        job_manager.start_job(job.id)

        progress = job_manager.update_progress(
            job_id=job.id,
            phase=GenerationPhase.SCRIPTING,
            message="Enhancing script...",
            progress_percent=25.0,
            current_step=1,
            total_steps=4
        )

        assert progress.phase == GenerationPhase.SCRIPTING
        assert progress.progress_percent == 25.0

    def test_get_progress(self, job_manager: JobManager):
        """Test getting job progress."""
        job = job_manager.create_job(mode=PipelineMode.NORMAL, prompt="Test")
        job_manager.start_job(job.id)
        job_manager.update_progress(
            job_id=job.id,
            phase=GenerationPhase.GENERATING_TTS,
            message="Generating voice...",
            progress_percent=50.0,
        )

        progress = job_manager.get_progress(job.id)

        assert progress.phase == GenerationPhase.GENERATING_TTS
        assert progress.progress_percent == 50.0

    def test_get_result(self, job_manager: JobManager):
        """Test getting job result."""
        job = job_manager.create_job(mode=PipelineMode.NORMAL, prompt="Test")
        job_manager.start_job(job.id)
        job_manager.complete_job(job.id, {
            "success": True,
            "output_path": "/output/video.mp4",
            "duration_seconds": 120.0,
        })

        result = job_manager.get_result(job.id)

        assert result.success is True
        assert result.output_path == "/output/video.mp4"

    def test_get_running_jobs(self, job_manager: JobManager):
        """Test getting list of running jobs."""
        job1 = job_manager.create_job(mode=PipelineMode.NORMAL, prompt="Test 1")
        job2 = job_manager.create_job(mode=PipelineMode.NORMAL, prompt="Test 2")
        job3 = job_manager.create_job(mode=PipelineMode.NORMAL, prompt="Test 3")

        job_manager.start_job(job1.id)
        job_manager.start_job(job2.id)
        # job3 stays pending

        running = job_manager.get_running_jobs()

        assert len(running) == 2
        assert job1.id in running
        assert job2.id in running
        assert job3.id not in running

    def test_list_jobs_pagination(self, job_manager: JobManager):
        """Test listing jobs with pagination."""
        for i in range(5):
            job_manager.create_job(mode=PipelineMode.NORMAL, prompt=f"Test {i}")

        jobs, total = job_manager.list_jobs(page=1, page_size=2)

        assert total == 5
        assert len(jobs) == 2

        jobs2, _ = job_manager.list_jobs(page=2, page_size=2)
        assert len(jobs2) == 2

    def test_list_jobs_status_filter(self, job_manager: JobManager):
        """Test filtering jobs by status."""
        job1 = job_manager.create_job(mode=PipelineMode.NORMAL, prompt="Test 1")
        job2 = job_manager.create_job(mode=PipelineMode.NORMAL, prompt="Test 2")

        job_manager.start_job(job1.id)

        pending_jobs, _ = job_manager.list_jobs(status_filter=JobStatus.PENDING)
        running_jobs, _ = job_manager.list_jobs(status_filter=JobStatus.RUNNING)

        assert len(pending_jobs) == 1
        assert len(running_jobs) == 1


class TestFileService:
    """Test FileService."""

    def test_is_supported_format(self, file_service: FileService):
        """Test format support checking."""
        assert file_service.is_supported_format("test.txt")
        assert file_service.is_supported_format("test.pdf")
        assert file_service.is_supported_format("test.mp3")
        assert not file_service.is_supported_format("test.exe")
        assert not file_service.is_supported_format("test")

    def test_get_supported_formats(self, file_service: FileService):
        """Test getting list of supported formats."""
        formats = file_service.get_supported_formats()
        assert ".txt" in formats
        assert ".pdf" in formats
        assert ".mp4" in formats

    @pytest.mark.asyncio
    async def test_upload_file(self, file_service: FileService):
        """Test file upload."""
        # Create mock upload file
        content = b"Test content for upload"
        mock_file = MagicMock()
        mock_file.filename = "test.txt"
        mock_file.content_type = "text/plain"
        mock_file.read = AsyncMock(return_value=content)

        result = await file_service.upload_file(mock_file)

        assert result.id is not None
        assert result.filename == "test.txt"
        assert result.size_bytes == len(content)
        assert result.source_type == "text"

    @pytest.mark.asyncio
    async def test_upload_unsupported_format(self, file_service: FileService):
        """Test uploading unsupported format raises error."""
        mock_file = MagicMock()
        mock_file.filename = "test.exe"

        with pytest.raises(ValueError) as exc:
            await file_service.upload_file(mock_file)
        assert "Unsupported file type" in str(exc.value)

    @pytest.mark.asyncio
    async def test_upload_too_large(self, file_service: FileService):
        """Test uploading too large file raises error."""
        # Create file larger than max size
        content = b"x" * (file_service.max_size_bytes + 1)
        mock_file = MagicMock()
        mock_file.filename = "large.txt"
        mock_file.content_type = "text/plain"
        mock_file.read = AsyncMock(return_value=content)

        with pytest.raises(ValueError) as exc:
            await file_service.upload_file(mock_file)
        assert "too large" in str(exc.value)

    def test_get_file(self, file_service: FileService):
        """Test getting nonexistent file returns None."""
        result = file_service.get_file("nonexistent")
        assert result is None

    def test_file_exists(self, file_service: FileService):
        """Test checking file existence."""
        assert not file_service.file_exists("nonexistent")

    def test_list_files_empty(self, file_service: FileService):
        """Test listing files when empty."""
        files = file_service.list_files()
        assert files == []


class TestPipelineService:
    """Test PipelineService."""

    @pytest.mark.asyncio
    async def test_run_job_creates_result(
        self,
        pipeline_service: PipelineService,
        job_manager: JobManager,
        sample_generation_request
    ):
        """Test running a job creates a result."""
        from app.models.requests import GenerationRequest

        job = job_manager.create_job(
            mode=PipelineMode.NORMAL,
            prompt=sample_generation_request["prompt"]
        )
        request = GenerationRequest(**sample_generation_request)

        # Override pipeline service's job_manager
        pipeline_service.job_manager = job_manager

        await pipeline_service.run_job(job.id, request)

        # Check job was completed or failed (depending on mock)
        final_job = job_manager.get_job(job.id)
        assert final_job.status in (
            JobStatus.COMPLETED,
            JobStatus.FAILED,
            JobStatus.CANCELLED
        )

    @pytest.mark.asyncio
    async def test_cancel_job(
        self,
        pipeline_service: PipelineService,
        job_manager: JobManager
    ):
        """Test cancelling a job."""
        job = job_manager.create_job(
            mode=PipelineMode.NORMAL,
            prompt="Test"
        )
        job_manager.start_job(job.id)

        await pipeline_service.cancel_job(job.id)

        assert job_manager.is_cancellation_requested(job.id)


class TestPipelineServiceTimeout:
    """Test timeout enforcement in PipelineService."""

    @pytest.mark.asyncio
    async def test_normal_mode_timeout(
        self,
        pipeline_service: PipelineService,
        job_manager: JobManager,
    ):
        """Job marked FAILED with 'timed out' message when pipeline hangs past timeout."""
        from app.models.requests import GenerationRequest
        from app.config import Settings

        job = job_manager.create_job(mode=PipelineMode.NORMAL, prompt="Test timeout")
        request = GenerationRequest(prompt="Test timeout", mode="normal")
        pipeline_service.job_manager = job_manager

        async def hanging_pipeline(*args, **kwargs):
            await asyncio.sleep(9999)

        test_settings = Settings(
            normal_mode_timeout_seconds=1,
            pro_mode_timeout_seconds=2,
        )

        with patch.object(pipeline_service, '_execute_pipeline', new=AsyncMock(side_effect=hanging_pipeline)), \
             patch.object(pipeline_service, '_update_progress', new=AsyncMock()), \
             patch('app.services.pipeline_service.get_settings', return_value=test_settings):
            await pipeline_service.run_job(job.id, request)

        final_job = job_manager.get_job(job.id)
        assert final_job.status == JobStatus.FAILED
        assert "timed out" in final_job.error.lower()

    @pytest.mark.asyncio
    async def test_pro_mode_uses_pro_timeout(
        self,
        pipeline_service: PipelineService,
        job_manager: JobManager,
    ):
        """Pro mode uses pro_mode_timeout_seconds value."""
        from app.models.requests import GenerationRequest
        from app.config import Settings

        job = job_manager.create_job(mode=PipelineMode.PRO, prompt="Test pro timeout")
        request = GenerationRequest(prompt="Test pro timeout", mode="pro")
        pipeline_service.job_manager = job_manager

        async def hanging_pipeline(*args, **kwargs):
            await asyncio.sleep(9999)

        test_settings = Settings(
            normal_mode_timeout_seconds=10,
            pro_mode_timeout_seconds=1,
        )

        with patch.object(pipeline_service, '_execute_pipeline', new=AsyncMock(side_effect=hanging_pipeline)), \
             patch.object(pipeline_service, '_update_progress', new=AsyncMock()), \
             patch('app.services.pipeline_service.get_settings', return_value=test_settings):
            await pipeline_service.run_job(job.id, request)

        final_job = job_manager.get_job(job.id)
        assert final_job.status == JobStatus.FAILED
        assert "timed out" in final_job.error.lower()
        assert "pro" in final_job.error.lower()

    @pytest.mark.asyncio
    async def test_fast_job_completes_normally(
        self,
        pipeline_service: PipelineService,
        job_manager: JobManager,
    ):
        """Job that finishes quickly is not killed by timeout."""
        from app.models.requests import GenerationRequest
        from app.config import Settings

        job = job_manager.create_job(mode=PipelineMode.NORMAL, prompt="Fast job")
        request = GenerationRequest(prompt="Fast job", mode="normal")
        pipeline_service.job_manager = job_manager

        async def fast_pipeline(*args, **kwargs):
            job_manager.complete_job(job.id, {"success": True, "output_path": "/out.mp4"})

        test_settings = Settings(
            normal_mode_timeout_seconds=10,
            pro_mode_timeout_seconds=10,
        )

        with patch.object(pipeline_service, '_execute_pipeline', new=AsyncMock(side_effect=fast_pipeline)), \
             patch.object(pipeline_service, '_update_progress', new=AsyncMock()), \
             patch('app.services.pipeline_service.get_settings', return_value=test_settings):
            await pipeline_service.run_job(job.id, request)

        final_job = job_manager.get_job(job.id)
        assert final_job.status == JobStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_timeout_error_message_includes_mode(
        self,
        pipeline_service: PipelineService,
        job_manager: JobManager,
    ):
        """Error message mentions the pipeline mode."""
        from app.models.requests import GenerationRequest
        from app.config import Settings

        job = job_manager.create_job(mode=PipelineMode.NORMAL, prompt="Test msg")
        request = GenerationRequest(prompt="Test msg", mode="normal")
        pipeline_service.job_manager = job_manager

        async def hanging_pipeline(*args, **kwargs):
            await asyncio.sleep(9999)

        test_settings = Settings(
            normal_mode_timeout_seconds=1,
            pro_mode_timeout_seconds=2,
        )

        with patch.object(pipeline_service, '_execute_pipeline', new=AsyncMock(side_effect=hanging_pipeline)), \
             patch.object(pipeline_service, '_update_progress', new=AsyncMock()), \
             patch('app.services.pipeline_service.get_settings', return_value=test_settings):
            await pipeline_service.run_job(job.id, request)

        final_job = job_manager.get_job(job.id)
        assert "normal" in final_job.error.lower()

    @pytest.mark.asyncio
    async def test_cancellation_still_works(
        self,
        pipeline_service: PipelineService,
        job_manager: JobManager,
    ):
        """Manual cancellation still works independently of timeout."""
        from app.models.requests import GenerationRequest
        from app.config import Settings

        job = job_manager.create_job(mode=PipelineMode.NORMAL, prompt="Test cancel")
        request = GenerationRequest(prompt="Test cancel", mode="normal")
        pipeline_service.job_manager = job_manager

        async def cancelling_pipeline(*args, **kwargs):
            raise asyncio.CancelledError()

        test_settings = Settings(
            normal_mode_timeout_seconds=10,
            pro_mode_timeout_seconds=10,
        )

        with patch.object(pipeline_service, '_execute_pipeline', new=AsyncMock(side_effect=cancelling_pipeline)), \
             patch.object(pipeline_service, '_update_progress', new=AsyncMock()), \
             patch('app.services.pipeline_service.get_settings', return_value=test_settings):
            await pipeline_service.run_job(job.id, request)

        final_job = job_manager.get_job(job.id)
        assert final_job.status == JobStatus.CANCELLED


class TestSubprocessTimeout:
    """Test subprocess timeout in video_assembler."""

    def test_subprocess_timeout_raises_runtime_error(self):
        """_run_subprocess raises RuntimeError when TimeoutExpired fires."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
        from utils.video_assembler import _run_subprocess

        with patch('utils.video_assembler.subprocess.run', side_effect=subprocess.TimeoutExpired(cmd=["ffmpeg"], timeout=120)):
            with pytest.raises(RuntimeError, match="timed out"):
                _run_subprocess(["ffmpeg", "-y", "-i", "input.mp4"])

    def test_subprocess_timeout_message(self):
        """Error message includes 'timed out' and partial command."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
        from utils.video_assembler import _run_subprocess

        with patch('utils.video_assembler.subprocess.run', side_effect=subprocess.TimeoutExpired(cmd=["ffmpeg"], timeout=120)):
            with pytest.raises(RuntimeError) as exc_info:
                _run_subprocess(["ffmpeg", "-y", "-i", "input.mp4", "-o", "output.mp4"])

            error_msg = str(exc_info.value)
            assert "timed out" in error_msg
            assert "ffmpeg" in error_msg
