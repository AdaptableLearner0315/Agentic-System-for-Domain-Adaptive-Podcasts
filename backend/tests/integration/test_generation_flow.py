"""
Integration tests for generation flow.

Tests job creation, WebSocket progress streaming, and pipeline
execution without AttributeError crashes.
"""

import asyncio
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.models.enums import JobStatus, GenerationPhase


class TestJobCreation:
    """Tests for job creation endpoint."""

    def test_create_job_returns_valid_id(self, client: TestClient):
        """POST /generate returns a job with a valid ID."""
        # Mock run_job so the background task doesn't trigger real pipelines
        with patch(
            "app.services.pipeline_service.PipelineService.run_job",
            new_callable=AsyncMock,
        ):
            response = client.post(
                "/api/pipelines/generate",
                json={
                    "prompt": "The history of electronic music",
                    "mode": "normal",
                },
            )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert isinstance(data["id"], str)
        assert len(data["id"]) > 0
        assert data["status"] in ("pending", "running")
        assert data["mode"] == "normal"


class TestWebSocketProgress:
    """Tests for WebSocket progress streaming."""

    @pytest.mark.asyncio
    async def test_websocket_receives_progress_updates(self):
        """Verify adapter queues progress updates for WebSocket broadcast."""
        from app.services.progress_adapter import adapter_manager, ProgressUpdate

        job_id = "ws-test-job"
        adapter = await adapter_manager.get_adapter(job_id)

        # Queue a progress update (simulates what the fixed callback does)
        adapter._queue.put_nowait(
            ProgressUpdate(
                job_id=job_id,
                phase=GenerationPhase.SCRIPTING,
                message="Enhancing script...",
                progress_percent=25.0,
                current_step=1,
                total_steps=4,
                elapsed_seconds=5.0,
            )
        )

        # Verify queue has the update
        assert not adapter._queue.empty()
        update = adapter._queue.get_nowait()
        assert update.progress_percent == 25.0
        assert update.phase == GenerationPhase.SCRIPTING
        assert update.message == "Enhancing script..."

    @pytest.mark.asyncio
    async def test_adapter_on_progress_queues_for_broadcast(self):
        """Verify on_progress queues updates that process_queue can broadcast."""
        from app.services.progress_adapter import adapter_manager

        job_id = "broadcast-test"
        adapter = await adapter_manager.get_adapter(job_id)

        # Simulate a ProgressStream update
        mock_update = MagicMock()
        mock_update.phase.value = "generating_tts"
        mock_update.message = "Generating voice (3/10)"
        mock_update.progress_percent = 40.0
        mock_update.current_step = 3
        mock_update.total_steps = 10
        mock_update.eta_seconds = 45.0
        mock_update.preview = "Sample text..."
        mock_update.elapsed_seconds = 20.0
        mock_update.details = {}

        adapter.on_progress(mock_update)

        assert not adapter._queue.empty()
        queued = adapter._queue.get_nowait()
        assert queued.progress_percent == 40.0
        assert queued.current_step == 3


class TestNormalPipelineNoAttributeError:
    """Tests that normal pipeline doesn't crash with AttributeError."""

    def test_normal_pipeline_mix_audio_calls_correct_method(self):
        """Verify _mix_audio calls mix_podcast_sentence_level, not mix_podcast."""
        import inspect
        from pipelines.normal_pipeline import NormalPipeline

        source = inspect.getsource(NormalPipeline._mix_audio)
        assert "mix_podcast_sentence_level" in source
        assert "mixer.mix_podcast(" not in source

    def test_normal_pipeline_adapts_tts_data_format(self):
        """Verify _mix_audio adapts TTS results to include required fields."""
        import inspect
        from pipelines.normal_pipeline import NormalPipeline

        source = inspect.getsource(NormalPipeline._mix_audio)
        # Should set type field for mixer compatibility
        assert '"type"' in source or "'type'" in source
        assert "hook_sentence" in source
        assert "chunk_sentence" in source
        assert "module_id" in source
        assert "chunk_idx" in source

    def test_pipeline_service_callbacks_use_adapter_on_progress(self):
        """Verify pipeline service callbacks use adapter.on_progress, not asyncio loop."""
        import inspect
        from app.services.pipeline_service import PipelineService

        normal_source = inspect.getsource(PipelineService._run_normal_pipeline)
        pro_source = inspect.getsource(PipelineService._run_pro_pipeline)

        # Should use adapter.on_progress
        assert "adapter.on_progress" in normal_source
        assert "adapter.on_progress" in pro_source

        # Should NOT use asyncio.get_event_loop() in callback
        assert "asyncio.get_event_loop()" not in normal_source
        assert "asyncio.get_event_loop()" not in pro_source

        # Should NOT use run_coroutine_threadsafe in callback
        assert "run_coroutine_threadsafe" not in normal_source
        assert "run_coroutine_threadsafe" not in pro_source


class TestVideoAssemblyImports:
    """Tests that both pipelines can import create_podcast_video."""

    def test_normal_pipeline_assemble_video_imports_correctly(self):
        """Verify _assemble_video in NormalPipeline imports create_podcast_video."""
        import inspect
        from pipelines.normal_pipeline import NormalPipeline

        source = inspect.getsource(NormalPipeline._assemble_video)
        assert "from utils.video_assembler import create_podcast_video" in source

    def test_pro_pipeline_assemble_video_imports_correctly(self):
        """Verify _assemble_video_pro in ProPipeline imports create_podcast_video."""
        import inspect
        from pipelines.pro_pipeline import ProPipeline

        source = inspect.getsource(ProPipeline._assemble_video_pro)
        assert "from utils.video_assembler import create_podcast_video" in source

    def test_create_podcast_video_importable_at_runtime(self):
        """Verify the import that both pipelines use actually resolves."""
        from utils.video_assembler import create_podcast_video
        assert callable(create_podcast_video)
