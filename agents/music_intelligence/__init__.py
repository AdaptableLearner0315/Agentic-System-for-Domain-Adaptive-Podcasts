"""
Music Intelligence System
Author: Sarath

Emotionally intelligent music system that tracks script emotions,
selects/composes appropriate music, and creates seamless transitions.

Normal Mode: Fast pre-composed track selection (~500ms)
Pro Mode: Dynamic stem composition with anticipatory transitions (~2s)
"""

from .emotion_timeline import (
    EmotionSegment,
    EmotionTimeline,
    extract_timeline,
    detect_peaks,
    classify_transitions,
)
from .music_selector import (
    TrackSelection,
    MusicSelector,
)
from .stem_composer import (
    StemComposer,
)
from .transition_engine import (
    TransitionEngine,
    apply_crossfade,
)
from .accent_placer import (
    AccentPoint,
    AccentPlacer,
)


class MusicIntelligence:
    """
    Main interface for the Music Intelligence System.

    Provides unified API for both Normal and Pro modes.

    Usage:
        mi = MusicIntelligence(mode="normal")
        timeline = mi.extract_emotion_timeline(script)
        bgm_path = mi.compose(timeline, tts_durations)
    """

    def __init__(self, mode: str = "normal"):
        """
        Initialize Music Intelligence System.

        Args:
            mode: "normal" for fast track selection, "pro" for dynamic composition
        """
        self.mode = mode
        self.timeline_extractor = EmotionTimeline()
        self.selector = MusicSelector()
        self.composer = StemComposer()
        self.transition_engine = TransitionEngine()
        self.accent_placer = AccentPlacer()

    def extract_emotion_timeline(
        self,
        script: dict,
        tts_durations: dict = None
    ) -> list:
        """
        Extract emotion timeline from enhanced script.

        Args:
            script: Enhanced script with emotions per chunk
            tts_durations: Optional dict of chunk_id -> duration_ms for precise timing

        Returns:
            List of EmotionSegment objects
        """
        return self.timeline_extractor.extract(script, tts_durations)

    def compose_for_normal(
        self,
        timeline: list,
        target_duration_ms: int = None
    ) -> str:
        """
        Compose BGM for Normal mode using pre-composed tracks.

        Fast (~500ms) track selection and crossfade assembly.

        Args:
            timeline: List of EmotionSegment from extract_emotion_timeline
            target_duration_ms: Target duration (estimated from script if not provided)

        Returns:
            Path to assembled BGM file
        """
        # Select best-matching tracks
        track_selections = self.selector.select_tracks(timeline)

        # Apply transitions
        bgm_path = self.transition_engine.assemble_tracks(
            track_selections,
            timeline,
            mode="normal"
        )

        # Place basic accents at peaks
        peaks = [seg for seg in timeline if seg.is_peak]
        if peaks:
            bgm_path = self.accent_placer.place_accents(
                bgm_path,
                timeline,
                density="low"
            )

        return bgm_path

    def compose_for_pro(
        self,
        timeline: list,
        target_duration_ms: int = None
    ) -> str:
        """
        Compose BGM for Pro mode using dynamic stem composition.

        High-quality (~2s) multi-layer composition with anticipatory transitions.

        Args:
            timeline: List of EmotionSegment from extract_emotion_timeline
            target_duration_ms: Target duration (estimated from script if not provided)

        Returns:
            Path to composed BGM file
        """
        # Compose from stems with energy envelope
        composed = self.composer.compose(timeline)

        # Apply anticipatory transitions
        bgm_path = self.transition_engine.apply_anticipatory_transitions(
            composed,
            timeline
        )

        # Place full accent suite
        bgm_path = self.accent_placer.place_accents(
            bgm_path,
            timeline,
            density="high"
        )

        return bgm_path

    def compose(
        self,
        timeline: list,
        target_duration_ms: int = None
    ) -> str:
        """
        Compose BGM using the configured mode.

        Args:
            timeline: List of EmotionSegment from extract_emotion_timeline
            target_duration_ms: Target duration

        Returns:
            Path to final BGM file
        """
        if self.mode == "pro":
            return self.compose_for_pro(timeline, target_duration_ms)
        return self.compose_for_normal(timeline, target_duration_ms)


__all__ = [
    'MusicIntelligence',
    'EmotionSegment',
    'EmotionTimeline',
    'TrackSelection',
    'MusicSelector',
    'StemComposer',
    'TransitionEngine',
    'AccentPoint',
    'AccentPlacer',
    'extract_timeline',
    'detect_peaks',
    'classify_transitions',
    'apply_crossfade',
]
