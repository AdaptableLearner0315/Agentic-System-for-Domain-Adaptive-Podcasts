"""
Unit tests for Duration Evaluator utility.
Author: Sarath

Tests evaluation of podcast output against target duration specifications.
"""

import pytest
import json
import subprocess
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.duration_evaluator import (
    DurationEvaluation,
    DurationEvaluator,
    evaluate_podcast_duration,
    DEFAULT_TOLERANCE_PERCENT,
    EXPECTED_WPM,
)


class TestDurationEvaluation:
    """Tests for DurationEvaluation dataclass."""

    def test_to_dict(self):
        """Test conversion to dictionary."""
        eval_result = DurationEvaluation(
            target_minutes=10.0,
            actual_minutes=9.5,
            difference_percent=-5.0,
            is_within_tolerance=True,
            tolerance_percent=15.0,
            word_count=1500,
            words_per_minute_actual=157.9,
            audio_path="/path/to/audio.mp3",
        )

        result_dict = eval_result.to_dict()

        assert result_dict["target_minutes"] == 10.0
        assert result_dict["actual_minutes"] == 9.5
        assert result_dict["difference_percent"] == -5.0
        assert result_dict["is_within_tolerance"] is True
        assert result_dict["word_count"] == 1500

    def test_str_representation_pass(self):
        """Test string representation for passing evaluation."""
        eval_result = DurationEvaluation(
            target_minutes=10.0,
            actual_minutes=9.5,
            difference_percent=-5.0,
            is_within_tolerance=True,
            tolerance_percent=15.0,
        )

        result_str = str(eval_result)

        assert "PASS" in result_str
        assert "10.0 min" in result_str
        assert "9.5 min" in result_str

    def test_str_representation_fail(self):
        """Test string representation for failing evaluation."""
        eval_result = DurationEvaluation(
            target_minutes=10.0,
            actual_minutes=7.0,
            difference_percent=-30.0,
            is_within_tolerance=False,
            tolerance_percent=15.0,
        )

        result_str = str(eval_result)

        assert "FAIL" in result_str

    def test_str_includes_word_count_when_present(self):
        """Test string includes word count when available."""
        eval_result = DurationEvaluation(
            target_minutes=10.0,
            actual_minutes=10.0,
            difference_percent=0.0,
            is_within_tolerance=True,
            tolerance_percent=15.0,
            word_count=1500,
            words_per_minute_actual=150.0,
        )

        result_str = str(eval_result)

        assert "1500" in result_str
        assert "WPM" in result_str


class TestDurationEvaluator:
    """Tests for DurationEvaluator class."""

    @pytest.fixture
    def evaluator(self):
        """Create evaluator instance."""
        return DurationEvaluator(tolerance_percent=15.0)

    @pytest.fixture
    def mock_ffprobe(self):
        """Mock ffprobe subprocess call."""
        with patch('subprocess.run') as mock_run:
            yield mock_run

    def test_evaluate_within_tolerance(self, evaluator, mock_ffprobe, tmp_path):
        """Test evaluation passes when within tolerance."""
        # Create temp audio file
        audio_file = tmp_path / "test.mp3"
        audio_file.write_text("fake audio")

        # Mock ffprobe to return 9.5 minutes (570 seconds)
        mock_ffprobe.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps({"format": {"duration": "570.0"}})
        )

        result = evaluator.evaluate(
            audio_path=str(audio_file),
            target_minutes=10.0
        )

        assert result.is_within_tolerance is True
        assert result.actual_minutes == 9.5
        assert result.difference_percent == -5.0

    def test_evaluate_outside_tolerance(self, evaluator, mock_ffprobe, tmp_path):
        """Test evaluation fails when outside tolerance."""
        audio_file = tmp_path / "test.mp3"
        audio_file.write_text("fake audio")

        # Mock ffprobe to return 7 minutes (420 seconds) - 30% under target
        mock_ffprobe.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps({"format": {"duration": "420.0"}})
        )

        result = evaluator.evaluate(
            audio_path=str(audio_file),
            target_minutes=10.0
        )

        assert result.is_within_tolerance is False
        assert result.actual_minutes == 7.0
        assert result.difference_percent == -30.0

    def test_evaluate_with_script_word_count(self, evaluator, mock_ffprobe, tmp_path):
        """Test evaluation includes word count from script."""
        audio_file = tmp_path / "test.mp3"
        audio_file.write_text("fake audio")

        script_file = tmp_path / "script.json"
        script_data = {
            "hook": {"text": "This is a test hook with ten words in it."},
            "modules": [
                {"chunks": [{"text": "Module one chunk with five words."}]}
            ]
        }
        script_file.write_text(json.dumps(script_data))

        # Mock ffprobe to return 10 minutes (600 seconds)
        mock_ffprobe.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps({"format": {"duration": "600.0"}})
        )

        result = evaluator.evaluate(
            audio_path=str(audio_file),
            target_minutes=10.0,
            script_path=str(script_file)
        )

        assert result.word_count is not None
        assert result.word_count > 0
        assert result.words_per_minute_actual is not None

    def test_evaluate_file_not_found(self, evaluator):
        """Test evaluation raises error for missing file."""
        with pytest.raises(FileNotFoundError):
            evaluator.evaluate(
                audio_path="/nonexistent/path.mp3",
                target_minutes=10.0
            )

    def test_evaluate_ffprobe_failure(self, evaluator, mock_ffprobe, tmp_path):
        """Test evaluation handles ffprobe failure."""
        audio_file = tmp_path / "test.mp3"
        audio_file.write_text("fake audio")

        mock_ffprobe.return_value = MagicMock(
            returncode=1,
            stderr="ffprobe error"
        )

        with pytest.raises(ValueError, match="ffprobe failed"):
            evaluator.evaluate(
                audio_path=str(audio_file),
                target_minutes=10.0
            )

    def test_evaluate_from_script_with_audio(self, evaluator, mock_ffprobe, tmp_path):
        """Test evaluate_from_script with audio file."""
        audio_file = tmp_path / "test.mp3"
        audio_file.write_text("fake audio")

        script = {
            "target_duration_minutes": 10,
            "hook": {"text": "Test hook."},
            "modules": []
        }

        mock_ffprobe.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps({"format": {"duration": "600.0"}})
        )

        result = evaluator.evaluate_from_script(
            script=script,
            audio_path=str(audio_file)
        )

        assert result.target_minutes == 10
        assert result.actual_minutes == 10.0

    def test_evaluate_from_script_word_based(self, evaluator):
        """Test evaluate_from_script without audio (word-based estimate)."""
        # Script with ~150 words = 1 minute estimated
        script = {
            "target_duration_minutes": 1,
            "hook": {"text": " ".join(["word"] * 50)},  # 50 words
            "modules": [
                {"chunks": [{"text": " ".join(["word"] * 100)}]}  # 100 words
            ]
        }

        result = evaluator.evaluate_from_script(script=script)

        assert result.target_minutes == 1
        assert result.word_count == 150
        # 150 words / 150 WPM = 1 minute
        assert result.actual_minutes == 1.0

    def test_evaluate_from_script_missing_target(self, evaluator):
        """Test evaluate_from_script raises error without target."""
        script = {"hook": {"text": "Test"}, "modules": []}

        with pytest.raises(ValueError, match="does not contain target_duration"):
            evaluator.evaluate_from_script(script=script)


class TestConvenienceFunction:
    """Tests for evaluate_podcast_duration convenience function."""

    def test_convenience_function_logs_warning(self, tmp_path, capsys):
        """Test that convenience function logs warning when outside tolerance."""
        audio_file = tmp_path / "test.mp3"
        audio_file.write_text("fake audio")

        with patch('subprocess.run') as mock_run:
            # Return 7 minutes (30% under 10 minute target)
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=json.dumps({"format": {"duration": "420.0"}})
            )

            result = evaluate_podcast_duration(
                audio_path=str(audio_file),
                target_minutes=10.0,
                log_warning=True
            )

            captured = capsys.readouterr()
            assert "WARNING" in captured.out
            assert result.is_within_tolerance is False


class TestToleranceConfiguration:
    """Tests for tolerance configuration."""

    def test_custom_tolerance(self, tmp_path):
        """Test custom tolerance percentage."""
        evaluator = DurationEvaluator(tolerance_percent=5.0)  # Strict 5%

        audio_file = tmp_path / "test.mp3"
        audio_file.write_text("fake audio")

        with patch('subprocess.run') as mock_run:
            # 9 minutes is 10% under target - should fail with 5% tolerance
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=json.dumps({"format": {"duration": "540.0"}})
            )

            result = evaluator.evaluate(
                audio_path=str(audio_file),
                target_minutes=10.0
            )

            assert result.is_within_tolerance is False
            assert result.tolerance_percent == 5.0

    def test_default_tolerance(self):
        """Test default tolerance is 15%."""
        evaluator = DurationEvaluator()
        assert evaluator.tolerance_percent == DEFAULT_TOLERANCE_PERCENT
        assert evaluator.tolerance_percent == 15


class TestWordCounting:
    """Tests for word counting functionality."""

    def test_count_dict_words_hook_text(self):
        """Test word counting in hook text."""
        evaluator = DurationEvaluator()

        script = {
            "hook": {"text": "One two three four five"},
            "modules": []
        }

        count = evaluator._count_dict_words(script)
        assert count == 5

    def test_count_dict_words_hook_string(self):
        """Test word counting when hook is string (legacy format)."""
        evaluator = DurationEvaluator()

        script = {
            "hook": "One two three",
            "modules": []
        }

        count = evaluator._count_dict_words(script)
        assert count == 3

    def test_count_dict_words_modules(self):
        """Test word counting across modules."""
        evaluator = DurationEvaluator()

        script = {
            "hook": {"text": "Hook text"},  # 2 words
            "modules": [
                {"chunks": [
                    {"text": "First chunk text"},  # 3 words
                    {"text": "Second chunk"}  # 2 words
                ]},
                {"chunks": [
                    {"text": "Another chunk"}  # 2 words
                ]}
            ]
        }

        count = evaluator._count_dict_words(script)
        assert count == 9  # 2 + 3 + 2 + 2
