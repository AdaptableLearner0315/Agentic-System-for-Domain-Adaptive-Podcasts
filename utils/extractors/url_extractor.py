"""
URL Extractor
Author: Sarath

Extracts text content from web pages using newspaper3k.
"""

from typing import Optional


class URLExtractor:
    """Extracts content from web URLs."""

    def __init__(self):
        """Initialize URL extractor."""
        self._newspaper = None

    def _load_newspaper(self):
        """Lazy-load newspaper3k."""
        if self._newspaper is None:
            try:
                import newspaper
                self._newspaper = newspaper
            except ImportError:
                raise ImportError("newspaper3k is required for URL extraction. Install with: pip install newspaper3k")

    def extract(self, url: str) -> 'ExtractedContent':
        """
        Extract text content from a web URL.

        Args:
            url: URL to extract content from

        Returns:
            ExtractedContent object
        """
        from utils.input_router import ExtractedContent

        # Load newspaper3k
        self._load_newspaper()

        print(f"[URLExtractor] Fetching {url}...")

        # Create article and download
        article = self._newspaper.Article(url)
        article.download()
        article.parse()

        text = article.text.strip()
        title = article.title or url

        return ExtractedContent(
            text=text,
            source_type='url',
            source_path=url,
            title=title,
            metadata={
                'authors': article.authors,
                'publish_date': str(article.publish_date) if article.publish_date else None,
                'word_count': len(text.split()),
                'top_image': article.top_image,
                'keywords': list(article.keywords) if article.keywords else [],
            }
        )
