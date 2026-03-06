"""
Voice Analyzer
Author: Sarath

Analyzes voice/TTS quality including generation success rate,
emotion coverage, and speed variation.
"""

from typing import Dict, Any, List
from pathlib import Path
from utils.quality_evaluator import VoiceMetrics


class VoiceAnalyzer:
    """Analyzes voice/TTS quality metrics."""

    def analyze(self, tts_results: List[Dict[str, Any]]) -> VoiceMetrics:
        """
        Analyze voice/TTS quality.

        Args:
            tts_results: TTS generation results

        Returns:
            VoiceMetrics with analysis results
        """
        metrics = VoiceMetrics()
        issues = []

        if not tts_results:
            issues.append("No TTS results available")
            metrics.issues = issues
            return metrics

        metrics.sentence_count = len(tts_results)

        # Count failures and successes
        successful_paths = []
        emotions_set = set()
        speeds = []

        for result in tts_results:
            path = result.get("path")
            if not path or not Path(path).exists():
                metrics.failed_count += 1
                if result.get("error"):
                    issues.append(f"TTS error: {result['error'][:100]}")
            else:
                successful_paths.append(path)

            # Track emotions
            emotion = result.get("emotion")
            if emotion:
                emotions_set.add(emotion)

            # Track speed variations
            speed = result.get("speed", 1.0)
            if speed:
                speeds.append(speed)

        # Calculate failure rate
        if metrics.sentence_count > 0:
            failure_rate = metrics.failed_count / metrics.sentence_count * 100
            if failure_rate > 10:
                issues.append(
                    f"High TTS failure rate: {failure_rate:.1f}% "
                    f"({metrics.failed_count}/{metrics.sentence_count})"
                )
            elif failure_rate > 0:
                issues.append(
                    f"Some TTS failures: {metrics.failed_count} of "
                    f"{metrics.sentence_count} sentences"
                )

        # Calculate emotion coverage
        if metrics.sentence_count > 0:
            # Count sentences with emotions
            sentences_with_emotion = sum(
                1 for r in tts_results if r.get("emotion") and r.get("emotion") != "neutral"
            )
            metrics.emotion_coverage = sentences_with_emotion / metrics.sentence_count * 100

        # Calculate speed variation
        if speeds and len(speeds) > 1:
            min_speed = min(speeds)
            max_speed = max(speeds)
            metrics.speed_variation = max_speed - min_speed

        # Calculate average duration (if durations are available)
        durations = []
        for path in successful_paths:
            duration = self._get_audio_duration(path)
            if duration:
                durations.append(duration)

        if durations:
            metrics.avg_duration_ms = sum(durations) / len(durations)

        metrics.issues = issues
        return metrics

    def _get_audio_duration(self, audio_path: str) -> float:
        """Get audio duration in milliseconds using pydub."""
        try:
            from pydub import AudioSegment
            audio = AudioSegment.from_file(audio_path)
            return len(audio)  # Duration in ms
        except Exception:
            return 0.0


__all__ = ['VoiceAnalyzer']
