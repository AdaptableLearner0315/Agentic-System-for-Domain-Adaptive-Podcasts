"""
Ending Analyzer
Author: Sarath

Analyzes ending quality including fadeout presence,
final level, and abrupt ending detection.
"""

from typing import Dict, Any
from pathlib import Path
from utils.quality_evaluator import EndingMetrics


class EndingAnalyzer:
    """Analyzes ending quality metrics."""

    def analyze(self, audio_path: str) -> EndingMetrics:
        """
        Analyze ending quality.

        Args:
            audio_path: Path to final audio file

        Returns:
            EndingMetrics with analysis results
        """
        metrics = EndingMetrics()
        issues = []

        if not audio_path or not Path(audio_path).exists():
            issues.append(f"Audio file not found: {audio_path}")
            metrics.issues = issues
            return metrics

        try:
            from pydub import AudioSegment
            audio = AudioSegment.from_file(audio_path)

            # Analyze the last 5 seconds
            if len(audio) > 5000:
                ending = audio[-5000:]
            else:
                ending = audio

            # Get final level (last 500ms)
            final_segment = ending[-500:]
            metrics.final_level_db = final_segment.dBFS

            # Detect fadeout by analyzing volume progression
            metrics.fadeout_present, metrics.fadeout_duration_ms = (
                self._detect_fadeout(ending)
            )

            # Detect abrupt ending
            metrics.is_abrupt = self._detect_abrupt_ending(
                ending, metrics.fadeout_present
            )

            # Check for outro content
            # (simplified - would ideally analyze script metadata)
            metrics.has_outro = not metrics.is_abrupt and metrics.fadeout_present

            # Generate issues
            if metrics.is_abrupt:
                issues.append(
                    "Abrupt ending detected - no fadeout applied"
                )

            if not metrics.fadeout_present:
                issues.append(
                    "No fadeout detected - ending may feel sudden"
                )

            if metrics.final_level_db > -30:
                issues.append(
                    f"Final audio level too high ({metrics.final_level_db:.1f}dB, "
                    "should be < -40dB)"
                )

        except Exception as e:
            issues.append(f"Ending analysis error: {e}")

        metrics.issues = issues
        return metrics

    def _detect_fadeout(self, audio_segment) -> tuple:
        """
        Detect if audio has a fadeout.

        Args:
            audio_segment: pydub AudioSegment of ending

        Returns:
            Tuple of (fadeout_present: bool, fadeout_duration_ms: int)
        """
        duration_ms = len(audio_segment)
        if duration_ms < 1000:
            return False, 0

        # Split ending into chunks and analyze volume progression
        chunk_size = 500  # 500ms chunks
        chunks = []

        for i in range(0, duration_ms - chunk_size, chunk_size):
            chunk = audio_segment[i:i + chunk_size]
            chunks.append(chunk.dBFS)

        if len(chunks) < 3:
            return False, 0

        # Check if volume consistently decreases
        decreasing_count = 0
        for i in range(1, len(chunks)):
            if chunks[i] < chunks[i - 1]:
                decreasing_count += 1

        # If more than 60% of chunks show decrease, likely fadeout
        if decreasing_count / (len(chunks) - 1) > 0.6:
            # Estimate fadeout duration
            total_decrease = chunks[0] - chunks[-1]
            if total_decrease > 10:  # Significant decrease
                return True, duration_ms
            elif total_decrease > 5:
                return True, duration_ms // 2

        return False, 0

    def _detect_abrupt_ending(
        self,
        audio_segment,
        has_fadeout: bool
    ) -> bool:
        """
        Detect if audio ends abruptly.

        Args:
            audio_segment: pydub AudioSegment of ending
            has_fadeout: Whether fadeout was detected

        Returns:
            True if ending is abrupt
        """
        if has_fadeout:
            return False

        # Check if final audio level is high (suggesting cut-off)
        final_100ms = audio_segment[-100:]
        final_level = final_100ms.dBFS

        # If final level is above -35dB, likely abrupt
        if final_level > -35:
            return True

        # Check for sudden drop in last 200ms
        if len(audio_segment) > 200:
            pre_final = audio_segment[-200:-100]
            if pre_final.dBFS - final_100ms.dBFS > 20:
                return True  # Sudden drop = abrupt

        return False


__all__ = ['EndingAnalyzer']
