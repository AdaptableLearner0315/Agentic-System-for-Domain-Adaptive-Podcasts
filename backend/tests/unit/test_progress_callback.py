"""
Unit tests for progress callback thread-safety and AudioMixer method.

Verifies:
- ProgressAdapter.on_progress() is sync-safe and queues updates
- The fixed callback pattern works from a thread context
- AudioMixer has mix_podcast_sentence_level but not mix_podcast
"""

import asyncio
import threading
from unittest.mock import MagicMock

import pytest

from app.services.progress_adapter import ProgressAdapter, ProgressUpdate
from app.models.enums import GenerationPhase


class TestProgressAdapterOnProgress:
    """Tests for ProgressAdapter.on_progress sync safety."""

    def test_adapter_on_progress_queues_update(self):
        """Verify on_progress() is sync and puts to queue."""
        adapter = ProgressAdapter(job_id="test-job")

        # Create a mock ProgressStream update (mimics utils.progress_stream.ProgressUpdate)
        mock_update = MagicMock()
        mock_update.phase.value = "scripting"
        mock_update.message = "Enhancing script..."
        mock_update.progress_percent = 25.0
        mock_update.current_step = 1
        mock_update.total_steps = 4
        mock_update.eta_seconds = 30.0
        mock_update.preview = "Hook text preview"
        mock_update.elapsed_seconds = 10.0
        mock_update.details = {"key": "value"}

        # Call on_progress synchronously
        adapter.on_progress(mock_update)

        # Verify item was queued
        assert not adapter._queue.empty()

        # Pull item and verify fields
        queued: ProgressUpdate = adapter._queue.get_nowait()
        assert queued.job_id == "test-job"
        assert queued.phase == GenerationPhase.SCRIPTING
        assert queued.message == "Enhancing script..."
        assert queued.progress_percent == 25.0
        assert queued.current_step == 1
        assert queued.total_steps == 4
        assert queued.eta_seconds == 30.0
        assert queued.preview == "Hook text preview"
        assert queued.elapsed_seconds == 10.0
        assert queued.details == {"key": "value"}

    def test_progress_callback_captures_adapter_in_closure(self):
        """Simulate the fixed callback pattern from a thread."""
        adapter = ProgressAdapter(job_id="thread-test")
        results = []

        # This mimics the fixed pattern: adapter captured in closure before thread starts
        def progress_callback(update):
            try:
                adapter.on_progress(update)
                results.append("success")
            except Exception as e:
                results.append(f"error: {e}")

        # Create mock update
        mock_update = MagicMock()
        mock_update.phase.value = "generating_tts"
        mock_update.message = "Generating voice (1/10)"
        mock_update.progress_percent = 30.0
        mock_update.current_step = 1
        mock_update.total_steps = 10
        mock_update.eta_seconds = 60.0
        mock_update.preview = None
        mock_update.elapsed_seconds = 15.0
        mock_update.details = {}

        # Call from a thread (simulates ProgressStream callback context)
        thread = threading.Thread(target=progress_callback, args=(mock_update,))
        thread.start()
        thread.join(timeout=5)

        assert results == ["success"]
        assert not adapter._queue.empty()

    def test_on_progress_handles_missing_details_attr(self):
        """Verify on_progress handles update without details attribute."""
        adapter = ProgressAdapter(job_id="no-details")

        mock_update = MagicMock(spec=[
            "phase", "message", "progress_percent",
            "current_step", "total_steps", "eta_seconds",
            "preview", "elapsed_seconds",
        ])
        mock_update.phase.value = "analyzing"
        mock_update.message = "Analyzing..."
        mock_update.progress_percent = 5.0
        mock_update.current_step = 0
        mock_update.total_steps = 0
        mock_update.eta_seconds = None
        mock_update.preview = None
        mock_update.elapsed_seconds = 2.0

        # Should not raise even though details is missing
        adapter.on_progress(mock_update)

        queued = adapter._queue.get_nowait()
        assert queued.details is None


class TestAudioMixerMethods:
    """Tests for AudioMixer method existence."""

    def test_audio_mixer_has_sentence_level_method(self):
        """Assert mix_podcast_sentence_level exists on AudioMixer."""
        from agents.audio_designer.audio_mixer import AudioMixer

        assert hasattr(AudioMixer, "mix_podcast_sentence_level")
        assert callable(getattr(AudioMixer, "mix_podcast_sentence_level"))

    def test_audio_mixer_has_no_mix_podcast_method(self):
        """Assert mix_podcast does NOT exist on AudioMixer."""
        from agents.audio_designer.audio_mixer import AudioMixer

        assert not hasattr(AudioMixer, "mix_podcast")
