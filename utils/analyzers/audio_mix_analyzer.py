"""
Audio Mix Analyzer
Author: Sarath

Analyzes final audio mix quality including voice/BGM ratio,
loudness, dynamic range, and clipping detection.
"""

import subprocess
import json
from typing import Dict, Any, Optional
from pathlib import Path
from utils.quality_evaluator import AudioMixMetrics


class AudioMixAnalyzer:
    """Analyzes final audio mix quality metrics."""

    def analyze(self, audio_path: str) -> AudioMixMetrics:
        """
        Analyze final audio mix quality.

        Args:
            audio_path: Path to final mixed audio file

        Returns:
            AudioMixMetrics with analysis results
        """
        metrics = AudioMixMetrics()
        issues = []

        if not audio_path or not Path(audio_path).exists():
            issues.append(f"Audio file not found: {audio_path}")
            metrics.issues = issues
            return metrics

        # Get duration
        metrics.duration_seconds = self._get_duration(audio_path)

        # Analyze loudness using ffmpeg loudnorm filter
        loudness_data = self._analyze_loudness(audio_path)
        if loudness_data:
            metrics.loudness_lufs = loudness_data.get("integrated_loudness", -16.0)
            metrics.dynamic_range_db = loudness_data.get("lra", 0.0)

            # Check loudness (ideal: -14 to -16 LUFS for podcasts)
            if metrics.loudness_lufs < -20:
                issues.append(
                    f"Audio too quiet ({metrics.loudness_lufs:.1f} LUFS, "
                    "ideal: -14 to -16)"
                )
            elif metrics.loudness_lufs > -12:
                issues.append(
                    f"Audio too loud ({metrics.loudness_lufs:.1f} LUFS, "
                    "ideal: -14 to -16)"
                )

        # Detect clipping
        metrics.clipping_detected = self._detect_clipping(audio_path)
        if metrics.clipping_detected:
            issues.append("Audio clipping detected - reduce gain levels")

        # Estimate voice/BGM ratio (simplified analysis)
        metrics.voice_bgm_ratio_db = self._estimate_voice_bgm_ratio(audio_path)
        if metrics.voice_bgm_ratio_db < 10:
            issues.append(
                f"Voice/BGM ratio too low ({metrics.voice_bgm_ratio_db:.1f}dB, "
                "ideal: 12-18dB) - voice may be masked"
            )
        elif metrics.voice_bgm_ratio_db > 22:
            issues.append(
                f"Voice/BGM ratio too high ({metrics.voice_bgm_ratio_db:.1f}dB, "
                "ideal: 12-18dB) - BGM may be too quiet"
            )

        metrics.issues = issues
        return metrics

    def _get_duration(self, audio_path: str) -> float:
        """Get audio duration in seconds."""
        try:
            result = subprocess.run(
                [
                    "ffprobe", "-v", "quiet",
                    "-show_entries", "format=duration",
                    "-of", "json",
                    audio_path
                ],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                data = json.loads(result.stdout)
                return float(data.get("format", {}).get("duration", 0))
        except Exception:
            pass
        return 0.0

    def _analyze_loudness(self, audio_path: str) -> Optional[Dict[str, float]]:
        """Analyze loudness using ffmpeg loudnorm filter."""
        try:
            result = subprocess.run(
                [
                    "ffmpeg", "-i", audio_path,
                    "-af", "loudnorm=print_format=json",
                    "-f", "null", "-"
                ],
                capture_output=True,
                text=True,
                timeout=120
            )

            # Parse loudnorm output from stderr
            stderr = result.stderr
            # Find JSON in output
            json_start = stderr.rfind("{")
            json_end = stderr.rfind("}") + 1

            if json_start != -1 and json_end > json_start:
                json_str = stderr[json_start:json_end]
                data = json.loads(json_str)
                return {
                    "integrated_loudness": float(data.get("input_i", -16)),
                    "lra": float(data.get("input_lra", 0)),
                    "true_peak": float(data.get("input_tp", 0)),
                }
        except Exception:
            pass
        return None

    def _detect_clipping(self, audio_path: str) -> bool:
        """Detect audio clipping using ffmpeg astats filter."""
        try:
            result = subprocess.run(
                [
                    "ffmpeg", "-i", audio_path,
                    "-af", "astats=metadata=1:reset=1",
                    "-f", "null", "-"
                ],
                capture_output=True,
                text=True,
                timeout=120
            )

            # Check for clipping indicators in output
            # High peak levels near 0 dBFS indicate potential clipping
            stderr = result.stderr.lower()
            return "clip" in stderr or "overload" in stderr

        except Exception:
            pass
        return False

    def _estimate_voice_bgm_ratio(self, audio_path: str) -> float:
        """
        Estimate voice/BGM ratio.

        This is a simplified estimation based on typical podcast mixing.
        A more accurate analysis would require source separation.
        """
        # Default estimate based on common mixing practices
        # For more accurate analysis, could use source separation
        # or analyze silence vs speech segments
        try:
            from pydub import AudioSegment
            audio = AudioSegment.from_file(audio_path)

            # Analyze peak vs RMS (speech has higher peaks than BGM)
            peak = audio.max_dBFS
            rms = audio.dBFS

            # Rough estimate: difference gives indication of dynamic range
            # Higher difference suggests clearer voice/BGM separation
            return abs(peak - rms) + 10  # Add baseline

        except Exception:
            pass

        return 15.0  # Default estimate


__all__ = ['AudioMixAnalyzer']
