"""
BGM Analyzer
Author: Sarath

Analyzes background music quality including volume levels,
ducking, transitions, and emotion alignment.
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
from utils.quality_evaluator import BGMMetrics


class BGMAnalyzer:
    """Analyzes BGM quality metrics."""

    # Expected volume levels by emotion
    EMOTION_VOLUME_MAP = {
        "reflection": -20,
        "tension": -15,
        "excitement": -14,
        "wonder": -18,
        "triumph": -12,
        "melancholy": -20,
        "intrigue": -17,
        "curiosity": -18,
        "neutral": -18,
    }

    def analyze(
        self,
        bgm_results: List[Dict[str, Any]],
        ducking_data: Optional[Dict[str, Any]] = None
    ) -> BGMMetrics:
        """
        Analyze BGM quality.

        Args:
            bgm_results: BGM generation results
            ducking_data: Optional ducking configuration data

        Returns:
            BGMMetrics with analysis results
        """
        metrics = BGMMetrics()
        issues = []

        if not bgm_results:
            issues.append("No BGM results available")
            metrics.issues = issues
            return metrics

        # Collect volume data
        volumes = []
        successful_segments = 0
        emotions_found = []

        for result in bgm_results:
            path = result.get("path")
            if path and Path(path).exists():
                successful_segments += 1

                # Get volume from result or analyze file
                volume = result.get("volume_db")
                if volume is None:
                    volume = self._analyze_volume(path)
                if volume is not None:
                    volumes.append(volume)

                # Track emotions
                emotion = result.get("emotion") or result.get("bgm_emotion")
                if emotion:
                    emotions_found.append(emotion)

        # Check if any BGM was generated
        if successful_segments == 0:
            issues.append("All BGM generation failed")
            metrics.issues = issues
            return metrics

        # Calculate average volume
        if volumes:
            metrics.avg_volume_db = sum(volumes) / len(volumes)
            metrics.volume_range_db = max(volumes) - min(volumes)

            # Check if volume is appropriate (should be between -20 and -12 dB)
            if metrics.avg_volume_db > -10:
                issues.append(
                    f"BGM too loud (avg {metrics.avg_volume_db:.1f}dB, should be -12 to -20)"
                )
            elif metrics.avg_volume_db < -25:
                issues.append(
                    f"BGM too quiet (avg {metrics.avg_volume_db:.1f}dB, should be -12 to -20)"
                )

            # Check for dynamic variation
            if metrics.volume_range_db < 2:
                issues.append(
                    "BGM volume is static - consider dynamic volume based on emotion"
                )

        # Check ducking
        if ducking_data:
            metrics.ducking_detected = ducking_data.get("enabled", False)
            if ducking_data.get("depth_db"):
                metrics.ducking_depth_db = ducking_data["depth_db"]
        else:
            # Estimate based on configuration or assume no ducking
            metrics.ducking_detected = False
            issues.append("No ducking data available - BGM may mask voice")

        # Count transitions
        metrics.transition_count = max(0, successful_segments - 1)

        # Analyze emotion alignment
        metrics.emotion_alignment = self._analyze_emotion_alignment(
            bgm_results, issues
        )

        metrics.issues = issues
        return metrics

    def _analyze_volume(self, audio_path: str) -> Optional[float]:
        """Analyze audio file to estimate volume in dB."""
        try:
            from pydub import AudioSegment
            audio = AudioSegment.from_file(audio_path)
            return audio.dBFS
        except Exception:
            return None

    def _analyze_emotion_alignment(
        self,
        bgm_results: List[Dict[str, Any]],
        issues: List[str]
    ) -> float:
        """Analyze how well BGM emotions align with content (0-10 score)."""
        if not bgm_results:
            return 5.0

        # Check if BGM has emotion tags
        has_emotion_tags = 0
        for result in bgm_results:
            if result.get("emotion") or result.get("bgm_emotion"):
                has_emotion_tags += 1

        if has_emotion_tags == 0:
            issues.append("BGM segments lack emotion alignment tags")
            return 4.0

        alignment_ratio = has_emotion_tags / len(bgm_results)
        return alignment_ratio * 10


__all__ = ['BGMAnalyzer']
