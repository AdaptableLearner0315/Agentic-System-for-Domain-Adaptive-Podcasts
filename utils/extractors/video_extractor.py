"""
Video Extractor
Author: Sarath

Extracts text content from video files by extracting audio
and transcribing with Whisper.
"""

from pathlib import Path
from typing import Optional
import tempfile
import os


class VideoExtractor:
    """Extracts content from video files via audio extraction + transcription."""

    def __init__(self, model_size: str = "base"):
        """
        Initialize Video extractor.

        Args:
            model_size: Whisper model size for transcription
        """
        self.model_size = model_size
        self._moviepy = None

    def _load_moviepy(self):
        """Lazy-load moviepy."""
        if self._moviepy is None:
            try:
                import moviepy.editor as mpy
                self._moviepy = mpy
            except ImportError:
                raise ImportError("moviepy is required for video extraction. Install with: pip install moviepy")

    def extract(self, file_path: str) -> 'ExtractedContent':
        """
        Extract text content from a video file.

        Args:
            file_path: Path to the video file

        Returns:
            ExtractedContent object
        """
        from utils.input_router import ExtractedContent
        from utils.extractors.audio_extractor import AudioExtractor

        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Load moviepy
        self._load_moviepy()

        # Extract audio to temporary file
        print(f"[VideoExtractor] Extracting audio from {path.name}...")

        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_audio:
            tmp_audio_path = tmp_audio.name

        try:
            # Extract audio using moviepy
            video = self._moviepy.VideoFileClip(str(path))
            video_duration = video.duration
            video.audio.write_audiofile(tmp_audio_path, verbose=False, logger=None)
            video.close()

            # Transcribe audio
            audio_extractor = AudioExtractor(model_size=self.model_size)
            audio_content = audio_extractor.extract(tmp_audio_path)

            return ExtractedContent(
                text=audio_content.text,
                source_type='video',
                source_path=str(path),
                title=path.stem.replace('_', ' ').title(),
                metadata={
                    'duration_seconds': video_duration,
                    'language': audio_content.metadata.get('language', 'en'),
                    'word_count': len(audio_content.text.split()),
                    'model_size': self.model_size,
                }
            )
        finally:
            # Clean up temporary file
            if os.path.exists(tmp_audio_path):
                os.remove(tmp_audio_path)
