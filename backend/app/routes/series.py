"""
Series API Routes
Author: Sarath

REST endpoints for episodic series creation and management.

Endpoints:
- POST   /api/series                    - Create series + generate outline
- GET    /api/series/{id}               - Get series details
- POST   /api/series/{id}/approve       - Approve/modify outline
- POST   /api/series/{id}/generate      - Generate next episode
- GET    /api/series/{id}/episodes/{n}  - Get episode details
- DELETE /api/series/{id}               - Cancel series
- GET    /api/series                    - List all series
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies import get_db, get_job_manager, get_pipeline_service
from ..services.series_service import SeriesService
from ..models.requests import (
    CreateSeriesRequest,
    ApproveOutlineRequest,
    GenerateEpisodeRequest
)
from ..models.responses import (
    SeriesResponse,
    EpisodeResponse,
    SeriesListResponse,
    ErrorResponse
)
from ..logging_config import get_logger

logger = get_logger("series_routes")

router = APIRouter(
    tags=["series"],
    responses={
        400: {"model": ErrorResponse, "description": "Bad request"},
        404: {"model": ErrorResponse, "description": "Not found"},
        500: {"model": ErrorResponse, "description": "Internal error"},
    }
)


async def get_series_service(
    session: AsyncSession = Depends(get_db)
) -> SeriesService:
    """Get series service with database session."""
    return SeriesService(
        session=session,
        job_manager=get_job_manager(),
        pipeline_service=get_pipeline_service()
    )


@router.post(
    "",
    response_model=SeriesResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new podcast series",
    description="""
    Creates a new podcast series with AI-generated outline.

    The system:
    1. Analyzes your prompt to detect genre, era, and style
    2. Generates a complete series outline with episode summaries
    3. Plans callbacks, cliffhangers, and narrative arcs

    Returns the series in 'draft' status for review and approval.
    """
)
async def create_series(
    request: CreateSeriesRequest,
    service: SeriesService = Depends(get_series_service)
) -> SeriesResponse:
    """Create a new podcast series."""
    try:
        logger.info("Creating series: %s", request.prompt[:50])
        series = await service.create_series(request)
        return series
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Failed to create series: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create series: {e}")


@router.get(
    "/{series_id}",
    response_model=SeriesResponse,
    summary="Get series details",
    description="Get full details of a series including outline, episodes, and progress."
)
async def get_series(
    series_id: str,
    service: SeriesService = Depends(get_series_service)
) -> SeriesResponse:
    """Get series by ID."""
    series = await service.get_series(series_id)
    if not series:
        raise HTTPException(
            status_code=404,
            detail=f"Series not found: {series_id}"
        )
    return series


@router.post(
    "/{series_id}/approve",
    response_model=SeriesResponse,
    summary="Approve or modify series outline",
    description="""
    Approve the series outline to begin episode generation.

    On approval:
    1. Any modifications are applied to the outline
    2. Series audio assets are generated (intro, outro, stings)
    3. Status changes to 'in_progress'

    You can optionally modify episode titles, premises, etc.
    """
)
async def approve_outline(
    series_id: str,
    request: ApproveOutlineRequest,
    service: SeriesService = Depends(get_series_service)
) -> SeriesResponse:
    """Approve or modify a series outline."""
    try:
        series = await service.approve_outline(series_id, request)
        return series
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Failed to approve outline: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to approve outline: {e}")


@router.post(
    "/{series_id}/generate",
    summary="Generate the next episode",
    description="""
    Start generating the next episode in the series.

    The system:
    1. Generates "Previously on..." narration (episodes 2+)
    2. Builds continuity context from prior episodes
    3. Generates episode content with callbacks and cliffhangers
    4. Updates series continuity state

    Returns a job_id for tracking generation progress.
    """
)
async def generate_episode(
    series_id: str,
    request: GenerateEpisodeRequest = None,
    service: SeriesService = Depends(get_series_service)
):
    """Generate the next episode in the series."""
    if request is None:
        request = GenerateEpisodeRequest()

    try:
        result = await service.generate_episode(series_id, request)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Failed to generate episode: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate episode: {e}")


@router.get(
    "/{series_id}/episodes/{episode_number}",
    response_model=EpisodeResponse,
    summary="Get episode details",
    description="Get details of a specific episode including status, outputs, and content."
)
async def get_episode(
    series_id: str,
    episode_number: int,
    service: SeriesService = Depends(get_series_service)
) -> EpisodeResponse:
    """Get episode by series ID and episode number."""
    series = await service.get_series(series_id)
    if not series:
        raise HTTPException(
            status_code=404,
            detail=f"Series not found: {series_id}"
        )

    for episode in series.episodes:
        if episode.episode_number == episode_number:
            return episode

    raise HTTPException(
        status_code=404,
        detail=f"Episode {episode_number} not found"
    )


@router.delete(
    "/{series_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cancel/delete a series",
    description="Cancels a series. Episodes already generated are preserved."
)
async def delete_series(
    series_id: str,
    service: SeriesService = Depends(get_series_service)
):
    """Delete/cancel a series."""
    success = await service.delete_series(series_id)
    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"Series not found: {series_id}"
        )
    return None


@router.get(
    "",
    response_model=SeriesListResponse,
    summary="List all series",
    description="Get a paginated list of all series, optionally filtered by status."
)
async def list_series(
    status: Optional[str] = Query(None, description="Filter by status: draft, in_progress, completed, cancelled"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    service: SeriesService = Depends(get_series_service)
) -> SeriesListResponse:
    """List all series with pagination."""
    return await service.list_series(status=status, page=page, page_size=page_size)
