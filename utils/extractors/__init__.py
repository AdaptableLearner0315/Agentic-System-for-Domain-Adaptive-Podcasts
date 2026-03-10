"""
Content Extractors
Author: Sarath

Provides extractors for different input formats:
- TextExtractor: Plain text files
- PDFExtractor: PDF documents
- WordExtractor: Word documents (.docx)
- AudioExtractor: Audio files (transcription)
- VideoExtractor: Video files (audio extraction + transcription)
- URLExtractor: Web pages
"""

from utils.extractors.text_extractor import TextExtractor
from utils.extractors.pdf_extractor import PDFExtractor
from utils.extractors.word_extractor import WordExtractor
from utils.extractors.audio_extractor import AudioExtractor
from utils.extractors.video_extractor import VideoExtractor
from utils.extractors.url_extractor import URLExtractor

__all__ = [
    'TextExtractor',
    'PDFExtractor',
    'WordExtractor',
    'AudioExtractor',
    'VideoExtractor',
    'URLExtractor',
]
