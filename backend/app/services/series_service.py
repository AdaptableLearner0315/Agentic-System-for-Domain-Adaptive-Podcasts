"""
Series Service
Author: Sarath

Orchestrates the creation and generation of episodic podcast series.

Workflow:
1. create_series() - IntentAnalyzer → SeriesPlanner → save draft
2. approve_outline() - apply modifications, generate series assets, set in_progress
3. generate_episode() - full episode generation with continuity
"""

import asyncio
import uuid
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List, Any

# Add project root to path for importing existing modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from agents.intent_analyzer import IntentAnalyzer
from agents.series_planner_agent import SeriesPlannerAgent
from agents.continuity_manager import ContinuityManager, create_initial_state
from agents.episode_linker import EpisodeLinker
from agents.series_asset_generator import SeriesAssetGenerator

from ..database.models import SeriesModel, EpisodeModel
from ..models.series import (
    SeriesStatus, EpisodeStatus, Series, Episode, SeriesOutline,
    StyleDNA, ContinuityState
)
from ..models.requests import CreateSeriesRequest, ApproveOutlineRequest, GenerateEpisodeRequest
from ..models.responses import (
    SeriesResponse, EpisodeResponse, SeriesOutlineResponse,
    EpisodeSummaryResponse, StyleDNAResponse, SeriesListResponse
)
from ..config import get_settings
from ..logging_config import get_logger

logger = get_logger("series")


class SeriesService:
    """
    Service for creating and managing episodic podcast series.

    Handles the full series lifecycle from creation through episode generation,
    maintaining continuity state across the series.
    """

    def __init__(self, session: AsyncSession, job_manager=None, pipeline_service=None):
        """
        Initialize the SeriesService.

        Args:
            session: SQLAlchemy async session
            job_manager: Optional JobManager for episode generation
            pipeline_service: Optional PipelineService for episode generation
        """
        self.session = session
        self.job_manager = job_manager
        self.pipeline_service = pipeline_service
        self.settings = get_settings()

        # Initialize agents
        self.intent_analyzer = IntentAnalyzer()
        self.series_planner = SeriesPlannerAgent()
        self.continuity_manager = ContinuityManager()
        self.episode_linker = EpisodeLinker()
        self.asset_generator = SeriesAssetGenerator()

    async def create_series(self, request: CreateSeriesRequest) -> SeriesResponse:
        """
        Create a new series with generated outline.

        1. Analyzes prompt with IntentAnalyzer to get StyleDNA
        2. Plans series with SeriesPlannerAgent
        3. Saves series as draft for user approval

        Args:
            request: CreateSeriesRequest with prompt and configuration

        Returns:
            SeriesResponse with generated outline
        """
        logger.info("Creating series for prompt: %s", request.prompt[:50])

        # Generate series ID
        series_id = str(uuid.uuid4())

        # Step 1: Analyze intent and generate StyleDNA
        logger.info("Analyzing intent...")
        style_dna = await asyncio.to_thread(
            self.intent_analyzer.analyze,
            request.prompt,
            request.guidance
        )

        # Step 2: Plan series outline
        logger.info("Planning series outline...")
        outline = await asyncio.to_thread(
            self.series_planner.plan_series,
            request.prompt,
            request.episode_count,
            style_dna,
            request.episode_length
        )

        # Step 3: Create database model
        now = datetime.utcnow()
        series_model = SeriesModel(
            id=series_id,
            status=SeriesStatus.DRAFT.value,
            prompt=request.prompt,
            guidance=request.guidance,
            mode=request.mode,
            series_type=request.series_type,
            episode_length=request.episode_length,
            episode_count=request.episode_count,
            title=outline.get("title", "Untitled Series"),
            description=outline.get("description", ""),
            created_at=now,
            updated_at=now
        )

        # Set JSON fields
        series_model.outline = outline
        series_model.style_dna = style_dna
        series_model.continuity_state = create_initial_state()

        # Save to database
        self.session.add(series_model)
        await self.session.commit()
        await self.session.refresh(series_model)

        logger.info("Series created: %s - %s", series_id, outline.get("title"))

        return self._model_to_response(series_model)

    async def approve_outline(
        self,
        series_id: str,
        request: ApproveOutlineRequest
    ) -> SeriesResponse:
        """
        Approve or modify a series outline.

        1. Apply any user modifications
        2. Generate series audio assets
        3. Set status to in_progress

        Args:
            series_id: Series ID to approve
            request: ApproveOutlineRequest with approval and modifications

        Returns:
            Updated SeriesResponse
        """
        # Get series
        series_model = await self._get_series_model(series_id)
        if not series_model:
            raise ValueError(f"Series not found: {series_id}")

        if series_model.status != SeriesStatus.DRAFT.value:
            raise ValueError(f"Series is not in draft status: {series_model.status}")

        # Apply modifications if any
        if request.modifications:
            logger.info("Applying modifications to series %s", series_id)
            outline = series_model.outline or {}
            outline = self.series_planner.modify_outline(outline, request.modifications)
            series_model.outline = outline
            series_model.title = outline.get("title", series_model.title)
            series_model.description = outline.get("description", series_model.description)

        if request.approved:
            # Generate series assets
            logger.info("Generating series assets for %s", series_id)

            assets_path = Path(self.settings.output_dir) / "series" / series_id
            assets_path.mkdir(parents=True, exist_ok=True)

            style_dna = series_model.style_dna or {}
            assets = await asyncio.to_thread(
                self.asset_generator.generate_series_assets,
                series_id,
                style_dna,
                assets_path
            )

            series_model.assets = assets
            series_model.assets_path = str(assets_path)
            series_model.status = SeriesStatus.IN_PROGRESS.value
            series_model.approved_at = datetime.utcnow()

            # Initialize episode models
            outline = series_model.outline or {}
            for ep_outline in outline.get("episodes", []):
                episode_model = EpisodeModel(
                    id=str(uuid.uuid4()),
                    series_id=series_id,
                    episode_number=ep_outline.get("episode_number", 1),
                    title=ep_outline.get("title", ""),
                    status=EpisodeStatus.PENDING.value,
                    cliffhanger_type=ep_outline.get("cliffhanger_type"),
                    created_at=datetime.utcnow()
                )
                self.session.add(episode_model)

        series_model.updated_at = datetime.utcnow()
        await self.session.commit()
        await self.session.refresh(series_model)

        return self._model_to_response(series_model)

    async def generate_episode(
        self,
        series_id: str,
        request: GenerateEpisodeRequest
    ) -> Dict[str, Any]:
        """
        Generate the next episode in a series.

        1. Load series and continuity state
        2. Generate "previously on" for episodes 2+
        3. Build guidance context from continuity
        4. Generate episode content via pipeline
        5. Generate cliffhanger
        6. Update continuity state

        Args:
            series_id: Series ID
            request: GenerateEpisodeRequest with optional episode number

        Returns:
            Dict with job_id for tracking generation progress
        """
        # Get series
        series_model = await self._get_series_model(series_id)
        if not series_model:
            raise ValueError(f"Series not found: {series_id}")

        if series_model.status != SeriesStatus.IN_PROGRESS.value:
            raise ValueError(f"Series not in progress: {series_model.status}")

        # Determine which episode to generate
        episode_number = request.episode_number
        if not episode_number:
            # Find next pending episode
            for ep in series_model.episodes:
                if ep.status == EpisodeStatus.PENDING.value:
                    episode_number = ep.episode_number
                    break

        if not episode_number:
            raise ValueError("No pending episodes to generate")

        # Get episode model
        episode_model = None
        for ep in series_model.episodes:
            if ep.episode_number == episode_number:
                episode_model = ep
                break

        if not episode_model:
            raise ValueError(f"Episode {episode_number} not found")

        if episode_model.status != EpisodeStatus.PENDING.value:
            raise ValueError(f"Episode {episode_number} is not pending: {episode_model.status}")

        logger.info("Generating episode %d of series %s", episode_number, series_id)

        # Get series data
        outline = series_model.outline or {}
        style_dna = series_model.style_dna or {}
        continuity_state = series_model.continuity_state or create_initial_state()
        total_episodes = series_model.episode_count

        # Get episode outline
        episode_outline = None
        for ep in outline.get("episodes", []):
            if ep.get("episode_number") == episode_number:
                episode_outline = ep
                break

        if not episode_outline:
            raise ValueError(f"Episode {episode_number} outline not found")

        # Generate "previously on" for episodes 2+
        previously_on = None
        if episode_number > 1:
            previously_on = await asyncio.to_thread(
                self.continuity_manager.generate_previously_on,
                series_model.title or outline.get("title", ""),
                episode_number,
                continuity_state,
                episode_outline.get("premise", "")
            )

        # Build generation guidance
        guidance = self.continuity_manager.get_context_for_generation(
            series_model.title or outline.get("title", ""),
            episode_number,
            total_episodes,
            episode_outline.get("premise", ""),
            outline,
            continuity_state
        )

        # Add style DNA guidance
        if style_dna.get("language_profile"):
            lang = style_dna["language_profile"]
            guidance += f"\n\nSTYLE GUIDANCE:\n- Tone: {lang.get('tone', 'engaging')}\n- Use vocabulary: {', '.join(lang.get('vocabulary', []))}"

        # Mark episode as generating
        episode_model.status = EpisodeStatus.GENERATING.value
        episode_model.previously_on = previously_on

        # Create job for progress tracking
        if not self.job_manager or not self.pipeline_service:
            raise ValueError("Job manager and pipeline service are required for episode generation")

        from ..models.enums import PipelineMode

        # Map string mode to PipelineMode enum
        mode_map = {"normal": PipelineMode.NORMAL, "pro": PipelineMode.PRO, "ultra": PipelineMode.ULTRA}
        pipeline_mode = mode_map.get(series_model.mode, PipelineMode.NORMAL)

        # Create the job
        job_response = self.job_manager.create_job(
            mode=pipeline_mode,
            prompt=episode_outline.get("premise", ""),
            guidance=guidance,
        )
        job_id = job_response.id

        # Store job_id in episode for tracking
        episode_model.job_id = job_id
        await self.session.commit()

        # Start pipeline in background (non-blocking)
        asyncio.create_task(self._run_episode_pipeline(
            job_id=job_id,
            series_id=series_id,
            episode_number=episode_number,
            episode_outline=episode_outline,
            guidance=guidance,
            previously_on=previously_on,
            assets_path=series_model.assets_path,
            mode=series_model.mode,
        ))

        return {
            "job_id": job_id,
            "series_id": series_id,
            "episode_number": episode_number,
            "episode_id": episode_model.id,
            "status": "generating",
            "previously_on": previously_on,
            "guidance": guidance,
            "cliffhanger_type": episode_outline.get("cliffhanger_type"),
            "message": "Episode generation initiated"
        }

    async def _run_episode_pipeline(
        self,
        job_id: str,
        series_id: str,
        episode_number: int,
        episode_outline: Dict[str, Any],
        guidance: str,
        previously_on: Optional[str],
        assets_path: Optional[str],
        mode: str,
    ) -> None:
        """
        Run the pipeline for an episode in the background.

        This is a fire-and-forget task that runs the full podcast pipeline
        and updates the episode on completion.

        Args:
            job_id: Job ID for progress tracking
            series_id: Series ID
            episode_number: Episode number being generated
            episode_outline: Episode outline with premise and title
            guidance: Combined guidance for generation
            previously_on: Previously on text (for eps 2+)
            assets_path: Path to series assets
            mode: Pipeline mode (normal, pro, ultra)
        """
        from ..models.requests import GenerationRequest

        try:
            # Build the prompt with previously_on and series context
            episode_title = episode_outline.get("title", f"Episode {episode_number}")
            episode_premise = episode_outline.get("premise", "")

            prompt_parts = []
            if previously_on:
                prompt_parts.append(f"[PREVIOUSLY ON]: {previously_on}\n")
            prompt_parts.append(f"Episode {episode_number}: {episode_title}")
            prompt_parts.append(f"\n{episode_premise}")

            full_prompt = "".join(prompt_parts)

            # Create the generation request
            request = GenerationRequest(
                prompt=full_prompt,
                guidance=guidance,
                mode=mode,
            )

            # Run the pipeline
            await self.pipeline_service.run_job(job_id, request)

            # Get the job result
            job = self.job_manager.get_job(job_id)
            if job and job.result:
                result = job.result
                script = result.script if result else {}
                output_path = result.output_path if result else None
                audio_path = result.audio_output_path if result else None
                duration = result.duration_seconds if result else 0

                # Complete the episode with result data
                await self.complete_episode(
                    series_id=series_id,
                    episode_number=episode_number,
                    script=script or {},
                    output_path=output_path or "",
                    audio_path=audio_path or "",
                    duration_seconds=duration or 0,
                )
                logger.info(
                    "Episode %d of series %s completed successfully",
                    episode_number,
                    series_id
                )
            else:
                # Job failed - update episode status
                await self._fail_episode(series_id, episode_number, "Pipeline did not return result")

        except Exception as e:
            logger.error(
                "Episode pipeline failed for series %s ep %d: %s",
                series_id,
                episode_number,
                e,
                exc_info=True
            )
            await self._fail_episode(series_id, episode_number, str(e))

    async def _fail_episode(
        self,
        series_id: str,
        episode_number: int,
        error: str,
    ) -> None:
        """
        Mark an episode as failed.

        Args:
            series_id: Series ID
            episode_number: Episode number
            error: Error message
        """
        try:
            series_model = await self._get_series_model(series_id)
            if not series_model:
                return

            for ep in series_model.episodes:
                if ep.episode_number == episode_number:
                    ep.status = EpisodeStatus.FAILED.value
                    break

            series_model.updated_at = datetime.utcnow()
            await self.session.commit()
            logger.warning("Episode %d of series %s failed: %s", episode_number, series_id, error)
        except Exception as e:
            logger.error("Failed to mark episode as failed: %s", e)

    async def complete_episode(
        self,
        series_id: str,
        episode_number: int,
        script: Dict[str, Any],
        output_path: str,
        audio_path: str,
        duration_seconds: float
    ) -> EpisodeResponse:
        """
        Mark an episode as complete after generation.

        Called after pipeline completes to:
        1. Generate cliffhanger
        2. Update continuity state
        3. Save episode results

        Args:
            series_id: Series ID
            episode_number: Episode number
            script: Generated script
            output_path: Path to video output
            audio_path: Path to audio output
            duration_seconds: Episode duration

        Returns:
            EpisodeResponse with completed episode
        """
        series_model = await self._get_series_model(series_id)
        if not series_model:
            raise ValueError(f"Series not found: {series_id}")

        # Get episode
        episode_model = None
        for ep in series_model.episodes:
            if ep.episode_number == episode_number:
                episode_model = ep
                break

        if not episode_model:
            raise ValueError(f"Episode {episode_number} not found")

        outline = series_model.outline or {}
        style_dna = series_model.style_dna or {}
        total_episodes = series_model.episode_count

        # Get cliffhanger type from outline
        cliffhanger_type = episode_model.cliffhanger_type
        cliffhanger = None

        if episode_number < total_episodes and cliffhanger_type:
            cliffhanger = await asyncio.to_thread(
                self.episode_linker.generate_cliffhanger,
                script,
                cliffhanger_type,
                episode_number,
                total_episodes
            )

        # Update continuity state
        continuity_state = series_model.continuity_state or create_initial_state()
        episode_outline = None
        for ep in outline.get("episodes", []):
            if ep.get("episode_number") == episode_number:
                episode_outline = ep
                break

        callbacks_planted = episode_outline.get("callbacks_to_plant", []) if episode_outline else []
        callbacks_resolved = episode_outline.get("callbacks_to_resolve", []) if episode_outline else []

        continuity_state = self.continuity_manager.update_state(
            continuity_state,
            episode_number,
            script,
            cliffhanger,
            callbacks_planted,
            callbacks_resolved
        )

        # Update episode model
        episode_model.status = EpisodeStatus.COMPLETED.value
        episode_model.cliffhanger = cliffhanger
        episode_model.script = script
        episode_model.output_path = output_path
        episode_model.audio_path = audio_path
        episode_model.duration_seconds = duration_seconds
        episode_model.completed_at = datetime.utcnow()
        episode_model.callbacks = {
            "planted": callbacks_planted,
            "resolved": callbacks_resolved
        }

        # Update series
        series_model.continuity_state = continuity_state
        series_model.updated_at = datetime.utcnow()

        # Check if series is complete
        all_complete = all(
            ep.status == EpisodeStatus.COMPLETED.value
            for ep in series_model.episodes
        )
        if all_complete:
            series_model.status = SeriesStatus.COMPLETED.value
            series_model.completed_at = datetime.utcnow()

        await self.session.commit()

        return self._episode_model_to_response(episode_model)

    async def get_series(self, series_id: str) -> Optional[SeriesResponse]:
        """Get a series by ID."""
        series_model = await self._get_series_model(series_id)
        if not series_model:
            return None
        return self._model_to_response(series_model)

    async def list_series(
        self,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> SeriesListResponse:
        """List all series with optional filtering."""
        query = select(SeriesModel).order_by(SeriesModel.created_at.desc())

        if status:
            query = query.where(SeriesModel.status == status)

        # Get total count
        count_query = select(SeriesModel)
        if status:
            count_query = count_query.where(SeriesModel.status == status)
        result = await self.session.execute(count_query)
        total = len(result.scalars().all())

        # Paginate
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.session.execute(query)
        series_models = result.scalars().all()

        return SeriesListResponse(
            series=[self._model_to_response(s) for s in series_models],
            total=total,
            page=page,
            page_size=page_size
        )

    async def delete_series(self, series_id: str) -> bool:
        """Delete/cancel a series."""
        series_model = await self._get_series_model(series_id)
        if not series_model:
            return False

        series_model.status = SeriesStatus.CANCELLED.value
        series_model.updated_at = datetime.utcnow()
        await self.session.commit()
        return True

    async def _get_series_model(self, series_id: str) -> Optional[SeriesModel]:
        """Get series model by ID with episodes."""
        result = await self.session.execute(
            select(SeriesModel).where(SeriesModel.id == series_id)
        )
        return result.scalar_one_or_none()

    def _model_to_response(self, model: SeriesModel, episodes_list: List[EpisodeModel] = None) -> SeriesResponse:
        """Convert database model to response."""
        outline = model.outline or {}
        style_dna = model.style_dna or {}

        # Use provided episodes list or try to get from model
        # For newly created models, episodes might not be loaded yet
        try:
            ep_list = episodes_list if episodes_list is not None else list(model.episodes)
        except Exception:
            ep_list = []

        # Build episode responses
        episodes = [
            self._episode_model_to_response(ep)
            for ep in sorted(ep_list, key=lambda e: e.episode_number)
        ]

        # Calculate progress
        completed = sum(1 for ep in ep_list if ep.status == EpisodeStatus.COMPLETED.value)
        progress = (completed / model.episode_count * 100) if model.episode_count else 0

        # Build style DNA response
        music_profile = style_dna.get("music_profile", {})
        voice_profile = style_dna.get("voice_profile", {})

        style_dna_response = StyleDNAResponse(
            era=style_dna.get("era", "modern"),
            genre=style_dna.get("genre", "documentary"),
            geography=style_dna.get("geography"),
            tone=style_dna.get("tone", "engaging"),
            music_style=music_profile.get("mood", ""),
            voice_style=voice_profile.get("style", "")
        )

        # Build outline response
        outline_response = SeriesOutlineResponse(
            title=outline.get("title", model.title or ""),
            description=outline.get("description", model.description or ""),
            episode_count=model.episode_count,
            episode_length=model.episode_length,
            series_type=model.series_type,
            overall_arc=outline.get("overall_arc", ""),
            themes=outline.get("themes", []),
            episodes=[
                EpisodeSummaryResponse(
                    episode_number=ep.get("episode_number", i + 1),
                    title=ep.get("title", ""),
                    premise=ep.get("premise", ""),
                    cliffhanger_type=ep.get("cliffhanger_type"),
                    status=self._get_episode_status(ep_list, ep.get("episode_number", i + 1))
                )
                for i, ep in enumerate(outline.get("episodes", []))
            ],
            style_dna=style_dna_response
        )

        return SeriesResponse(
            id=model.id,
            status=model.status,
            prompt=model.prompt,
            guidance=model.guidance,
            mode=model.mode,
            outline=outline_response,
            episodes=episodes,
            progress_percent=progress,
            assets_generated=model.assets is not None,
            created_at=model.created_at,
            approved_at=model.approved_at,
            completed_at=model.completed_at
        )

    def _episode_model_to_response(self, model: EpisodeModel) -> EpisodeResponse:
        """Convert episode model to response."""
        settings = get_settings()

        # Build URLs if paths exist
        video_url = None
        audio_url = None
        if model.output_path:
            video_url = f"/api/output/{model.output_path}"
        if model.audio_path:
            audio_url = f"/api/output/{model.audio_path}"

        return EpisodeResponse(
            id=model.id,
            series_id=model.series_id,
            episode_number=model.episode_number,
            title=model.title,
            status=model.status,
            job_id=model.job_id,
            previously_on=model.previously_on,
            cliffhanger=model.cliffhanger,
            cliffhanger_type=model.cliffhanger_type,
            output_path=model.output_path,
            audio_path=model.audio_path,
            video_url=video_url,
            audio_url=audio_url,
            duration_seconds=model.duration_seconds,
            created_at=model.created_at,
            completed_at=model.completed_at
        )

    def _get_episode_status(self, episodes: List[EpisodeModel], episode_number: int) -> str:
        """Get status of a specific episode by number."""
        for ep in episodes:
            if ep.episode_number == episode_number:
                return ep.status
        return "pending"
