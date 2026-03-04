"""
Trailer route - Serve trailer preview files.

Author: Sarath

Provides endpoints to serve trailer video/audio files generated
during podcast creation.
"""

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from ..config import get_settings


router = APIRouter()


@router.get("/{job_id}")
async def get_trailer(job_id: str):
    """
    Serve trailer video or audio file.

    The trailer is generated immediately after script enhancement
    to give users playable content while the full podcast generates.

    Args:
        job_id: Job identifier.

    Returns:
        FileResponse with trailer video (MP4) or audio (MP3).

    Raises:
        HTTPException 404: If trailer not found for this job.
    """
    settings = get_settings()
    trailer_dir = settings.output_path / job_id / "trailer"

    # Try video first, then audio
    video_path = trailer_dir / f"trailer_{job_id}.mp4"
    audio_path = trailer_dir / f"trailer_mixed_{job_id}.mp3"

    if video_path.exists():
        return FileResponse(
            path=str(video_path),
            media_type="video/mp4",
            filename=f"trailer_{job_id}.mp4"
        )
    elif audio_path.exists():
        return FileResponse(
            path=str(audio_path),
            media_type="audio/mpeg",
            filename=f"trailer_{job_id}.mp3"
        )
    else:
        raise HTTPException(
            status_code=404,
            detail=f"Trailer not found for job {job_id}"
        )


@router.head("/{job_id}")
async def check_trailer_exists(job_id: str):
    """
    Check if trailer exists for a job.

    Used by frontend to verify trailer availability before rendering player.

    Args:
        job_id: Job identifier.

    Returns:
        Empty 200 response if trailer exists.

    Raises:
        HTTPException 404: If trailer not found.
    """
    settings = get_settings()
    trailer_dir = settings.output_path / job_id / "trailer"

    video_path = trailer_dir / f"trailer_{job_id}.mp4"
    audio_path = trailer_dir / f"trailer_mixed_{job_id}.mp3"

    if video_path.exists() or audio_path.exists():
        return None  # 200 OK with empty body
    else:
        raise HTTPException(
            status_code=404,
            detail=f"Trailer not found for job {job_id}"
        )


__all__ = ['router']
