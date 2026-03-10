"""
Voice Asset Manager
Author: Sarath

Manages pre-generated voice assets for fast TTS generation.
Uses a phrase library for common expressions and blends with
generated content for unique segments.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
import json
import hashlib


class VoiceAssetManager:
    """
    Manages pre-generated voice segments for fast TTS.

    Features:
    - Phrase library for common expressions
    - Transition word bank
    - Emotional tone templates
    - Cache for recently generated segments
    """

    # Common phrases that can be pre-generated
    COMMON_PHRASES = {
        # Openers
        "welcome": [
            "Welcome to the podcast.",
            "Welcome back.",
            "Thank you for joining us.",
            "Thanks for tuning in.",
        ],
        # Transitions
        "transitions": [
            "However",
            "Meanwhile",
            "Interestingly",
            "On the other hand",
            "But here's the thing",
            "And that's not all",
            "What happened next changed everything",
            "This is where it gets interesting",
        ],
        # Closers
        "closers": [
            "Thank you for listening.",
            "Until next time.",
            "Stay curious.",
            "Keep exploring.",
        ],
        # Emotional interjections
        "emotions": [
            "Incredible.",
            "Unbelievable.",
            "Remarkable.",
            "Fascinating.",
            "Amazing.",
        ],
    }

    def __init__(self, asset_dir: Optional[Path] = None):
        """
        Initialize the Voice Asset Manager.

        Args:
            asset_dir: Directory for voice assets
        """
        if asset_dir:
            self.asset_dir = Path(asset_dir)
        else:
            self.asset_dir = Path(__file__).parent / "voice"

        self.asset_dir.mkdir(parents=True, exist_ok=True)

        # Cache for phrase audio files
        self._phrase_cache: Dict[str, str] = {}
        self._load_cache()

    def _load_cache(self):
        """Load phrase cache from disk."""
        cache_file = self.asset_dir / "cache.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    self._phrase_cache = json.load(f)
            except Exception:
                self._phrase_cache = {}

    def _save_cache(self):
        """Save phrase cache to disk."""
        cache_file = self.asset_dir / "cache.json"
        with open(cache_file, 'w') as f:
            json.dump(self._phrase_cache, f, indent=2)

    def _hash_text(self, text: str) -> str:
        """Generate hash for text content."""
        return hashlib.md5(text.lower().strip().encode()).hexdigest()[:12]

    def get_phrase_path(self, text: str) -> Optional[str]:
        """
        Get pre-generated audio for a phrase if available.

        Args:
            text: Text to look up

        Returns:
            Path to audio file or None if not available
        """
        text_hash = self._hash_text(text)
        path = self._phrase_cache.get(text_hash)
        if path and Path(path).exists():
            return path
        return None

    def add_to_cache(self, text: str, audio_path: str):
        """
        Add a generated phrase to the cache.

        Args:
            text: Original text
            audio_path: Path to generated audio
        """
        text_hash = self._hash_text(text)
        self._phrase_cache[text_hash] = str(audio_path)
        self._save_cache()

    def segment_text_for_optimization(
        self,
        full_text: str
    ) -> List[Dict[str, Any]]:
        """
        Segment text into reusable phrases and unique content.

        This identifies parts of the text that match common phrases
        and can potentially use cached audio.

        Args:
            full_text: Full text to segment

        Returns:
            List of segments with 'text', 'is_common', 'cache_path'
        """
        segments = []
        remaining = full_text

        # For now, return as single segment
        # Future: implement phrase matching
        segments.append({
            'text': remaining,
            'is_common': False,
            'cache_path': self.get_phrase_path(remaining),
        })

        return segments

    def generate_with_assets(
        self,
        text: str,
        tts_func,
        output_filename: str
    ) -> Optional[str]:
        """
        Generate TTS using assets where possible.

        Args:
            text: Text to convert
            tts_func: TTS generation function
            output_filename: Output filename

        Returns:
            Path to audio file
        """
        # Check cache first
        cached_path = self.get_phrase_path(text)
        if cached_path:
            print(f"    Using cached audio for: {text[:50]}...")
            return cached_path

        # Generate new audio
        path = tts_func(text, output_filename)

        # Cache for future use
        if path:
            self.add_to_cache(text, path)

        return path

    def pregenerate_common_phrases(self, tts_func):
        """
        Pre-generate audio for common phrases.

        Args:
            tts_func: TTS generation function (text, filename) -> path
        """
        print("[VoiceAssetManager] Pre-generating common phrases...")

        for category, phrases in self.COMMON_PHRASES.items():
            for i, phrase in enumerate(phrases):
                if self.get_phrase_path(phrase):
                    print(f"  Skipping (cached): {phrase}")
                    continue

                filename = f"{category}_{i+1}"
                print(f"  Generating: {phrase}")
                path = tts_func(phrase, filename)

                if path:
                    self.add_to_cache(phrase, path)

        print(f"[VoiceAssetManager] Phrase library ready: {len(self._phrase_cache)} phrases")


__all__ = ['VoiceAssetManager']
