"""
Stem Composer (Pro Mode)
Author: Sarath

Dynamically composes music by mixing layered stems based on emotion timeline.
Creates rich, responsive soundscapes with precise energy tracking.
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional

from config.music_intelligence import (
    PRO_MODE,
    ENERGY_TO_LAYERS,
    LAYER_VOLUME_CURVES,
    get_emotion_profile,
    get_layers_for_energy,
)
from .emotion_timeline import EmotionSegment


class StemComposer:
    """
    Composes music dynamically using layered stems.

    Stem Layers:
    - Atmosphere: Continuous ambient bed, texture changes with emotion
    - Rhythm: Energy and drive, intensity tracks tension level
    - Melody: Emotional hook, enters at key moments

    Energy Mapping:
    - Tension 1-2: Atmosphere only (sparse)
    - Tension 3: Atmosphere + light Rhythm
    - Tension 4: Atmosphere + Rhythm + hints of Melody
    - Tension 5: All layers full (climax)
    """

    def __init__(self, catalog_path: Optional[Path] = None, output_dir: Optional[Path] = None):
        """
        Initialize the stem composer.

        Args:
            catalog_path: Path to stem catalog JSON file
            output_dir: Directory for output files
        """
        if catalog_path:
            self.catalog_path = Path(catalog_path)
        else:
            self.catalog_path = Path(__file__).parent.parent.parent / "assets" / "music" / "stems" / "catalog.json"

        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            self.output_dir = Path(__file__).parent.parent.parent / "Output" / "audio" / "bgm_intelligent"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self._catalog: Dict[str, Any] = {}
        self._load_catalog()

    def _load_catalog(self):
        """Load stem catalog from disk."""
        if self.catalog_path.exists():
            try:
                with open(self.catalog_path, 'r') as f:
                    self._catalog = json.load(f)
            except Exception as e:
                print(f"[StemComposer] Error loading catalog: {e}")
                self._catalog = {"stems": {"atmosphere": [], "rhythm": [], "melody": []}}
        else:
            self._catalog = {"stems": {"atmosphere": [], "rhythm": [], "melody": []}}

    def get_stems_for_layer(self, layer: str) -> List[Dict[str, Any]]:
        """Get all stems for a specific layer."""
        return self._catalog.get("stems", {}).get(layer, [])

    def select_stems_for_emotion(
        self,
        emotion: str,
        tension_level: int
    ) -> Dict[str, Optional[str]]:
        """
        Select appropriate stems for an emotion and energy level.

        Args:
            emotion: Target emotion
            tension_level: Tension level (1-5)

        Returns:
            Dictionary mapping layer names to stem paths
        """
        profile = get_emotion_profile(emotion)
        active_layers = get_layers_for_energy(tension_level)

        selected = {}
        stems = self._catalog.get("stems", {})

        for layer in PRO_MODE["stem_layers"]:
            if layer not in active_layers:
                selected[layer] = None
                continue

            layer_stems = stems.get(layer, [])
            best_stem = None
            best_score = -1

            for stem in layer_stems:
                score = self._score_stem_match(stem, emotion, tension_level)
                if score > best_score:
                    best_score = score
                    best_stem = stem

            if best_stem:
                selected[layer] = str(self.catalog_path.parent / best_stem["path"])
            else:
                selected[layer] = None

        return selected

    def _score_stem_match(
        self,
        stem: Dict[str, Any],
        emotion: str,
        tension_level: int
    ) -> float:
        """Score how well a stem matches the target emotion and energy."""
        score = 0.0

        # Emotion match
        if stem.get("emotion", "").lower() == emotion.lower():
            score += 0.5
        elif "neutral" in stem.get("tags", []) or "ambient" in stem.get("tags", []):
            score += 0.2

        # Energy range match
        energy_range = stem.get("energy_range", [1, 10])
        target_energy = tension_level * 2
        if energy_range[0] <= target_energy <= energy_range[1]:
            score += 0.3

        # Loop compatibility bonus for atmosphere
        if stem.get("loop_compatible"):
            score += 0.1

        return score

    def compose(
        self,
        timeline: List[EmotionSegment],
        target_duration_ms: Optional[int] = None
    ) -> str:
        """
        Compose BGM by dynamically mixing stems based on timeline.

        Args:
            timeline: List of EmotionSegment objects
            target_duration_ms: Target duration (uses timeline duration if not provided)

        Returns:
            Path to composed audio file
        """
        if not timeline:
            return ""

        if target_duration_ms is None:
            target_duration_ms = timeline[-1].end_ms

        try:
            from pydub import AudioSegment
        except ImportError:
            print("[StemComposer] pydub not available")
            return ""

        # Create base silent track at target duration
        composed = AudioSegment.silent(duration=target_duration_ms)

        # Process each segment
        for seg in timeline:
            # Select stems for this segment's emotion and tension
            stems = self.select_stems_for_emotion(seg.emotion, seg.tension_level)

            # Mix layers for this segment
            segment_audio = self._mix_layers_for_segment(
                stems,
                seg.duration_ms,
                seg.tension_level
            )

            if segment_audio:
                # Overlay on composed track at segment position
                composed = composed.overlay(segment_audio, position=seg.start_ms)

        # Apply energy envelope smoothing
        composed = self._smooth_energy_envelope(composed, timeline)

        # Export
        output_path = self.output_dir / "bgm_pro_composed.wav"
        composed.export(str(output_path), format="wav")

        return str(output_path)

    def _mix_layers_for_segment(
        self,
        stems: Dict[str, Optional[str]],
        duration_ms: int,
        tension_level: int
    ):
        """Mix stem layers for a single segment."""
        try:
            from pydub import AudioSegment
        except ImportError:
            return None

        # Start with silence
        mixed = AudioSegment.silent(duration=duration_ms)

        for layer, stem_path in stems.items():
            if not stem_path or not Path(stem_path).exists():
                continue

            try:
                stem_audio = AudioSegment.from_file(stem_path)

                # Adjust length to match segment
                if len(stem_audio) < duration_ms:
                    # Loop stem to fill duration
                    loops_needed = (duration_ms // len(stem_audio)) + 1
                    stem_audio = stem_audio * loops_needed
                stem_audio = stem_audio[:duration_ms]

                # Apply volume based on layer and tension
                volume_db = LAYER_VOLUME_CURVES.get(layer, {}).get(tension_level, 0)
                stem_audio = stem_audio + volume_db

                # Overlay on mix
                mixed = mixed.overlay(stem_audio)

            except Exception as e:
                print(f"[StemComposer] Error loading stem {stem_path}: {e}")
                continue

        return mixed

    def _smooth_energy_envelope(
        self,
        audio,
        timeline: List[EmotionSegment]
    ):
        """Apply smoothing to prevent abrupt energy changes."""
        # For now, return audio as-is
        # Full implementation would apply gain interpolation
        # between segments to create smooth transitions
        return audio

    def apply_energy_envelope(
        self,
        audio,
        timeline: List[EmotionSegment]
    ):
        """
        Apply dynamic energy envelope to audio.

        Adjusts volume throughout the track based on tension levels
        in the timeline to create natural rises and falls.

        Args:
            audio: AudioSegment to process
            timeline: Emotion timeline for energy mapping

        Returns:
            Processed AudioSegment
        """
        if not timeline:
            return audio

        try:
            from pydub import AudioSegment
        except ImportError:
            return audio

        audio_duration_ms = len(audio)
        timeline_duration_ms = timeline[-1].end_ms if timeline else audio_duration_ms

        # Scale timeline to audio duration
        scale_factor = audio_duration_ms / timeline_duration_ms if timeline_duration_ms > 0 else 1

        # Apply per-segment volume adjustments
        result = AudioSegment.empty()

        for i, seg in enumerate(timeline):
            scaled_start = int(seg.start_ms * scale_factor)
            scaled_end = int(seg.end_ms * scale_factor)

            # Extract segment from audio
            segment = audio[scaled_start:scaled_end]

            # Calculate volume adjustment
            # Tension 1 = -6dB, Tension 5 = +3dB
            volume_db = (seg.tension_level - 3) * 1.5

            # Apply adjustment
            segment = segment + volume_db

            result += segment

        return result


def compose_from_stems(
    timeline: List[EmotionSegment],
    catalog_path: Optional[Path] = None
) -> str:
    """
    Convenience function to compose BGM from stems.

    Args:
        timeline: Emotion timeline
        catalog_path: Optional path to stem catalog

    Returns:
        Path to composed audio file
    """
    composer = StemComposer(catalog_path)
    return composer.compose(timeline)


__all__ = [
    'StemComposer',
    'compose_from_stems',
]
