"""
Music Selector (Normal Mode)
Author: Sarath

Selects best-matching pre-composed tracks from the library based on emotion timeline.
Ensures harmonic compatibility and smooth transitions between tracks.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any, Optional

from config.music_intelligence import (
    NORMAL_MODE,
    get_emotion_profile,
    is_harmonic_compatible,
)
from .emotion_timeline import EmotionSegment


@dataclass
class TrackSelection:
    """
    Represents a selected track for a portion of the timeline.

    Attributes:
        track_path: Path to the audio file
        track_id: Unique track identifier
        emotion_match: The emotion this track matches
        energy_level: Energy level of the track (1-10)
        start_ms: When to start this track in the final mix
        end_ms: When to end this track
        crossfade_in_ms: Crossfade duration from previous track
        crossfade_out_ms: Crossfade duration to next track
        key: Musical key (e.g., "C_major")
        tempo_bpm: Tempo in beats per minute
    """
    track_path: str
    track_id: str
    emotion_match: str
    energy_level: int
    start_ms: int
    end_ms: int
    crossfade_in_ms: int = 3000
    crossfade_out_ms: int = 3000
    key: str = "C_major"
    tempo_bpm: int = 90

    @property
    def duration_ms(self) -> int:
        """Duration of this track selection."""
        return self.end_ms - self.start_ms

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "track_path": self.track_path,
            "track_id": self.track_id,
            "emotion_match": self.emotion_match,
            "energy_level": self.energy_level,
            "start_ms": self.start_ms,
            "end_ms": self.end_ms,
            "crossfade_in_ms": self.crossfade_in_ms,
            "crossfade_out_ms": self.crossfade_out_ms,
            "key": self.key,
            "tempo_bpm": self.tempo_bpm,
        }


class MusicSelector:
    """
    Selects pre-composed tracks from library based on emotion timeline.

    Used in Normal mode for fast (~500ms) music selection.
    """

    def __init__(self, catalog_path: Optional[Path] = None):
        """
        Initialize the music selector.

        Args:
            catalog_path: Path to track catalog JSON file
        """
        if catalog_path:
            self.catalog_path = Path(catalog_path)
        else:
            self.catalog_path = Path(__file__).parent.parent.parent / "assets" / "music" / "tracks" / "catalog.json"

        self._catalog: Dict[str, Any] = {}
        self._load_catalog()

    def _load_catalog(self):
        """Load track catalog from disk."""
        if self.catalog_path.exists():
            try:
                with open(self.catalog_path, 'r') as f:
                    self._catalog = json.load(f)
            except Exception as e:
                print(f"[MusicSelector] Error loading catalog: {e}")
                self._catalog = {"tracks": []}
        else:
            self._catalog = {"tracks": []}

    def get_tracks_for_emotion(self, emotion: str) -> List[Dict[str, Any]]:
        """
        Get all tracks matching an emotion.

        Args:
            emotion: Emotion to match

        Returns:
            List of track metadata dictionaries
        """
        matches = []
        for track in self._catalog.get("tracks", []):
            if track.get("emotion", "").lower() == emotion.lower():
                matches.append(track)
        return matches

    def score_track_match(
        self,
        track_meta: Dict[str, Any],
        emotion: str,
        tension_level: int
    ) -> float:
        """
        Score how well a track matches the desired emotion and energy.

        Args:
            track_meta: Track metadata from catalog
            emotion: Target emotion
            tension_level: Target tension level (1-5)

        Returns:
            Match score (0.0 - 1.0)
        """
        score = 0.0

        # Emotion match (50% weight)
        if track_meta.get("emotion", "").lower() == emotion.lower():
            score += 0.5
        elif emotion.lower() in track_meta.get("tags", []):
            score += 0.25

        # Energy match (30% weight)
        track_energy = track_meta.get("energy", 5)
        target_energy = tension_level * 2  # Map 1-5 to 2-10
        energy_diff = abs(track_energy - target_energy)
        energy_score = max(0, 1 - (energy_diff / 10))
        score += energy_score * 0.3

        # Texture match (20% weight)
        profile = get_emotion_profile(emotion)
        track_texture = track_meta.get("texture", "")
        if track_texture == profile.get("texture"):
            score += 0.2
        elif track_texture in ["balanced", "neutral"]:
            score += 0.1

        return min(1.0, score)

    def select_tracks(
        self,
        timeline: List[EmotionSegment],
        max_tracks: int = None
    ) -> List[TrackSelection]:
        """
        Select best-matching tracks for the emotion timeline.

        Strategy:
        1. Divide timeline into zones based on max_tracks
        2. Identify dominant emotion per zone
        3. Select best-matching track for each zone
        4. Ensure harmonic compatibility between adjacent tracks

        Args:
            timeline: List of EmotionSegment objects
            max_tracks: Maximum number of tracks to select

        Returns:
            List of TrackSelection objects
        """
        if max_tracks is None:
            max_tracks = NORMAL_MODE["max_tracks"]

        if not timeline:
            return []

        # Group segments into zones
        zones = self._create_zones(timeline, max_tracks)

        selections = []
        prev_selection = None

        for zone_start, zone_end, dominant_emotion, avg_tension in zones:
            # Find best matching track
            candidates = self._catalog.get("tracks", [])
            if not candidates:
                # No tracks available, create placeholder
                selections.append(self._create_placeholder_selection(
                    zone_start, zone_end, dominant_emotion, avg_tension
                ))
                continue

            best_track = None
            best_score = -1

            for track in candidates:
                score = self.score_track_match(track, dominant_emotion, avg_tension)

                # Bonus for harmonic compatibility with previous track
                if prev_selection:
                    if is_harmonic_compatible(prev_selection.key, track.get("key", "C_major")):
                        score += 0.1

                if score > best_score:
                    best_score = score
                    best_track = track

            if best_track:
                selection = TrackSelection(
                    track_path=str(self.catalog_path.parent / best_track["path"]),
                    track_id=best_track["id"],
                    emotion_match=dominant_emotion,
                    energy_level=best_track.get("energy", 5),
                    start_ms=zone_start,
                    end_ms=zone_end,
                    crossfade_in_ms=NORMAL_MODE["crossfade_ms"],
                    crossfade_out_ms=NORMAL_MODE["crossfade_ms"],
                    key=best_track.get("key", "C_major"),
                    tempo_bpm=best_track.get("tempo_bpm", 90),
                )
                selections.append(selection)
                prev_selection = selection
            else:
                selections.append(self._create_placeholder_selection(
                    zone_start, zone_end, dominant_emotion, avg_tension
                ))

        return selections

    def _create_zones(
        self,
        timeline: List[EmotionSegment],
        num_zones: int
    ) -> List[tuple]:
        """
        Divide timeline into zones for track selection.

        Args:
            timeline: List of segments
            num_zones: Number of zones to create

        Returns:
            List of (start_ms, end_ms, dominant_emotion, avg_tension) tuples
        """
        total_duration = timeline[-1].end_ms if timeline else 0
        zone_duration = total_duration // num_zones

        zones = []
        for i in range(num_zones):
            zone_start = i * zone_duration
            zone_end = (i + 1) * zone_duration if i < num_zones - 1 else total_duration

            # Find dominant emotion and average tension in zone
            emotion_weights: Dict[str, int] = {}
            tension_sum = 0
            tension_count = 0

            for seg in timeline:
                overlap_start = max(zone_start, seg.start_ms)
                overlap_end = min(zone_end, seg.end_ms)
                if overlap_end > overlap_start:
                    overlap_duration = overlap_end - overlap_start
                    emotion_weights[seg.emotion] = emotion_weights.get(seg.emotion, 0) + overlap_duration
                    tension_sum += seg.tension_level * overlap_duration
                    tension_count += overlap_duration

            dominant_emotion = max(emotion_weights.items(), key=lambda x: x[1])[0] if emotion_weights else "neutral"
            avg_tension = round(tension_sum / tension_count) if tension_count > 0 else 3

            zones.append((zone_start, zone_end, dominant_emotion, avg_tension))

        return zones

    def _create_placeholder_selection(
        self,
        start_ms: int,
        end_ms: int,
        emotion: str,
        tension: int
    ) -> TrackSelection:
        """Create a placeholder selection when no tracks are available."""
        return TrackSelection(
            track_path="",
            track_id="placeholder",
            emotion_match=emotion,
            energy_level=tension * 2,
            start_ms=start_ms,
            end_ms=end_ms,
            crossfade_in_ms=NORMAL_MODE["crossfade_ms"],
            crossfade_out_ms=NORMAL_MODE["crossfade_ms"],
        )

    def check_harmonic_compatibility(
        self,
        track1: Dict[str, Any],
        track2: Dict[str, Any]
    ) -> bool:
        """
        Check if two tracks are harmonically compatible.

        Args:
            track1: First track metadata
            track2: Second track metadata

        Returns:
            True if tracks can transition smoothly
        """
        key1 = track1.get("key", "C_major")
        key2 = track2.get("key", "C_major")
        return is_harmonic_compatible(key1, key2)


def select_tracks(
    timeline: List[EmotionSegment],
    catalog_path: Optional[Path] = None
) -> List[TrackSelection]:
    """
    Convenience function to select tracks for a timeline.

    Args:
        timeline: List of EmotionSegment objects
        catalog_path: Optional path to track catalog

    Returns:
        List of TrackSelection objects
    """
    selector = MusicSelector(catalog_path)
    return selector.select_tracks(timeline)


__all__ = [
    'TrackSelection',
    'MusicSelector',
    'select_tracks',
]
