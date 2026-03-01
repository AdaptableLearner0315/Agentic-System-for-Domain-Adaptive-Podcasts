"""
Unit tests for utils.video_assembler.create_podcast_video.

Verifies the function is importable, accepts the correct signature,
handles edge cases, and uses a single-pass FFmpeg pipeline.
"""

import inspect
import platform
from unittest.mock import patch, MagicMock, call

import pytest


class TestCreatePodcastVideoImport:
    """Verify the function exists and is importable."""

    def test_create_podcast_video_is_importable(self):
        """create_podcast_video can be imported from utils.video_assembler."""
        from utils.video_assembler import create_podcast_video
        assert callable(create_podcast_video)

    def test_create_podcast_video_signature(self):
        """Function accepts original positional params plus new keyword-only params."""
        from utils.video_assembler import create_podcast_video

        sig = inspect.signature(create_podcast_video)
        params = list(sig.parameters.keys())

        # Original positional params
        assert "audio_path" in params
        assert "image_paths" in params
        assert "output_path" in params
        assert "crossfade_duration" in params

        # crossfade_duration should have a default of 1.0
        assert sig.parameters["crossfade_duration"].default == 1.0

        # New keyword-only params
        assert "use_ken_burns" in params
        assert "resolution" in params
        assert "fps" in params
        assert "quality" in params

        # New params should be keyword-only
        assert sig.parameters["use_ken_burns"].kind == inspect.Parameter.KEYWORD_ONLY
        assert sig.parameters["resolution"].kind == inspect.Parameter.KEYWORD_ONLY
        assert sig.parameters["fps"].kind == inspect.Parameter.KEYWORD_ONLY
        assert sig.parameters["quality"].kind == inspect.Parameter.KEYWORD_ONLY

        # Defaults
        assert sig.parameters["use_ken_burns"].default is False
        assert sig.parameters["fps"].default == 24
        assert sig.parameters["quality"].default == "fast"


class TestCreatePodcastVideoEdgeCases:
    """Edge case handling."""

    def test_no_images_returns_audio_path(self, tmp_path):
        """If image list is empty, returns audio_path unchanged."""
        from utils.video_assembler import create_podcast_video

        audio = str(tmp_path / "audio.mp3")
        output = str(tmp_path / "out.mp4")

        result = create_podcast_video(audio, [], output)
        assert result == audio


class TestSinglePassPipeline:
    """Verify create_podcast_video uses a single FFmpeg call."""

    @patch("utils.video_assembler._run_subprocess")
    @patch("utils.video_assembler.get_audio_duration", return_value=60.0)
    def test_single_subprocess_call(self, mock_duration, mock_run, tmp_path):
        """Only one _run_subprocess call for the entire video assembly."""
        from utils.video_assembler import create_podcast_video

        audio = str(tmp_path / "audio.mp3")
        images = [
            str(tmp_path / "img1.png"),
            str(tmp_path / "img2.png"),
            str(tmp_path / "img3.png"),
        ]
        output = str(tmp_path / "output" / "final.mp4")

        create_podcast_video(audio, images, output, crossfade_duration=0.5)

        # Exactly one FFmpeg call (no intermediate clips, no concat, no mux)
        assert mock_run.call_count == 1

    @patch("utils.video_assembler._detect_hw_encoder", return_value=("libx264", ["-preset", "ultrafast", "-crf", "28"]))
    @patch("utils.video_assembler._run_subprocess")
    @patch("utils.video_assembler.get_audio_duration", return_value=60.0)
    def test_static_mode_no_zoompan(self, mock_duration, mock_run, mock_hw, tmp_path):
        """With use_ken_burns=False, filter_complex has xfade but NOT zoompan."""
        from utils.video_assembler import create_podcast_video

        audio = str(tmp_path / "audio.mp3")
        images = [str(tmp_path / f"img{i}.png") for i in range(4)]
        output = str(tmp_path / "out.mp4")

        create_podcast_video(audio, images, output, use_ken_burns=False)

        # Extract filter_complex from the command
        cmd = mock_run.call_args[0][0]
        fc_idx = cmd.index("-filter_complex")
        filter_str = cmd[fc_idx + 1]

        assert "xfade" in filter_str
        assert "zoompan" not in filter_str

    @patch("utils.video_assembler._detect_hw_encoder", return_value=("libx264", ["-preset", "ultrafast", "-crf", "28"]))
    @patch("utils.video_assembler._run_subprocess")
    @patch("utils.video_assembler.get_audio_duration", return_value=60.0)
    def test_ken_burns_mode_has_zoompan(self, mock_duration, mock_run, mock_hw, tmp_path):
        """With use_ken_burns=True, filter_complex has both zoompan AND xfade."""
        from utils.video_assembler import create_podcast_video

        audio = str(tmp_path / "audio.mp3")
        images = [str(tmp_path / f"img{i}.png") for i in range(4)]
        output = str(tmp_path / "out.mp4")

        create_podcast_video(audio, images, output, use_ken_burns=True, quality="quality")

        cmd = mock_run.call_args[0][0]
        fc_idx = cmd.index("-filter_complex")
        filter_str = cmd[fc_idx + 1]

        assert "zoompan" in filter_str
        assert "xfade" in filter_str

    @patch("utils.video_assembler._run_subprocess")
    @patch("utils.video_assembler.get_audio_duration", return_value=30.0)
    def test_single_image_no_xfade(self, mock_duration, mock_run, tmp_path):
        """With one image, there should be no xfade in the filter graph."""
        from utils.video_assembler import create_podcast_video

        audio = str(tmp_path / "audio.mp3")
        images = [str(tmp_path / "img.png")]
        output = str(tmp_path / "out.mp4")

        create_podcast_video(audio, images, output)

        cmd = mock_run.call_args[0][0]
        fc_idx = cmd.index("-filter_complex")
        filter_str = cmd[fc_idx + 1]

        assert "xfade" not in filter_str

    @patch("utils.video_assembler._run_subprocess")
    @patch("utils.video_assembler.get_audio_duration", return_value=60.0)
    def test_fast_quality_uses_short_timeout(self, mock_duration, mock_run, tmp_path):
        """Fast quality should use a 30s timeout."""
        from utils.video_assembler import create_podcast_video

        audio = str(tmp_path / "audio.mp3")
        images = [str(tmp_path / "img.png")]
        output = str(tmp_path / "out.mp4")

        create_podcast_video(audio, images, output, quality="fast")

        # Check timeout kwarg
        assert mock_run.call_args[1].get("timeout") == 30

    @patch("utils.video_assembler._run_subprocess")
    @patch("utils.video_assembler.get_audio_duration", return_value=60.0)
    def test_quality_mode_uses_long_timeout(self, mock_duration, mock_run, tmp_path):
        """Quality mode should use a 180s timeout."""
        from utils.video_assembler import create_podcast_video

        audio = str(tmp_path / "audio.mp3")
        images = [str(tmp_path / "img.png")]
        output = str(tmp_path / "out.mp4")

        create_podcast_video(audio, images, output, quality="quality")

        assert mock_run.call_args[1].get("timeout") == 180


class TestDetectHwEncoder:
    """Hardware encoder detection."""

    @patch("platform.system", return_value="Darwin")
    @patch("subprocess.run")
    def test_detects_videotoolbox_on_macos(self, mock_run, mock_sys):
        """Returns h264_videotoolbox when available on macOS."""
        from utils.video_assembler import _detect_hw_encoder

        mock_run.return_value = MagicMock(stdout="... h264_videotoolbox ...")

        encoder, args = _detect_hw_encoder()
        assert encoder == "h264_videotoolbox"

    @patch("platform.system", return_value="Darwin")
    @patch("subprocess.run")
    def test_falls_back_to_libx264(self, mock_run, mock_sys):
        """Falls back to libx264 ultrafast when videotoolbox not found."""
        from utils.video_assembler import _detect_hw_encoder

        mock_run.return_value = MagicMock(stdout="... libx264 ...")

        encoder, args = _detect_hw_encoder()
        assert encoder == "libx264"
        assert "-preset" in args
        assert "ultrafast" in args

    @patch("platform.system", return_value="Linux")
    def test_linux_uses_libx264(self, mock_sys):
        """Non-macOS always uses libx264."""
        from utils.video_assembler import _detect_hw_encoder

        encoder, args = _detect_hw_encoder()
        assert encoder == "libx264"


class TestFilterGraphBuilders:
    """Test filter graph helper functions."""

    def test_static_graph_single_image(self):
        """Single image produces a graph with no xfade."""
        from utils.video_assembler import _build_static_filter_graph

        graph, label = _build_static_filter_graph(1, 30.0, 1.0, 24, 1920, 1080)

        assert "scale=1920:1080" in graph
        assert "xfade" not in graph
        assert label == "v0"

    def test_static_graph_multiple_images(self):
        """Multiple images produce xfade chain."""
        from utils.video_assembler import _build_static_filter_graph

        graph, label = _build_static_filter_graph(3, 20.0, 0.5, 24, 1920, 1080)

        assert "xfade" in graph
        assert "zoompan" not in graph
        assert label == "vout"

    def test_ken_burns_graph_has_zoompan(self):
        """Ken Burns graph includes zoompan for each image."""
        from utils.video_assembler import _build_ken_burns_filter_graph

        graph, label = _build_ken_burns_filter_graph(3, 20.0, 0.5, 24, 1920, 1080)

        assert "zoompan" in graph
        assert "xfade" in graph
        assert label == "vout"
