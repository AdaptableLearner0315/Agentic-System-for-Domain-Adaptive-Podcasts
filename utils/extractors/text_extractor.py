"""
Text Extractor
Author: Sarath

Extracts content from plain text and markdown files.
"""

from pathlib import Path
from typing import Optional
import re


class TextExtractor:
    """Extracts content from plain text files."""

    def extract(self, file_path: str) -> 'ExtractedContent':
        """
        Extract text content from a file.

        Args:
            file_path: Path to the text file

        Returns:
            ExtractedContent object
        """
        from utils.input_router import ExtractedContent

        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(path, 'r', encoding='utf-8') as f:
            text = f.read()

        # Try to extract title from first line or filename
        title = self._extract_title(text, path.stem)

        return ExtractedContent(
            text=text.strip(),
            source_type='text',
            source_path=str(path),
            title=title,
            metadata={
                'file_size': path.stat().st_size,
                'word_count': len(text.split()),
                'char_count': len(text),
            }
        )

    def _extract_title(self, text: str, fallback: str) -> str:
        """Extract title from text content."""
        lines = text.strip().split('\n')
        if lines:
            first_line = lines[0].strip()
            # Check if it's a markdown header
            if first_line.startswith('#'):
                return first_line.lstrip('#').strip()
            # If first line is short enough, use it as title
            if len(first_line) < 100 and not first_line.endswith('.'):
                return first_line
        return fallback.replace('_', ' ').title()
