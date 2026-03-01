"""
Audio Extractor
Author: Sarath

Extracts text content from audio files using Whisper transcription.
"""

from pathlib import Path
from typing import Optional
import os


class AudioExtractor:
    """Extracts content from audio files via transcription."""

    def __init__(self, model_size: str = "base"):
        """
        Initialize Audio extractor.

        Args:
            model_size: Whisper model size (tiny, base, small, medium, large)
        """
        self.model_size = model_size
        self._whisper = None
        self._model = None

    def _load_whisper(self):
        """Lazy-load Whisper model."""
        if self._whisper is None:
            try:
                import whisper
                self._whisper = whisper
                self._model = whisper.load_model(self.model_size)
            except ImportError:
                raise ImportError("openai-whisper is required for audio transcription. Install with: pip install openai-whisper")

    def extract(self, file_path: str) -> 'ExtractedContent':
        """
        Extract text content from an audio file via transcription.

        Args:
            file_path: Path to the audio file

        Returns:
            ExtractedContent object
        """
        from utils.input_router import ExtractedContent

        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Load Whisper model
        self._load_whisper()

        # Transcribe audio
        print(f"[AudioExtractor] Transcribing {path.name}...")
        result = self._model.transcribe(str(path))

        text = result.get('text', '').strip()
        language = result.get('language', 'en')

        # Get audio duration using pydub if available
        duration = self._get_duration(path)

        return ExtractedContent(
            text=text,
            source_type='audio',
            source_path=str(path),
            title=path.stem.replace('_', ' ').title(),
            metadata={
                'language': language,
                'duration_seconds': duration,
                'word_count': len(text.split()),
                'model_size': self.model_size,
            }
        )

    def _get_duration(self, path: Path) -> Optional[float]:
        """Get audio duration in seconds."""
        try:
            from pydub import AudioSegment
            audio = AudioSegment.from_file(str(path))
            return len(audio) / 1000.0
        except Exception:
            return None
