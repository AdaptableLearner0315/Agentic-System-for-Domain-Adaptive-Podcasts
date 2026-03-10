"""
Pacing Analyzer
Author: Sarath

Analyzes pacing quality including pause durations, tempo variation,
and emotion alignment of pauses.
"""

from typing import Dict, Any, List, Optional
from utils.quality_evaluator import PacingMetrics


class PacingAnalyzer:
    """Analyzes pacing quality metrics."""

    # Expected pause duration by pause style (from emotion_voice_mapping)
    EXPECTED_PAUSES = {
        "contemplative": 450,
        "questioning": 350,
        "dramatic": 400,
        "confident": 300,
        "slow": 500,
        "mysterious": 400,
        "quick": 250,
        "thoughtful": 450,
        "edgy": 300,
        "defiant": 300,
        "triumphant": 350,
        "creative": 350,
        "normal": 350,
    }

    def analyze(
        self,
        tts_results: List[Dict[str, Any]],
        pause_metadata: Optional[Dict[str, Any]] = None
    ) -> PacingMetrics:
        """
        Analyze pacing quality.

        Args:
            tts_results: TTS generation results with timing info
            pause_metadata: Optional pause duration metadata

        Returns:
            PacingMetrics with analysis results
        """
        metrics = PacingMetrics()
        issues = []

        if not tts_results:
            issues.append("No TTS results available for pacing analysis")
            metrics.issues = issues
            return metrics

        # Collect pause data
        pause_durations = []
        emotions_with_pauses = []

        # Check if pause metadata is available
        if pause_metadata:
            for entry in pause_metadata.get("pauses", []):
                pause_durations.append(entry.get("duration_ms", 350))
                emotions_with_pauses.append(entry.get("emotion", "neutral"))

        # If no explicit pause data, infer from TTS results
        if not pause_durations:
            # Check if all results have same pause or have emotion-based variation
            unique_emotions = set()
            for result in tts_results:
                emotion = result.get("emotion", "neutral")
                unique_emotions.add(emotion)

            # Estimate pause durations based on emotions
            for result in tts_results:
                emotion = result.get("emotion", "neutral")
                pause_style = self._get_pause_style_for_emotion(emotion)
                expected_pause = self.EXPECTED_PAUSES.get(pause_style, 350)
                pause_durations.append(expected_pause)
                emotions_with_pauses.append(emotion)

        # Calculate metrics
        if pause_durations:
            metrics.avg_sentence_pause_ms = sum(pause_durations) / len(pause_durations)

            # Check for uniform pauses (all same value)
            unique_pauses = set(pause_durations)
            metrics.uniform_pause_detected = len(unique_pauses) == 1

            if metrics.uniform_pause_detected:
                issues.append(
                    f"Uniform {metrics.avg_sentence_pause_ms:.0f}ms pauses "
                    "detected - lacks natural variation"
                )

            # Calculate pause variation
            if len(pause_durations) > 1:
                min_pause = min(pause_durations)
                max_pause = max(pause_durations)
                avg_pause = sum(pause_durations) / len(pause_durations)
                if avg_pause > 0:
                    metrics.pause_variation_pct = (
                        (max_pause - min_pause) / avg_pause * 100
                    )
            else:
                metrics.pause_variation_pct = 0

        # Analyze emotion alignment
        metrics.emotion_alignment = self._analyze_emotion_alignment(
            tts_results, pause_durations, issues
        )

        # Analyze tempo variation
        metrics.tempo_variation = self._analyze_tempo_variation(tts_results, issues)

        metrics.issues = issues
        return metrics

    def _get_pause_style_for_emotion(self, emotion: str) -> str:
        """Map emotion to pause style."""
        emotion_to_pause_style = {
            "wonder": "contemplative",
            "curiosity": "questioning",
            "tension": "dramatic",
            "triumph": "confident",
            "melancholy": "slow",
            "intrigue": "mysterious",
            "excitement": "quick",
            "reflection": "thoughtful",
            "restlessness": "edgy",
            "rebellion": "defiant",
            "liberation": "triumphant",
            "experimentation": "creative",
            "mastery": "confident",
            "intensity": "dramatic",
            "neutral": "normal",
        }
        return emotion_to_pause_style.get(emotion.lower(), "normal")

    def _analyze_emotion_alignment(
        self,
        tts_results: List[Dict[str, Any]],
        pause_durations: List[float],
        issues: List[str]
    ) -> float:
        """Analyze how well pauses align with emotions (0-10 score)."""
        if not tts_results or not pause_durations:
            return 5.0

        aligned_count = 0
        total_checked = 0

        for i, result in enumerate(tts_results):
            if i >= len(pause_durations):
                break

            emotion = result.get("emotion", "neutral")
            actual_pause = pause_durations[i]

            pause_style = self._get_pause_style_for_emotion(emotion)
            expected_pause = self.EXPECTED_PAUSES.get(pause_style, 350)

            total_checked += 1
            # Allow 20% tolerance
            if abs(actual_pause - expected_pause) / expected_pause < 0.2:
                aligned_count += 1

        if total_checked == 0:
            return 5.0

        alignment_pct = aligned_count / total_checked * 100
        if alignment_pct < 50:
            issues.append(
                f"Low pause-emotion alignment ({alignment_pct:.0f}%) - "
                "pauses don't match emotional context"
            )

        return alignment_pct / 10  # Convert to 0-10 scale

    def _analyze_tempo_variation(
        self,
        tts_results: List[Dict[str, Any]],
        issues: List[str]
    ) -> float:
        """Analyze tempo variation across the podcast (0-10 score)."""
        # Get speed variations from TTS results
        speeds = []
        for result in tts_results:
            # Speed might come from emotion-based TTS settings
            speed = result.get("speed", 1.0)
            if speed:
                speeds.append(speed)

        if not speeds:
            return 5.0

        min_speed = min(speeds)
        max_speed = max(speeds)
        variation = max_speed - min_speed

        # Good variation is 0.15-0.25 (e.g., 0.90 to 1.15)
        if variation < 0.05:
            issues.append("Minimal tempo variation - consider varying narration speed")
            return 4.0
        elif 0.15 <= variation <= 0.30:
            return 8.0
        elif variation > 0.30:
            return 7.0  # Too much variation
        else:
            return 6.0


__all__ = ['PacingAnalyzer']
