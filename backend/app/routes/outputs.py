"""
Output file routes.

Handles:
- GET /download/{job_id}: Download output files
- GET /stream/{job_id}: Stream video
"""

from pathlib import Path
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse, StreamingResponse

from ..models.responses import ErrorResponse
from ..dependencies import get_job_manager
from ..services.job_manager import JobManager
from ..models.enums import JobStatus
from ..config import get_settings, Settings
from ..constants import STREAM_CHUNK_SIZE

router = APIRouter()


def _validate_file_path(file_path: Path, settings: Settings) -> None:
    """
    Validate that a file path is within allowed directories.

    Prevents directory traversal attacks by ensuring the resolved path
    is within the output or upload directories.

    Args:
        file_path: Resolved path to validate.
        settings: Application settings with allowed directory paths.

    Raises:
        HTTPException: If path is outside allowed directories.
    """
    allowed_dirs = [
        Path(settings.output_path).resolve(),
        Path(settings.upload_path).resolve(),
    ]
    if not any(str(file_path).startswith(str(d)) for d in allowed_dirs):
        raise HTTPException(
            status_code=403,
            detail="Access denied: path outside allowed directory"
        )


@router.get(
    "/download/{job_id}",
    responses={
        404: {"model": ErrorResponse, "description": "Job or file not found"},
        400: {"model": ErrorResponse, "description": "Job not completed"},
    },
    summary="Download output",
    description="Download the generated video file for a completed job.",
)
async def download_output(
    job_id: str,
    file_type: str = "video",
    job_manager: JobManager = Depends(get_job_manager),
):
    """
    Download the generated output file.

    Args:
        job_id: Unique job identifier.
        file_type: Type of file to download (video, audio, script).
        job_manager: Job management service.

    Returns:
        FileResponse with the requested file.

    Raises:
        HTTPException: If job is not found, not completed, or file not available.
    """
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")

    if job.status != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"Job is not completed. Current status: {job.status}"
        )

    result = job_manager.get_result(job_id)
    if not result:
        raise HTTPException(status_code=404, detail="Result not available")

    # Determine file path based on type
    settings = get_settings()
    file_path = None
    media_type = None
    filename = None

    if file_type == "video":
        if result.output_path:
            file_path = Path(result.output_path).resolve()
            _validate_file_path(file_path, settings)
            media_type = "video/mp4"
            filename = f"nell_podcast_{job_id}.mp4"
    elif file_type == "audio":
        # Use the stored audio path directly
        if result.audio_output_path:
            audio_path = Path(result.audio_output_path).resolve()
            _validate_file_path(audio_path, settings)
            if audio_path.exists():
                file_path = audio_path
                media_type = "audio/mpeg"
                filename = f"nell_podcast_{job_id}.mp3"
    elif file_type == "script":
        # Look for script JSON
        if result.script:
            import json
            import tempfile

            # Create temp file with script JSON
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".json", delete=False
            ) as f:
                json.dump(result.script, f, indent=2)
                file_path = Path(f.name)
            media_type = "application/json"
            filename = f"nell_script_{job_id}.json"

    if not file_path or not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"File not found for type: {file_type}"
        )

    return FileResponse(
        path=str(file_path),
        media_type=media_type,
        filename=filename,
    )


@router.get(
    "/stream/{job_id}",
    responses={
        404: {"model": ErrorResponse, "description": "Job or file not found"},
        400: {"model": ErrorResponse, "description": "Job not completed"},
    },
    summary="Stream video",
    description="Stream the generated video for playback.",
)
async def stream_video(
    job_id: str,
    job_manager: JobManager = Depends(get_job_manager),
):
    """
    Stream the generated video file.

    Args:
        job_id: Unique job identifier.
        job_manager: Job management service.

    Returns:
        StreamingResponse for video playback.

    Raises:
        HTTPException: If job is not found or video not available.
    """
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")

    if job.status != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"Job is not completed. Current status: {job.status}"
        )

    result = job_manager.get_result(job_id)
    if not result or not result.output_path:
        raise HTTPException(status_code=404, detail="Video not available")

    settings = get_settings()
    file_path = Path(result.output_path).resolve()
    _validate_file_path(file_path, settings)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Video file not found")

    def iterfile():
        """Generator to stream file in chunks."""
        with open(file_path, "rb") as f:
            while chunk := f.read(STREAM_CHUNK_SIZE):
                yield chunk

    file_size = file_path.stat().st_size
    return StreamingResponse(
        iterfile(),
        media_type="video/mp4",
        headers={
            "Content-Disposition": f"inline; filename=nell_podcast_{job_id}.mp4",
            "Content-Length": str(file_size),
            "Accept-Ranges": "bytes",
        },
    )


@router.get(
    "/preview/{job_id}/{asset_type}/{asset_id}",
    responses={
        404: {"model": ErrorResponse, "description": "Asset not found"},
    },
    summary="Preview asset",
    description="Preview a specific asset (image, audio segment).",
)
async def preview_asset(
    job_id: str,
    asset_type: str,
    asset_id: str,
    job_manager: JobManager = Depends(get_job_manager),
):
    """
    Preview a specific generated asset.

    Args:
        job_id: Unique job identifier.
        asset_type: Type of asset (image, tts, bgm).
        asset_id: Asset identifier.
        job_manager: Job management service.

    Returns:
        FileResponse with the asset file.

    Raises:
        HTTPException: If asset is not found.
    """
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")

    result = job_manager.get_result(job_id)
    if not result:
        raise HTTPException(status_code=404, detail="Result not available")

    # Find the asset
    asset = None
    media_type = None

    if asset_type == "image":
        for img in result.image_assets:
            if img.id == asset_id:
                asset = img
                media_type = "image/png"
                break
    elif asset_type == "tts":
        for tts in result.tts_assets:
            if tts.id == asset_id:
                asset = tts
                media_type = "audio/wav"
                break
    elif asset_type == "bgm":
        for bgm in result.bgm_assets:
            if bgm.id == asset_id:
                asset = bgm
                media_type = "audio/wav"
                break

    if not asset:
        raise HTTPException(
            status_code=404,
            detail=f"Asset not found: {asset_type}/{asset_id}"
        )

    settings = get_settings()
    file_path = Path(asset.path).resolve()
    _validate_file_path(file_path, settings)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Asset file not found")

    return FileResponse(
        path=str(file_path),
        media_type=media_type,
        filename=asset.filename,
    )
