"""
File upload and extraction service.

Handles file uploads, storage, and content extraction using
the existing InputRouter and extractor infrastructure.
"""

import os
import uuid
import shutil
import re
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Dict, List, Optional
import threading

from fastapi import UploadFile

from ..models.responses import FileResponse
from ..models.enums import InputSourceType


# Mapping of file extensions to source types
EXTENSION_TO_TYPE = {
    ".txt": InputSourceType.TEXT,
    ".md": InputSourceType.TEXT,
    ".pdf": InputSourceType.PDF,
    ".docx": InputSourceType.WORD,
    ".doc": InputSourceType.WORD,
    ".mp3": InputSourceType.AUDIO,
    ".wav": InputSourceType.AUDIO,
    ".m4a": InputSourceType.AUDIO,
    ".mp4": InputSourceType.VIDEO,
    ".mov": InputSourceType.VIDEO,
    ".avi": InputSourceType.VIDEO,
    ".mkv": InputSourceType.VIDEO,
}


def _sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal."""
    # Extract just the filename part (no directory components)
    filename = PurePosixPath(filename).name
    # Remove any remaining path separators
    filename = filename.replace("/", "").replace("\\", "")
    # Remove dangerous characters, keep only safe ones
    filename = re.sub(r'[^\w\s.\-]', '', filename)
    # Limit length
    return filename[:200] or "unnamed"


class FileInfo:
    """
    Internal file information storage.

    Attributes:
        id: Unique file identifier
        filename: Original filename
        content_type: MIME type
        size_bytes: File size
        uploaded_at: Upload timestamp
        source_type: Detected source type
        path: Storage path
        extracted_text: Extracted text content
        description: User description
    """

    def __init__(
        self,
        id: str,
        filename: str,
        content_type: Optional[str],
        size_bytes: int,
        source_type: str,
        path: Path,
        extracted_text: Optional[str] = None,
        description: Optional[str] = None,
    ):
        self.id = id
        self.filename = filename
        self.content_type = content_type
        self.size_bytes = size_bytes
        self.uploaded_at = datetime.utcnow()
        self.source_type = source_type
        self.path = path
        self.extracted_text = extracted_text
        self.description = description


class FileService:
    """
    Manages file uploads and content extraction.

    Provides methods for uploading files, extracting content from URLs,
    and retrieving file information.

    Attributes:
        upload_dir: Directory for storing uploaded files
        max_size_bytes: Maximum allowed file size
        _files: In-memory file registry
        _lock: Thread lock for safe concurrent access
    """

    def __init__(
        self,
        upload_dir: Path,
        max_size_bytes: int = 100 * 1024 * 1024,  # 100MB default
    ):
        """
        Initialize the file service.

        Args:
            upload_dir: Directory for storing uploaded files.
            max_size_bytes: Maximum allowed file size.
        """
        self.upload_dir = upload_dir
        self.max_size_bytes = max_size_bytes
        self._files: Dict[str, FileInfo] = {}
        self._lock = threading.Lock()

        # Ensure upload directory exists
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    async def upload_file(
        self,
        file: UploadFile,
        description: Optional[str] = None,
    ) -> FileResponse:
        """
        Upload and process a file.

        Args:
            file: FastAPI UploadFile object.
            description: Optional file description.

        Returns:
            FileResponse with file information.

        Raises:
            ValueError: If file type is unsupported or file is too large.
            IOError: If file cannot be saved.
        """
        if not file.filename:
            raise ValueError("Filename is required")

        # Generate unique ID
        file_id = str(uuid.uuid4())[:8]

        # Determine source type
        ext = Path(file.filename).suffix.lower()
        source_type = EXTENSION_TO_TYPE.get(ext)
        if not source_type:
            raise ValueError(f"Unsupported file type: {ext}")

        # Create file path with sanitized filename
        safe_filename = f"{file_id}_{_sanitize_filename(file.filename)}"
        file_path = self.upload_dir / safe_filename

        # Stream file in chunks with size check
        total_read = 0
        chunk_size = 8192  # 8KB chunks
        with open(file_path, 'wb') as f:
            while True:
                chunk = await file.read(chunk_size)
                if not chunk:
                    break
                total_read += len(chunk)
                if total_read > self.max_size_bytes:
                    f.close()
                    file_path.unlink(missing_ok=True)
                    raise ValueError(f"File too large. Maximum size: {self.max_size_bytes // (1024*1024)}MB")
                f.write(chunk)

        # Extract text content
        extracted_text = await self._extract_text(file_path, source_type)

        # Create file info
        file_info = FileInfo(
            id=file_id,
            filename=file.filename,
            content_type=file.content_type,
            size_bytes=total_read,
            source_type=source_type.value,
            path=file_path,
            extracted_text=extracted_text,
            description=description,
        )

        with self._lock:
            self._files[file_id] = file_info

        return self._to_response(file_info)

    async def extract_from_url(
        self,
        url: str,
        description: Optional[str] = None,
    ) -> FileResponse:
        """
        Extract content from a URL.

        Args:
            url: Web URL to extract from.
            description: Optional description.

        Returns:
            FileResponse with extracted content info.

        Raises:
            ValueError: If URL is invalid.
            Exception: If extraction fails.
        """
        # Import URL extractor
        try:
            from utils.extractors.url_extractor import URLExtractor
            extractor = URLExtractor()
        except ImportError:
            # Fallback implementation
            import urllib.request
            from html.parser import HTMLParser

            class TextExtractor(HTMLParser):
                def __init__(self):
                    super().__init__()
                    self.text = []
                    self._in_script = False
                    self._in_style = False

                def handle_starttag(self, tag, attrs):
                    if tag in ("script", "style"):
                        self._in_script = True

                def handle_endtag(self, tag):
                    if tag in ("script", "style"):
                        self._in_script = False

                def handle_data(self, data):
                    if not self._in_script:
                        self.text.append(data.strip())

            # Fetch URL content
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Nell Podcast Generator"}
            )
            with urllib.request.urlopen(req, timeout=30) as response:
                html_content = response.read().decode("utf-8", errors="ignore")

            parser = TextExtractor()
            parser.feed(html_content)
            extracted_text = "\n".join(filter(None, parser.text))

            # Create file info for URL
            file_id = str(uuid.uuid4())[:8]
            filename = f"url_{file_id}.txt"
            file_path = self.upload_dir / filename

            # Save extracted text
            with open(file_path, "w") as f:
                f.write(extracted_text)

            file_info = FileInfo(
                id=file_id,
                filename=filename,
                content_type="text/plain",
                size_bytes=len(extracted_text.encode()),
                source_type=InputSourceType.URL.value,
                path=file_path,
                extracted_text=extracted_text[:500] if extracted_text else None,
                description=description or url,
            )

            with self._lock:
                self._files[file_id] = file_info

            return self._to_response(file_info)

        # Use URL extractor if available
        result = await extractor.extract_async(url)

        file_id = str(uuid.uuid4())[:8]
        filename = f"url_{file_id}.txt"
        file_path = self.upload_dir / filename

        with open(file_path, "w") as f:
            f.write(result.text)

        file_info = FileInfo(
            id=file_id,
            filename=filename,
            content_type="text/plain",
            size_bytes=len(result.text.encode()),
            source_type=InputSourceType.URL.value,
            path=file_path,
            extracted_text=result.text[:500] if result.text else None,
            description=description or url,
        )

        with self._lock:
            self._files[file_id] = file_info

        return self._to_response(file_info)

    async def _extract_text(
        self,
        file_path: Path,
        source_type: InputSourceType,
    ) -> Optional[str]:
        """
        Extract text from a file.

        Args:
            file_path: Path to the file.
            source_type: Type of source file.

        Returns:
            Extracted text content, or None if extraction fails.
        """
        try:
            if source_type == InputSourceType.TEXT:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    return f.read()[:500]  # Preview only

            elif source_type == InputSourceType.PDF:
                try:
                    from utils.extractors.pdf_extractor import PDFExtractor
                    extractor = PDFExtractor()
                    result = extractor.extract(str(file_path))
                    return result.text[:500] if result.text else None
                except ImportError:
                    return "[PDF extraction requires pypdf]"

            elif source_type == InputSourceType.WORD:
                try:
                    from utils.extractors.word_extractor import WordExtractor
                    extractor = WordExtractor()
                    result = extractor.extract(str(file_path))
                    return result.text[:500] if result.text else None
                except ImportError:
                    return "[Word extraction requires python-docx]"

            elif source_type in (InputSourceType.AUDIO, InputSourceType.VIDEO):
                return "[Audio/video content - transcription on processing]"

        except Exception as e:
            return f"[Extraction failed: {e}]"

        return None

    def get_file(self, file_id: str) -> Optional[FileResponse]:
        """
        Get file information by ID.

        Args:
            file_id: Unique file identifier.

        Returns:
            FileResponse if found, None otherwise.
        """
        with self._lock:
            file_info = self._files.get(file_id)
            if file_info:
                return self._to_response(file_info)
        return None

    def get_file_path(self, file_id: str) -> Optional[Path]:
        """
        Get the file path for a file ID.

        Args:
            file_id: Unique file identifier.

        Returns:
            Path to the file if found, None otherwise.
        """
        with self._lock:
            file_info = self._files.get(file_id)
            if file_info:
                return file_info.path
        return None

    def file_exists(self, file_id: str) -> bool:
        """
        Check if a file exists.

        Args:
            file_id: Unique file identifier.

        Returns:
            True if file exists.
        """
        with self._lock:
            return file_id in self._files

    def delete_file(self, file_id: str) -> bool:
        """
        Delete a file.

        Args:
            file_id: Unique file identifier.

        Returns:
            True if file was deleted.
        """
        with self._lock:
            file_info = self._files.get(file_id)
            if file_info:
                # Delete physical file
                try:
                    if file_info.path.exists():
                        file_info.path.unlink()
                except Exception:
                    pass  # Ignore deletion errors

                # Remove from registry
                del self._files[file_id]
                return True
        return False

    def list_files(self) -> List[FileResponse]:
        """
        List all uploaded files.

        Returns:
            List of FileResponse objects.
        """
        with self._lock:
            return [self._to_response(f) for f in self._files.values()]

    def is_supported_format(self, filename: str) -> bool:
        """
        Check if a file format is supported.

        Args:
            filename: Filename to check.

        Returns:
            True if format is supported.
        """
        ext = Path(filename).suffix.lower()
        return ext in EXTENSION_TO_TYPE

    def get_supported_formats(self) -> List[str]:
        """
        Get list of supported file formats.

        Returns:
            List of supported file extensions.
        """
        return list(EXTENSION_TO_TYPE.keys())

    def _to_response(self, file_info: FileInfo) -> FileResponse:
        """
        Convert internal FileInfo to FileResponse.

        Args:
            file_info: Internal file info.

        Returns:
            FileResponse for API output.
        """
        return FileResponse(
            id=file_info.id,
            filename=file_info.filename,
            content_type=file_info.content_type,
            size_bytes=file_info.size_bytes,
            uploaded_at=file_info.uploaded_at,
            source_type=file_info.source_type,
            extracted_text=file_info.extracted_text,
        )
