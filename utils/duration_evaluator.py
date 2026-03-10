"""
Duration Evaluator
Author: Sarath

Evaluates podcast output against target duration specifications.
Used for quality assurance and to verify that generated content
matches user-specified duration targets.

Key metrics:
- Actual duration vs target duration
- Tolerance check (±15% by default)
- Word count and actual words-per-minute
"""

import subprocess
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict, Any


# Default tolerance for duration matching (15%)
DEFAULT_TOLERANCE_PERCENT = 15

# Expected words per minute for podcast narration
EXPECTED_WPM = 150


@dataclass
class DurationEvaluation:
    """
    Evaluation result for podcast duration.

    Attributes:
        target_minutes: Target duration in minutes
        actual_minutes: Actual duration in minutes
        difference_percent: Percentage difference from target
        is_within_tolerance: Whether actual is within acceptable range
        tolerance_percent: Tolerance threshold used
        word_count: Total word count in script (if available)
        words_per_minute_actual: Actual WPM based on audio duration
        audio_path: Path to evaluated audio file
        script_path: Path to script file (if used)
    """
    target_minutes: float
    actual_minutes: float
    difference_percent: float
    is_within_tolerance: bool
    tolerance_percent: float
    word_count: Optional[int] = None
    words_per_minute_actual: Optional[float] = None
    audio_path: Optional[str] = None
    script_path: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert evaluation to dictionary."""
        return {
            "target_minutes": self.target_minutes,
            "actual_minutes": self.actual_minutes,
            "difference_percent": self.difference_percent,
            "is_within_tolerance": self.is_within_tolerance,
            "tolerance_percent": self.tolerance_percent,
            "word_count": self.word_count,
            "words_per_minute_actual": self.words_per_minute_actual,
            "audio_path": self.audio_path,
            "script_path": self.script_path,
        }

    def __str__(self) -> str:
        """Human-readable evaluation summary."""
        status = "PASS" if self.is_within_tolerance else "FAIL"
        sign = "+" if self.difference_percent > 0 else ""
        lines = [
            f"Duration Evaluation: {status}",
            f"  Target:   {self.target_minutes:.1f} min",
            f"  Actual:   {self.actual_minutes:.1f} min",
            f"  Diff:     {sign}{self.difference_percent:.1f}% (tolerance: ±{self.tolerance_percent}%)",
        ]
        if self.word_count:
            lines.append(f"  Words:    {self.word_count}")
        if self.words_per_minute_actual:
            lines.append(f"  WPM:      {self.words_per_minute_actual:.0f} (expected: {EXPECTED_WPM})")
        return "\n".join(lines)


class DurationEvaluator:
    """
    Evaluates podcast output against target duration.

    Uses ffprobe to get actual audio duration and compares against
    the target duration specification.
    """

    def __init__(self, tolerance_percent: float = DEFAULT_TOLERANCE_PERCENT):
        """
        Initialize the evaluator.

        Args:
            tolerance_percent: Acceptable deviation from target (default: 15%)
        """
        self.tolerance_percent = tolerance_percent

    def evaluate(
        self,
        audio_path: str,
        target_minutes: float,
        script_path: Optional[str] = None
    ) -> DurationEvaluation:
        """
        Evaluate podcast audio against target duration.

        Args:
            audio_path: Path to audio/video file
            target_minutes: Target duration in minutes
            script_path: Optional path to script JSON for word count

        Returns:
            DurationEvaluation with comparison metrics

        Raises:
            FileNotFoundError: If audio file doesn't exist
            ValueError: If duration cannot be determined
        """
        audio_file = Path(audio_path)
        if not audio_file.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        # Get actual duration using ffprobe
        actual_seconds = self._get_duration_seconds(audio_path)
        actual_minutes = actual_seconds / 60

        # Calculate difference
        difference_percent = ((actual_minutes - target_minutes) / target_minutes) * 100

        # Check tolerance
        is_within = abs(difference_percent) <= self.tolerance_percent

        # Get word count from script if available
        word_count = None
        wpm_actual = None

        if script_path:
            word_count = self._count_script_words(script_path)
            if word_count and actual_minutes > 0:
                wpm_actual = word_count / actual_minutes

        return DurationEvaluation(
            target_minutes=target_minutes,
            actual_minutes=round(actual_minutes, 2),
            difference_percent=round(difference_percent, 1),
            is_within_tolerance=is_within,
            tolerance_percent=self.tolerance_percent,
            word_count=word_count,
            words_per_minute_actual=round(wpm_actual, 1) if wpm_actual else None,
            audio_path=str(audio_path),
            script_path=script_path,
        )

    def evaluate_from_script(
        self,
        script: Dict[str, Any],
        audio_path: Optional[str] = None
    ) -> DurationEvaluation:
        """
        Evaluate using target duration from script metadata.

        Args:
            script: Enhanced script dictionary with target_duration_minutes
            audio_path: Path to audio file (optional for word-based estimate)

        Returns:
            DurationEvaluation with comparison metrics

        Raises:
            ValueError: If script doesn't contain target duration
        """
        target = script.get("target_duration_minutes")
        if not target:
            raise ValueError("Script does not contain target_duration_minutes")

        if audio_path:
            # Full evaluation with actual audio
            return self.evaluate(
                audio_path=audio_path,
                target_minutes=target,
                script_path=None  # Script already provided
            )

        # Word-based estimate (no audio)
        word_count = self._count_dict_words(script)
        estimated_minutes = word_count / EXPECTED_WPM

        difference_percent = ((estimated_minutes - target) / target) * 100
        is_within = abs(difference_percent) <= self.tolerance_percent

        return DurationEvaluation(
            target_minutes=target,
            actual_minutes=round(estimated_minutes, 2),
            difference_percent=round(difference_percent, 1),
            is_within_tolerance=is_within,
            tolerance_percent=self.tolerance_percent,
            word_count=word_count,
            words_per_minute_actual=EXPECTED_WPM,  # Assumed, not measured
        )

    def _get_duration_seconds(self, audio_path: str) -> float:
        """Get audio duration in seconds using ffprobe."""
        try:
            result = subprocess.run(
                [
                    "ffprobe",
                    "-v", "quiet",
                    "-show_entries", "format=duration",
                    "-of", "json",
                    audio_path
                ],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                raise ValueError(f"ffprobe failed: {result.stderr}")

            data = json.loads(result.stdout)
            duration = float(data.get("format", {}).get("duration", 0))

            if duration <= 0:
                raise ValueError("Could not determine audio duration")

            return duration

        except FileNotFoundError:
            raise ValueError("ffprobe not found. Please install ffmpeg.")
        except json.JSONDecodeError:
            raise ValueError(f"Failed to parse ffprobe output")

    def _count_script_words(self, script_path: str) -> Optional[int]:
        """Count words in a script JSON file."""
        try:
            with open(script_path, 'r') as f:
                script = json.load(f)
            return self._count_dict_words(script)
        except Exception:
            return None

    def _count_dict_words(self, script: Dict[str, Any]) -> int:
        """Count total words in script structure."""
        total = 0

        # Count hook words
        hook = script.get("hook", {})
        if isinstance(hook, dict):
            hook_text = hook.get("text", "")
        else:
            hook_text = str(hook)
        total += len(hook_text.split())

        # Count module words
        for module in script.get("modules", []):
            for chunk in module.get("chunks", []):
                text = chunk.get("text", "")
                total += len(text.split())

        return total


def evaluate_podcast_duration(
    audio_path: str,
    target_minutes: float,
    script_path: Optional[str] = None,
    tolerance_percent: float = DEFAULT_TOLERANCE_PERCENT,
    log_warning: bool = True
) -> DurationEvaluation:
    """
    Convenience function to evaluate podcast duration.

    Args:
        audio_path: Path to audio/video file
        target_minutes: Target duration in minutes
        script_path: Optional path to script JSON
        tolerance_percent: Acceptable deviation (default: 15%)
        log_warning: Print warning if outside tolerance

    Returns:
        DurationEvaluation result
    """
    evaluator = DurationEvaluator(tolerance_percent=tolerance_percent)
    result = evaluator.evaluate(audio_path, target_minutes, script_path)

    if log_warning and not result.is_within_tolerance:
        print(f"[WARNING] Podcast duration outside tolerance:")
        print(result)

    return result


__all__ = [
    'DurationEvaluation',
    'DurationEvaluator',
    'evaluate_podcast_duration',
    'DEFAULT_TOLERANCE_PERCENT',
    'EXPECTED_WPM',
]
