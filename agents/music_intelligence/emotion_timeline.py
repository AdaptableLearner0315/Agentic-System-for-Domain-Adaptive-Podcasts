"""
Emotion Timeline Extractor
Author: Sarath

Converts script emotions into time-aligned segments for music synchronization.
Detects peaks, transitions, and emotional arc for intelligent music selection.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple

from config.music_intelligence import (
    TRANSITION_CONFIG,
    get_emotion_profile,
)


@dataclass
class EmotionSegment:
    """
    Represents a time-aligned emotion segment for music synchronization.

    Attributes:
        start_ms: Start time in milliseconds
        end_ms: End time in milliseconds
        emotion: Primary emotion (wonder, tension, etc.)
        tension_level: Intensity level 1-5
        is_peak: True if this is an emotional climax
        is_transition: True if emotion changes from previous segment
        transition_type: Type of transition ("build", "release", "shift", "none")
        chunk_id: ID of the source chunk (e.g., "module_1_chunk_2")
        text_preview: First few words of the chunk text for debugging
    """
    start_ms: int
    end_ms: int
    emotion: str
    tension_level: int = 3
    is_peak: bool = False
    is_transition: bool = False
    transition_type: str = "none"
    chunk_id: str = ""
    text_preview: str = ""

    @property
    def duration_ms(self) -> int:
        """Duration of this segment in milliseconds."""
        return self.end_ms - self.start_ms

    @property
    def midpoint_ms(self) -> int:
        """Midpoint time of this segment."""
        return self.start_ms + (self.duration_ms // 2)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "start_ms": self.start_ms,
            "end_ms": self.end_ms,
            "emotion": self.emotion,
            "tension_level": self.tension_level,
            "is_peak": self.is_peak,
            "is_transition": self.is_transition,
            "transition_type": self.transition_type,
            "chunk_id": self.chunk_id,
            "text_preview": self.text_preview,
        }


class EmotionTimeline:
    """
    Extracts and manages emotion timeline from enhanced scripts.

    Provides time-aligned emotion segments with peak detection
    and transition classification for music synchronization.
    """

    # Estimated words per second for duration calculation
    WORDS_PER_SECOND = 2.5  # ~150 WPM typical narration

    def __init__(self):
        """Initialize the emotion timeline extractor."""
        self._segments: List[EmotionSegment] = []

    def extract(
        self,
        script: Dict[str, Any],
        tts_durations: Optional[Dict[str, int]] = None
    ) -> List[EmotionSegment]:
        """
        Extract emotion timeline from enhanced script.

        Args:
            script: Enhanced script with hook and modules containing chunks
            tts_durations: Optional dict mapping chunk_id -> actual duration_ms

        Returns:
            List of EmotionSegment objects representing the emotional journey
        """
        segments = []
        current_time_ms = 0

        # Process hook
        hook = script.get("hook", {})
        if hook.get("text"):
            hook_duration = self._estimate_duration(
                hook["text"],
                tts_durations.get("hook") if tts_durations else None
            )

            segments.append(EmotionSegment(
                start_ms=current_time_ms,
                end_ms=current_time_ms + hook_duration,
                emotion=hook.get("emotion", "intrigue"),
                tension_level=hook.get("tension_level", 3),
                chunk_id="hook",
                text_preview=hook["text"][:50] + "..." if len(hook["text"]) > 50 else hook["text"],
            ))
            current_time_ms += hook_duration

        # Process modules
        for module in script.get("modules", []):
            module_id = module.get("id", 0)

            for chunk_idx, chunk in enumerate(module.get("chunks", [])):
                text = chunk.get("text", "")
                if not text:
                    continue

                chunk_id = f"module_{module_id}_chunk_{chunk_idx}"
                duration = self._estimate_duration(
                    text,
                    tts_durations.get(chunk_id) if tts_durations else None
                )

                segments.append(EmotionSegment(
                    start_ms=current_time_ms,
                    end_ms=current_time_ms + duration,
                    emotion=chunk.get("emotion", "neutral"),
                    tension_level=chunk.get("tension_level", 3),
                    chunk_id=chunk_id,
                    text_preview=text[:50] + "..." if len(text) > 50 else text,
                ))
                current_time_ms += duration

        # Detect peaks and classify transitions
        segments = detect_peaks(segments)
        segments = classify_transitions(segments)

        self._segments = segments
        return segments

    def _estimate_duration(
        self,
        text: str,
        actual_duration_ms: Optional[int] = None
    ) -> int:
        """
        Estimate duration in milliseconds for text.

        Args:
            text: The text to estimate duration for
            actual_duration_ms: Optional actual duration from TTS

        Returns:
            Duration in milliseconds
        """
        if actual_duration_ms:
            return actual_duration_ms

        # Count words and estimate duration
        word_count = len(text.split())
        duration_seconds = word_count / self.WORDS_PER_SECOND
        return int(duration_seconds * 1000)

    def get_peaks(self) -> List[EmotionSegment]:
        """Get all peak segments."""
        return [seg for seg in self._segments if seg.is_peak]

    def get_transitions(self) -> List[EmotionSegment]:
        """Get all segments marked as transitions."""
        return [seg for seg in self._segments if seg.is_transition]

    def get_total_duration_ms(self) -> int:
        """Get total timeline duration in milliseconds."""
        if not self._segments:
            return 0
        return self._segments[-1].end_ms

    def get_dominant_emotions(self, count: int = 3) -> List[str]:
        """
        Get the most common emotions in the timeline.

        Args:
            count: Number of top emotions to return

        Returns:
            List of emotion names sorted by frequency
        """
        emotion_counts: Dict[str, int] = {}
        for seg in self._segments:
            duration = seg.duration_ms
            emotion_counts[seg.emotion] = emotion_counts.get(seg.emotion, 0) + duration

        sorted_emotions = sorted(
            emotion_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return [emotion for emotion, _ in sorted_emotions[:count]]

    def get_segment_at_time(self, time_ms: int) -> Optional[EmotionSegment]:
        """
        Get the segment at a specific time.

        Args:
            time_ms: Time in milliseconds

        Returns:
            EmotionSegment at that time or None
        """
        for seg in self._segments:
            if seg.start_ms <= time_ms < seg.end_ms:
                return seg
        return None

    def get_emotion_zones(self, count: int = 3) -> List[Tuple[int, int, str]]:
        """
        Divide timeline into emotion zones for track selection.

        Args:
            count: Number of zones to create

        Returns:
            List of (start_ms, end_ms, dominant_emotion) tuples
        """
        if not self._segments:
            return []

        total_duration = self.get_total_duration_ms()
        zone_duration = total_duration // count
        zones = []

        for i in range(count):
            zone_start = i * zone_duration
            zone_end = (i + 1) * zone_duration if i < count - 1 else total_duration

            # Find dominant emotion in this zone
            zone_emotions: Dict[str, int] = {}
            for seg in self._segments:
                # Calculate overlap with zone
                overlap_start = max(zone_start, seg.start_ms)
                overlap_end = min(zone_end, seg.end_ms)
                if overlap_end > overlap_start:
                    overlap_duration = overlap_end - overlap_start
                    zone_emotions[seg.emotion] = zone_emotions.get(seg.emotion, 0) + overlap_duration

            dominant = max(zone_emotions.items(), key=lambda x: x[1])[0] if zone_emotions else "neutral"
            zones.append((zone_start, zone_end, dominant))

        return zones


def extract_timeline(
    script: Dict[str, Any],
    tts_durations: Optional[Dict[str, int]] = None
) -> List[EmotionSegment]:
    """
    Convenience function to extract emotion timeline from script.

    Args:
        script: Enhanced script dictionary
        tts_durations: Optional mapping of chunk_id to actual TTS duration

    Returns:
        List of EmotionSegment objects
    """
    extractor = EmotionTimeline()
    return extractor.extract(script, tts_durations)


def detect_peaks(segments: List[EmotionSegment]) -> List[EmotionSegment]:
    """
    Detect emotional peaks in the timeline.

    Peaks are identified by:
    - Tension level of 5
    - Local maxima in tension (higher than neighbors)
    - High-energy emotions (triumph, excitement, explosive_energy)

    Args:
        segments: List of EmotionSegment objects

    Returns:
        Updated list with is_peak flags set
    """
    high_energy_emotions = {
        "triumph", "excitement", "explosive_energy",
        "liberation", "rebellion"
    }

    for i, seg in enumerate(segments):
        # Check for max tension
        if seg.tension_level >= 5:
            seg.is_peak = True
            continue

        # Check for high-energy emotions
        if seg.emotion.lower() in high_energy_emotions and seg.tension_level >= 4:
            seg.is_peak = True
            continue

        # Check for local maximum in tension
        prev_tension = segments[i - 1].tension_level if i > 0 else 0
        next_tension = segments[i + 1].tension_level if i < len(segments) - 1 else 0

        if seg.tension_level > prev_tension and seg.tension_level > next_tension:
            if seg.tension_level >= 4:  # Only mark as peak if tension is significant
                seg.is_peak = True

    return segments


def classify_transitions(segments: List[EmotionSegment]) -> List[EmotionSegment]:
    """
    Classify transitions between segments.

    Transition types:
    - "build": Tension increasing toward a peak
    - "release": Tension decreasing after a peak
    - "shift": Emotion change at similar energy level
    - "none": No significant transition

    Args:
        segments: List of EmotionSegment objects

    Returns:
        Updated list with transition classifications
    """
    for i, seg in enumerate(segments):
        if i == 0:
            seg.is_transition = False
            seg.transition_type = "none"
            continue

        prev = segments[i - 1]

        # Check for emotion change
        emotion_changed = seg.emotion.lower() != prev.emotion.lower()

        # Check for tension change
        tension_delta = seg.tension_level - prev.tension_level

        if emotion_changed or abs(tension_delta) >= 2:
            seg.is_transition = True

            if seg.is_peak:
                seg.transition_type = "build"
            elif prev.is_peak:
                seg.transition_type = "release"
            elif tension_delta > 0:
                seg.transition_type = "build"
            elif tension_delta < 0:
                seg.transition_type = "release"
            else:
                seg.transition_type = "shift"
        else:
            seg.is_transition = False
            seg.transition_type = "none"

    return segments


def get_transition_points(
    segments: List[EmotionSegment],
    min_gap_ms: int = None
) -> List[int]:
    """
    Get optimal times for music transitions.

    Args:
        segments: List of EmotionSegment objects
        min_gap_ms: Minimum gap between transitions

    Returns:
        List of times (in ms) where transitions should occur
    """
    if min_gap_ms is None:
        min_gap_ms = TRANSITION_CONFIG["min_segment_duration_ms"]

    transition_times = []
    last_transition_time = 0

    for seg in segments:
        if seg.is_transition:
            # Apply anticipatory offset
            transition_time = max(0, seg.start_ms - TRANSITION_CONFIG["anticipatory_lead_ms"])

            # Ensure minimum gap between transitions
            if transition_time - last_transition_time >= min_gap_ms:
                transition_times.append(transition_time)
                last_transition_time = transition_time

    return transition_times


__all__ = [
    'EmotionSegment',
    'EmotionTimeline',
    'extract_timeline',
    'detect_peaks',
    'classify_transitions',
    'get_transition_points',
]
