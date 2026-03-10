"""
File management routes.

Handles:
- POST /upload: Upload a file
- POST /upload-url: Extract content from URL
- GET /{id}: Get file info
- DELETE /{id}: Delete a file
- GET /: List all files
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form

from ..models.requests import URLExtractionRequest
from ..models.responses import FileResponse, FileListResponse, ErrorResponse
from ..dependencies import get_file_service
from ..services.file_service import FileService

router = APIRouter()


@router.post(
    "/upload",
    response_model=FileResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid file"},
        413: {"model": ErrorResponse, "description": "File too large"},
    },
    summary="Upload a file",
    description="""
    Upload a file for content extraction.

    Supported formats:
    - Text: .txt, .md
    - PDF: .pdf
    - Word: .docx, .doc
    - Audio: .mp3, .wav, .m4a
    - Video: .mp4, .mov, .avi, .mkv

    The file will be processed to extract text content for podcast generation.
    """,
)
async def upload_file(
    file: UploadFile = File(..., description="File to upload"),
    description: Optional[str] = Form(None, description="Optional description"),
    file_service: FileService = Depends(get_file_service),
) -> FileResponse:
    """
    Upload a file for content extraction.

    Args:
        file: The uploaded file.
        description: Optional description.
        file_service: File management service.

    Returns:
        FileResponse with file ID and metadata.

    Raises:
        HTTPException: If file is invalid or too large.
    """
    # Validate file type
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")

    if not file_service.is_supported_format(file.filename):
        supported = file_service.get_supported_formats()
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format. Supported: {', '.join(supported)}"
        )

    # Upload and extract
    try:
        file_info = await file_service.upload_file(
            file=file,
            description=description,
        )
        return file_info
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except IOError as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")


@router.post(
    "/upload-url",
    response_model=FileResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid URL"},
        422: {"model": ErrorResponse, "description": "Failed to extract"},
    },
    summary="Extract from URL",
    description="""
    Extract content from a web URL.

    The URL content will be fetched, converted to text, and stored
    for use in podcast generation.
    """,
)
async def extract_from_url(
    request: URLExtractionRequest,
    file_service: FileService = Depends(get_file_service),
) -> FileResponse:
    """
    Extract content from a web URL.

    Args:
        request: URL extraction request.
        file_service: File management service.

    Returns:
        FileResponse with extracted content info.

    Raises:
        HTTPException: If URL is invalid or extraction fails.
    """
    try:
        file_info = await file_service.extract_from_url(
            url=request.url,
            description=request.description,
        )
        return file_info
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=422,
            detail=f"Failed to extract content from URL: {e}"
        )


@router.get(
    "/{file_id}",
    response_model=FileResponse,
    responses={
        404: {"model": ErrorResponse, "description": "File not found"},
    },
    summary="Get file info",
    description="Get information about an uploaded file.",
)
async def get_file(
    file_id: str,
    file_service: FileService = Depends(get_file_service),
) -> FileResponse:
    """
    Get information about an uploaded file.

    Args:
        file_id: Unique file identifier.
        file_service: File management service.

    Returns:
        FileResponse with file metadata.

    Raises:
        HTTPException: If file is not found.
    """
    file_info = file_service.get_file(file_id)
    if not file_info:
        raise HTTPException(status_code=404, detail=f"File not found: {file_id}")

    return file_info


@router.delete(
    "/{file_id}",
    response_model=dict,
    responses={
        404: {"model": ErrorResponse, "description": "File not found"},
    },
    summary="Delete a file",
    description="Delete an uploaded file.",
)
async def delete_file(
    file_id: str,
    file_service: FileService = Depends(get_file_service),
) -> dict:
    """
    Delete an uploaded file.

    Args:
        file_id: Unique file identifier.
        file_service: File management service.

    Returns:
        Success message.

    Raises:
        HTTPException: If file is not found.
    """
    if not file_service.file_exists(file_id):
        raise HTTPException(status_code=404, detail=f"File not found: {file_id}")

    file_service.delete_file(file_id)
    return {"message": "File deleted successfully", "id": file_id}


@router.get(
    "/",
    response_model=FileListResponse,
    summary="List all files",
    description="Get a list of all uploaded files.",
)
async def list_files(
    file_service: FileService = Depends(get_file_service),
) -> FileListResponse:
    """
    Get a list of all uploaded files.

    Args:
        file_service: File management service.

    Returns:
        FileListResponse with all file metadata.
    """
    files = file_service.list_files()
    return FileListResponse(files=files, total=len(files))
