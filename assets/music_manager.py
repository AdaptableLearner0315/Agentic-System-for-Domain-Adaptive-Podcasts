"""
Music Asset Manager
Author: Sarath

Manages pre-generated music stems for fast BGM assembly.
Uses stem library for Normal mode to avoid generation time.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
import json
import random


class MusicAssetManager:
    """
    Manages pre-generated music stems for fast BGM assembly.

    Features:
    - Categorized stem library (intro, main, outro)
    - Mood-based selection
    - Real-time mixing of stems
    - Fallback generation for missing stems
    """

    # Stem categories and variations
    STEM_CATEGORIES = {
        "intro": {
            "moods": ["mysterious", "uplifting", "dramatic", "calm", "energetic"],
            "duration": 30,  # seconds
        },
        "main": {
            "moods": ["ambient", "cinematic", "electronic", "acoustic", "minimal"],
            "duration": 45,
        },
        "outro": {
            "moods": ["reflective", "triumphant", "peaceful", "hopeful", "conclusive"],
            "duration": 30,
        },
    }

    # Mood mappings from emotions
    EMOTION_TO_MOOD = {
        "intrigue": "mysterious",
        "wonder": "uplifting",
        "curiosity": "mysterious",
        "triumph": "triumphant",
        "tension": "dramatic",
        "excitement": "energetic",
        "reflection": "reflective",
        "nostalgia": "peaceful",
        "joy": "uplifting",
        "awe": "cinematic",
        "urgency": "energetic",
        "calm": "calm",
        "hope": "hopeful",
        "neutral": "ambient",
    }

    def __init__(self, asset_dir: Optional[Path] = None):
        """
        Initialize the Music Asset Manager.

        Args:
            asset_dir: Directory for music stems
        """
        if asset_dir:
            self.asset_dir = Path(asset_dir)
        else:
            self.asset_dir = Path(__file__).parent / "music"

        self.asset_dir.mkdir(parents=True, exist_ok=True)

        # Catalog of available stems
        self._stem_catalog: Dict[str, Dict[str, str]] = {}
        self._load_catalog()

    def _load_catalog(self):
        """Load stem catalog from disk."""
        catalog_file = self.asset_dir / "catalog.json"
        if catalog_file.exists():
            try:
                with open(catalog_file, 'r') as f:
                    self._stem_catalog = json.load(f)
            except Exception:
                self._stem_catalog = {}

    def _save_catalog(self):
        """Save stem catalog to disk."""
        catalog_file = self.asset_dir / "catalog.json"
        with open(catalog_file, 'w') as f:
            json.dump(self._stem_catalog, f, indent=2)

    def get_stem_path(self, category: str, mood: str) -> Optional[str]:
        """
        Get pre-generated stem for category and mood.

        Args:
            category: Stem category (intro, main, outro)
            mood: Mood variation

        Returns:
            Path to audio file or None
        """
        key = f"{category}_{mood}"
        path = self._stem_catalog.get(key)
        if path and Path(path).exists():
            return path
        return None

    def has_stems(self, min_coverage: float = 0.5) -> bool:
        """
        Check if sufficient pre-generated stems are available.

        Args:
            min_coverage: Minimum fraction of stem categories that must have
                at least one stem (default 0.5 = at least 2 of 3 categories)

        Returns:
            True if enough stems are available for fast generation
        """
        categories_with_stems = 0
        for category in self.STEM_CATEGORIES:
            for mood in self.STEM_CATEGORIES[category]["moods"]:
                if self.get_stem_path(category, mood):
                    categories_with_stems += 1
                    break  # Only need one stem per category

        return categories_with_stems >= len(self.STEM_CATEGORIES) * min_coverage

    def get_available_stem_count(self) -> int:
        """Return the number of stems currently in the catalog."""
        count = 0
        for key, path in self._stem_catalog.items():
            if Path(path).exists():
                count += 1
        return count

    def add_to_catalog(self, category: str, mood: str, audio_path: str):
        """
        Add a generated stem to the catalog.

        Args:
            category: Stem category
            mood: Mood variation
            audio_path: Path to generated audio
        """
        key = f"{category}_{mood}"
        self._stem_catalog[key] = str(audio_path)
        self._save_catalog()

    def select_best_stem(
        self,
        category: str,
        emotion: str
    ) -> Optional[str]:
        """
        Select the best stem for a given emotion.

        Args:
            category: Stem category
            emotion: Emotion from script

        Returns:
            Path to selected stem or None
        """
        # Map emotion to mood
        mood = self.EMOTION_TO_MOOD.get(emotion.lower(), "ambient")

        # Try exact match
        path = self.get_stem_path(category, mood)
        if path:
            return path

        # Try fallback moods
        fallback_moods = self.STEM_CATEGORIES.get(category, {}).get("moods", [])
        for fallback in fallback_moods:
            path = self.get_stem_path(category, fallback)
            if path:
                return path

        return None

    def select_stems_for_emotions(
        self,
        emotions: List[str]
    ) -> Dict[str, Optional[str]]:
        """
        Select intro, main, and outro stems based on emotion timeline.

        Args:
            emotions: List of emotions throughout the content

        Returns:
            Dictionary with 'intro', 'main', 'outro' paths
        """
        # Use first emotion for intro
        intro_emotion = emotions[0] if emotions else "intrigue"

        # Use middle emotion for main
        mid_idx = len(emotions) // 2
        main_emotion = emotions[mid_idx] if emotions else "neutral"

        # Use last emotion for outro
        outro_emotion = emotions[-1] if emotions else "reflection"

        return {
            "intro": self.select_best_stem("intro", intro_emotion),
            "main": self.select_best_stem("main", main_emotion),
            "outro": self.select_best_stem("outro", outro_emotion),
        }

    def mix_stems(
        self,
        stems: Dict[str, str],
        output_path: str
    ) -> str:
        """
        Mix intro, main, and outro stems into single BGM track.

        Args:
            stems: Dictionary of stem paths
            output_path: Output file path

        Returns:
            Path to mixed audio
        """
        try:
            from pydub import AudioSegment

            segments = []

            # Load intro
            if stems.get("intro") and Path(stems["intro"]).exists():
                intro = AudioSegment.from_file(stems["intro"])
                segments.append(intro)

            # Load main (loop if needed)
            if stems.get("main") and Path(stems["main"]).exists():
                main = AudioSegment.from_file(stems["main"])
                # Loop main to desired length
                segments.append(main)

            # Load outro
            if stems.get("outro") and Path(stems["outro"]).exists():
                outro = AudioSegment.from_file(stems["outro"])
                segments.append(outro)

            if not segments:
                return None

            # Concatenate with crossfades
            combined = segments[0]
            for seg in segments[1:]:
                combined = combined.append(seg, crossfade=500)

            # Export
            combined.export(output_path, format="wav")
            return output_path

        except Exception as e:
            print(f"[MusicAssetManager] Error mixing stems: {e}")
            return None

    def generate_3segment_bgm(
        self,
        emotions: List[str],
        bgm_func,
        output_dir: Path
    ) -> List[Dict[str, Any]]:
        """
        Generate 3-segment BGM using stems or generation.

        Args:
            emotions: Emotion timeline
            bgm_func: BGM generation function
            output_dir: Output directory

        Returns:
            List of BGM segment metadata
        """
        # Try to use pre-generated stems first
        stems = self.select_stems_for_emotions(emotions)

        segments = []
        for i, (category, path) in enumerate(stems.items(), 1):
            if path:
                print(f"  Using pre-generated stem: {category}")
                segments.append({
                    "segment_id": i,
                    "name": category.title(),
                    "path": path,
                    "from_library": True
                })
            else:
                # Generate new segment
                print(f"  Generating new segment: {category}")
                emotion = emotions[i-1] if i-1 < len(emotions) else "neutral"
                filename = f"segment_{i}_{category}"
                duration = self.STEM_CATEGORIES[category]["duration"]

                path = bgm_func(emotion, filename, duration)
                if path:
                    segments.append({
                        "segment_id": i,
                        "name": category.title(),
                        "path": path,
                        "from_library": False
                    })
                    # Add to catalog for future use
                    mood = self.EMOTION_TO_MOOD.get(emotion.lower(), "ambient")
                    self.add_to_catalog(category, mood, path)

        return segments

    def pregenerate_stems(self, bgm_func):
        """
        Pre-generate all stem variations.

        Args:
            bgm_func: BGM generation function (emotion, filename, duration) -> path
        """
        print("[MusicAssetManager] Pre-generating music stems...")

        for category, config in self.STEM_CATEGORIES.items():
            for mood in config["moods"]:
                if self.get_stem_path(category, mood):
                    print(f"  Skipping (cached): {category}_{mood}")
                    continue

                filename = f"{category}_{mood}"
                duration = config["duration"]

                print(f"  Generating: {filename}")
                path = bgm_func(mood, filename, duration)

                if path:
                    self.add_to_catalog(category, mood, path)

        print(f"[MusicAssetManager] Stem library ready: {len(self._stem_catalog)} stems")


__all__ = ['MusicAssetManager']
