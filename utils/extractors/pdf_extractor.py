"""
PDF Extractor
Author: Sarath

Extracts text content from PDF documents using pypdf.
"""

from pathlib import Path
from typing import Optional, List
import re


class PDFExtractor:
    """Extracts content from PDF documents."""

    def __init__(self):
        """Initialize PDF extractor."""
        try:
            import pypdf
            self._pypdf = pypdf
        except ImportError:
            self._pypdf = None

    def extract(self, file_path: str) -> 'ExtractedContent':
        """
        Extract text content from a PDF file.

        Args:
            file_path: Path to the PDF file

        Returns:
            ExtractedContent object
        """
        from utils.input_router import ExtractedContent

        if self._pypdf is None:
            raise ImportError("pypdf is required for PDF extraction. Install with: pip install pypdf")

        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Extract text from PDF
        with open(path, 'rb') as f:
            reader = self._pypdf.PdfReader(f)
            pages = []
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    pages.append(text.strip())

        full_text = '\n\n'.join(pages)

        # Try to extract title from metadata or first page
        title = self._extract_title(reader, full_text, path.stem)

        return ExtractedContent(
            text=full_text,
            source_type='pdf',
            source_path=str(path),
            title=title,
            metadata={
                'page_count': len(reader.pages),
                'word_count': len(full_text.split()),
                'char_count': len(full_text),
                'pdf_metadata': dict(reader.metadata) if reader.metadata else {},
            }
        )

    def _extract_title(self, reader, text: str, fallback: str) -> str:
        """Extract title from PDF metadata or content."""
        # Try metadata first
        if reader.metadata:
            title = reader.metadata.get('/Title')
            if title:
                return str(title)

        # Try first line of first page
        lines = text.split('\n')
        for line in lines[:10]:
            line = line.strip()
            if line and len(line) < 150 and not line.endswith('.'):
                return line

        return fallback.replace('_', ' ').title()
