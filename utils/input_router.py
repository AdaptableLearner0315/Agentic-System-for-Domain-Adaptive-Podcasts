"""
Input Router
Author: Sarath

Routes different input formats (PDF, Word, audio, video, URL, text)
to appropriate extractors for content extraction.
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class ExtractedContent:
    """Extracted content from any input format."""
    text: str
    source_type: str
    source_path: str
    title: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    user_prompt: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'text': self.text,
            'source_type': self.source_type,
            'source_path': self.source_path,
            'title': self.title,
            'metadata': self.metadata or {},
            'user_prompt': self.user_prompt,
        }


class InputRouter:
    """
    Routes input files to appropriate extractors based on format.

    Supported formats:
    - Text files (.txt, .md)
    - PDF files (.pdf)
    - Word documents (.docx, .doc)
    - Audio files (.mp3, .wav, .m4a)
    - Video files (.mp4, .mov, .avi)
    - URLs (http://, https://)
    """

    EXTRACTORS = {
        '.txt': 'text',
        '.md': 'text',
        '.pdf': 'pdf',
        '.docx': 'word',
        '.doc': 'word',
        '.mp3': 'audio',
        '.wav': 'audio',
        '.m4a': 'audio',
        '.mp4': 'video',
        '.mov': 'video',
        '.avi': 'video',
        '.mkv': 'video',
    }

    def __init__(self):
        """Initialize the InputRouter."""
        self._extractors = {}

    def _get_extractor(self, extractor_type: str):
        """Lazy-load extractors to avoid import overhead."""
        if extractor_type not in self._extractors:
            if extractor_type == 'text':
                from utils.extractors.text_extractor import TextExtractor
                self._extractors['text'] = TextExtractor()
            elif extractor_type == 'pdf':
                from utils.extractors.pdf_extractor import PDFExtractor
                self._extractors['pdf'] = PDFExtractor()
            elif extractor_type == 'word':
                from utils.extractors.word_extractor import WordExtractor
                self._extractors['word'] = WordExtractor()
            elif extractor_type == 'audio':
                from utils.extractors.audio_extractor import AudioExtractor
                self._extractors['audio'] = AudioExtractor()
            elif extractor_type == 'video':
                from utils.extractors.video_extractor import VideoExtractor
                self._extractors['video'] = VideoExtractor()
            elif extractor_type == 'url':
                from utils.extractors.url_extractor import URLExtractor
                self._extractors['url'] = URLExtractor()
        return self._extractors.get(extractor_type)

    def detect_type(self, input_path: str) -> str:
        """
        Detect the input type based on path or URL.

        Args:
            input_path: File path or URL

        Returns:
            Extractor type string
        """
        # Check if it's a URL
        if input_path.startswith(('http://', 'https://')):
            return 'url'

        # Get file extension
        ext = Path(input_path).suffix.lower()
        return self.EXTRACTORS.get(ext, 'text')

    def extract(
        self,
        input_path: str,
        user_prompt: Optional[str] = None
    ) -> ExtractedContent:
        """
        Extract content from any supported input format.

        Args:
            input_path: Path to input file or URL
            user_prompt: Optional user context/prompt to merge with content

        Returns:
            ExtractedContent object with text and metadata
        """
        extractor_type = self.detect_type(input_path)
        extractor = self._get_extractor(extractor_type)

        if extractor is None:
            raise ValueError(f"No extractor available for type: {extractor_type}")

        # Extract content
        content = extractor.extract(input_path)

        # Add user prompt if provided
        if user_prompt:
            content.user_prompt = user_prompt

        return content

    async def extract_async(
        self,
        input_path: str,
        user_prompt: Optional[str] = None
    ) -> ExtractedContent:
        """
        Async version of extract for pipeline integration.

        Args:
            input_path: Path to input file or URL
            user_prompt: Optional user context/prompt

        Returns:
            ExtractedContent object
        """
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.extract(input_path, user_prompt)
        )

    def get_supported_formats(self) -> Dict[str, str]:
        """Get dictionary of supported formats and their types."""
        return {
            **self.EXTRACTORS,
            'http://': 'url',
            'https://': 'url',
        }


# Convenience function for direct extraction
def extract_content(
    input_path: str,
    user_prompt: Optional[str] = None
) -> ExtractedContent:
    """
    Extract content from any supported input format.

    Args:
        input_path: Path to input file or URL
        user_prompt: Optional user context

    Returns:
        ExtractedContent object
    """
    router = InputRouter()
    return router.extract(input_path, user_prompt)


__all__ = [
    'InputRouter',
    'ExtractedContent',
    'extract_content',
]
