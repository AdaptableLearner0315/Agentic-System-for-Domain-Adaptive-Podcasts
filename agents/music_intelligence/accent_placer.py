"""
Accent Placer
Author: Sarath

Places musical accents (risers, impacts, swells, drops) at key emotional moments.
Adds punctuation that amplifies peaks and transitions.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any, Optional

from config.music_intelligence import (
    ACCENT_TYPES,
    NORMAL_MODE,
    PRO_MODE,
)
from .emotion_timeline import EmotionSegment


@dataclass
class AccentPoint:
    """
    Represents a point where an accent should be placed.

    Attributes:
        time_ms: Time position in milliseconds
        accent_type: Type of accent (riser, impact, swell, drop)
        intensity: Intensity level (0.0 - 1.0)
        trigger_emotion: Emotion that triggered this accent
        trigger_segment_id: ID of the segment that triggered this accent
    """
    time_ms: int
    accent_type: str
    intensity: float = 1.0
    trigger_emotion: str = ""
    trigger_segment_id: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "time_ms": self.time_ms,
            "accent_type": self.accent_type,
            "intensity": self.intensity,
            "trigger_emotion": self.trigger_emotion,
            "trigger_segment_id": self.trigger_segment_id,
        }


class AccentPlacer:
    """
    Places musical accents at emotional peaks and transitions.

    Accent Types:
    - Riser: Building sweep before tension peak (2-4s before)
    - Impact: Percussive hit at peak moment
    - Swell: Emotional crescendo for revelations (wonder, triumph, liberation)
    - Drop: Sudden reduction/silence after climax
    """

    def __init__(self, catalog_path: Optional[Path] = None, output_dir: Optional[Path] = None):
        """
        Initialize the accent placer.

        Args:
            catalog_path: Path to accent catalog directory
            output_dir: Directory for output files
        """
        if catalog_path:
            self.catalog_path = Path(catalog_path)
        else:
            self.catalog_path = Path(__file__).parent.parent.parent / "assets" / "music" / "accents"

        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            self.output_dir = Path(__file__).parent.parent.parent / "Output" / "audio" / "bgm_intelligent"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self._accent_files: Dict[str, List[str]] = {}
        self._load_accent_files()

    def _load_accent_files(self):
        """Load available accent files from catalog directory."""
        for accent_type in ACCENT_TYPES.keys():
            accent_dir = self.catalog_path / f"{accent_type}s"
            if accent_dir.exists():
                files = list(accent_dir.glob("*.wav")) + list(accent_dir.glob("*.mp3"))
                self._accent_files[accent_type] = [str(f) for f in files]
            else:
                self._accent_files[accent_type] = []

    def detect_accent_points(
        self,
        timeline: List[EmotionSegment],
        density: str = "low"
    ) -> List[AccentPoint]:
        """
        Detect points where accents should be placed.

        Args:
            timeline: Emotion timeline
            density: "low" for Normal mode (1-2 accents), "high" for Pro mode (4-8)

        Returns:
            List of AccentPoint objects
        """
        points = []
        max_points = NORMAL_MODE["max_accent_points"] if density == "low" else PRO_MODE["max_accent_points"]

        # Find peaks for riser + impact placement
        peak_segments = [seg for seg in timeline if seg.is_peak]

        for seg in peak_segments[:max_points // 2]:
            # Place riser before peak
            riser_time = max(0, seg.start_ms + ACCENT_TYPES["riser"]["offset_ms"])
            points.append(AccentPoint(
                time_ms=riser_time,
                accent_type="riser",
                intensity=seg.tension_level / 5.0,
                trigger_emotion=seg.emotion,
                trigger_segment_id=seg.chunk_id,
            ))

            # Place impact at peak
            points.append(AccentPoint(
                time_ms=seg.start_ms,
                accent_type="impact",
                intensity=seg.tension_level / 5.0,
                trigger_emotion=seg.emotion,
                trigger_segment_id=seg.chunk_id,
            ))

            # Place drop after peak (only in high density)
            if density == "high" and seg.start_ms + 500 < timeline[-1].end_ms:
                points.append(AccentPoint(
                    time_ms=seg.start_ms + ACCENT_TYPES["drop"]["offset_ms"],
                    accent_type="drop",
                    intensity=0.7,
                    trigger_emotion=seg.emotion,
                    trigger_segment_id=seg.chunk_id,
                ))

        # Find emotional revelations for swell placement
        swell_emotions = ACCENT_TYPES["swell"]["emotions"]
        revelation_segments = [
            seg for seg in timeline
            if seg.emotion.lower() in swell_emotions and not seg.is_peak
        ]

        remaining_slots = max_points - len(points)
        for seg in revelation_segments[:remaining_slots]:
            points.append(AccentPoint(
                time_ms=seg.midpoint_ms,
                accent_type="swell",
                intensity=seg.tension_level / 5.0,
                trigger_emotion=seg.emotion,
                trigger_segment_id=seg.chunk_id,
            ))

        # Sort by time
        points.sort(key=lambda p: p.time_ms)

        return points

    def place_accents(
        self,
        audio_path: str,
        timeline: List[EmotionSegment],
        density: str = "low"
    ) -> str:
        """
        Place accents on audio based on timeline.

        Args:
            audio_path: Path to base audio file
            timeline: Emotion timeline
            density: Accent density ("low" or "high")

        Returns:
            Path to audio with accents
        """
        if not Path(audio_path).exists():
            return audio_path

        try:
            from pydub import AudioSegment
        except ImportError:
            print("[AccentPlacer] pydub not available")
            return audio_path

        try:
            audio = AudioSegment.from_file(audio_path)
        except Exception as e:
            print(f"[AccentPlacer] Error loading audio: {e}")
            return audio_path

        # Detect accent points
        points = self.detect_accent_points(timeline, density)

        if not points:
            return audio_path

        # Apply accents
        for point in points:
            accent_audio = self._get_accent_audio(point)
            if accent_audio:
                # Adjust volume based on intensity
                volume_db = -6 + (point.intensity * 6)  # -6dB to 0dB range
                accent_audio = accent_audio + volume_db

                # Overlay at position
                audio = audio.overlay(accent_audio, position=point.time_ms)

        # Export
        output_path = self.output_dir / "bgm_with_accents.wav"
        audio.export(str(output_path), format="wav")

        return str(output_path)

    def _get_accent_audio(self, point: AccentPoint):
        """Get appropriate accent audio for a point."""
        try:
            from pydub import AudioSegment
        except ImportError:
            return None

        accent_files = self._accent_files.get(point.accent_type, [])

        if not accent_files:
            # Generate synthetic accent if no files available
            return self._generate_synthetic_accent(point)

        # Select a random accent file
        import random
        accent_path = random.choice(accent_files)

        try:
            return AudioSegment.from_file(accent_path)
        except Exception as e:
            print(f"[AccentPlacer] Error loading accent: {e}")
            return self._generate_synthetic_accent(point)

    def _generate_synthetic_accent(self, point: AccentPoint):
        """Generate a synthetic accent when no files are available."""
        try:
            from pydub import AudioSegment
            from pydub.generators import Sine, WhiteNoise
        except ImportError:
            return None

        accent_config = ACCENT_TYPES.get(point.accent_type, {})
        duration_range = accent_config.get("duration_range_ms", (500, 1000))
        duration = duration_range[0]

        try:
            if point.accent_type == "riser":
                # Ascending tone
                start_freq = 100
                end_freq = 800
                riser = AudioSegment.empty()
                steps = 20
                step_duration = duration // steps
                for i in range(steps):
                    freq = start_freq + (end_freq - start_freq) * (i / steps)
                    tone = Sine(freq).to_audio_segment(duration=step_duration)
                    # Increase volume through riser
                    tone = tone + (i * 0.5 - 5)
                    riser += tone
                return riser.fade_in(100).fade_out(50)

            elif point.accent_type == "impact":
                # Short percussive hit
                impact = Sine(80).to_audio_segment(duration=100)
                noise = WhiteNoise().to_audio_segment(duration=50) - 10
                return (impact.overlay(noise)).fade_out(80)

            elif point.accent_type == "swell":
                # Gradual crescendo
                swell = Sine(220).to_audio_segment(duration=duration)
                return swell.fade_in(duration // 2).fade_out(duration // 4)

            elif point.accent_type == "drop":
                # Very short silence marker (not actual audio, just reduces volume)
                return AudioSegment.silent(duration=500) - 20

            else:
                return AudioSegment.silent(duration=100)

        except Exception as e:
            print(f"[AccentPlacer] Error generating synthetic accent: {e}")
            return None


def detect_accent_points(
    timeline: List[EmotionSegment],
    density: str = "low"
) -> List[AccentPoint]:
    """
    Convenience function to detect accent points.

    Args:
        timeline: Emotion timeline
        density: "low" or "high"

    Returns:
        List of AccentPoint objects
    """
    placer = AccentPlacer()
    return placer.detect_accent_points(timeline, density)


__all__ = [
    'AccentPoint',
    'AccentPlacer',
    'detect_accent_points',
]
