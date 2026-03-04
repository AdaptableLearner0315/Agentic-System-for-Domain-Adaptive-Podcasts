"""
Pipeline orchestration service.

Wraps the existing Normal and Pro pipelines, handling job execution,
progress tracking, and cancellation.
"""

import asyncio
import sys
from pathlib import Path
from typing import Dict, Optional, Any
import traceback

# Add project root to path for importing existing modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from pipelines.normal_pipeline import NormalPipeline
from pipelines.pro_pipeline import ProPipeline, ProConfig
from utils.progress_stream import ProgressStream
from utils.smart_input_handler import SmartInputHandler, SmartInput

from ..models.enums import JobStatus, PipelineMode, GenerationPhase
from ..models.requests import GenerationRequest
from ..config import get_settings
from .job_manager import JobManager
from .progress_adapter import adapter_manager, ProgressUpdate as AdapterProgressUpdate


class PipelineService:
    """
    Orchestrates pipeline execution.

    Wraps the existing NormalPipeline and ProPipeline classes,
    providing async job execution with progress tracking.

    Attributes:
        output_dir: Directory for output files
        job_manager: JobManager for state updates
        file_service: FileService for resolving uploaded file paths
        _running_tasks: Dictionary of running asyncio tasks
    """

    def __init__(
        self,
        output_dir: Path,
        job_manager: JobManager,
        file_service=None,
    ):
        """
        Initialize the pipeline service.

        Args:
            output_dir: Directory for output files.
            job_manager: JobManager instance for state updates.
            file_service: FileService instance for resolving file paths.
        """
        self.output_dir = output_dir
        self.job_manager = job_manager
        self.file_service = file_service
        self._running_tasks: Dict[str, asyncio.Task] = {}

    # Phase-level timeout defaults (seconds)
    PHASE_TIMEOUTS = {
        "content_prep": 120,     # 2 min for content extraction/generation
        "scripting": 180,        # 3 min for script enhancement + review
        "asset_generation": 360, # 6 min for TTS + BGM + Images
        "mixing": 120,           # 2 min for audio mixing
        "video_assembly": 120,   # 2 min for video assembly
    }

    async def run_job(
        self,
        job_id: str,
        request: GenerationRequest,
    ) -> None:
        """
        Run a generation job.

        This method is called as a background task. It handles the full
        job lifecycle including setup, execution, and cleanup. Uses
        phase-level timeouts instead of a single global timeout to avoid
        killing jobs that are 95% complete.

        Args:
            job_id: Unique job identifier.
            request: Generation request with parameters.
        """
        try:
            # Mark job as running
            self.job_manager.start_job(job_id)

            # Update progress
            await self._update_progress(
                job_id=job_id,
                phase=GenerationPhase.INITIALIZING,
                message="Initializing pipeline...",
                progress_percent=0,
            )

            await self._execute_pipeline(job_id, request)

        except asyncio.CancelledError:
            self.job_manager.cancel_job(job_id)
        except Exception as e:
            traceback.print_exc()
            self.job_manager.fail_job(job_id, str(e))
            await self._update_progress(
                job_id=job_id,
                phase=GenerationPhase.ERROR,
                message=f"Error: {e}",
                progress_percent=0,
            )
        finally:
            # Cleanup
            if job_id in self._running_tasks:
                del self._running_tasks[job_id]

    async def _execute_pipeline(
        self,
        job_id: str,
        request: GenerationRequest,
    ) -> None:
        """
        Execute the pipeline with phase-level timeouts.

        Each phase (content prep, pipeline execution) has its own timeout.
        On timeout, partial results are saved and returned rather than
        losing all progress.

        Args:
            job_id: Unique job identifier.
            request: Generation request with parameters.
        """
        # Phase 1: Prepare content (with timeout)
        try:
            content = await asyncio.wait_for(
                self._prepare_content(job_id, request),
                timeout=self.PHASE_TIMEOUTS["content_prep"],
            )
        except asyncio.TimeoutError:
            self.job_manager.fail_job(
                job_id,
                "Content preparation timed out. Try a smaller input file."
            )
            await self._update_progress(
                job_id=job_id,
                phase=GenerationPhase.ERROR,
                message="Content preparation timed out.",
                progress_percent=5,
            )
            return

        if not content:
            return  # Job failed during preparation

        # Check for cancellation
        if self.job_manager.is_cancellation_requested(job_id):
            self.job_manager.cancel_job(job_id)
            return

        # Phase 2: Run pipeline (with generous timeout for full pipeline)
        pipeline_timeout = (
            self.PHASE_TIMEOUTS["scripting"]
            + self.PHASE_TIMEOUTS["asset_generation"]
            + self.PHASE_TIMEOUTS["mixing"]
            + self.PHASE_TIMEOUTS["video_assembly"]
        )

        try:
            if request.mode == "pro":
                result = await asyncio.wait_for(
                    self._run_pro_pipeline(job_id, content, request),
                    timeout=pipeline_timeout,
                )
            else:
                result = await asyncio.wait_for(
                    self._run_normal_pipeline(job_id, content),
                    timeout=pipeline_timeout,
                )
        except asyncio.TimeoutError:
            timeout_minutes = pipeline_timeout / 60
            error_msg = (
                f"Pipeline timed out after {timeout_minutes:.0f} minutes. "
                f"Partial results may be available in the output directory."
            )
            self.job_manager.fail_job(job_id, error_msg)
            await self._update_progress(
                job_id=job_id,
                phase=GenerationPhase.ERROR,
                message=error_msg,
                progress_percent=0,
            )
            return

        # Check for cancellation
        if self.job_manager.is_cancellation_requested(job_id):
            self.job_manager.cancel_job(job_id)
            return

        # Complete job — accept partial success (output_path present even if not fully successful)
        if result and (result.get("success") or result.get("output_path")):
            self.job_manager.complete_job(job_id, result)
            await self._update_progress(
                job_id=job_id,
                phase=GenerationPhase.COMPLETE,
                message="Generation complete!",
                progress_percent=100,
            )
        else:
            error_msg = result.get("error", "Unknown error") if result else "Pipeline failed"
            self.job_manager.fail_job(job_id, error_msg)

    async def _update_progress(
        self,
        job_id: str,
        phase: GenerationPhase,
        message: str,
        progress_percent: float = 0.0,
        current_step: int = 0,
        total_steps: int = 0,
        eta_seconds: Optional[float] = None,
        preview: Optional[str] = None,
        details: Optional[Dict] = None,
    ) -> None:
        """
        Update progress in both the job manager and the WebSocket adapter.

        Args:
            job_id: Job identifier.
            phase: Current generation phase.
            message: Status message.
            progress_percent: Overall progress (0-100).
            current_step: Current step number.
            total_steps: Total steps.
            eta_seconds: Estimated time remaining.
            preview: Preview content.
            details: Additional details.
        """
        # Update job manager (persisted state)
        self.job_manager.update_progress(
            job_id=job_id,
            phase=phase,
            message=message,
            progress_percent=progress_percent,
            current_step=current_step,
            total_steps=total_steps,
            eta_seconds=eta_seconds,
            preview=preview,
            details=details,
        )

        # Push to WebSocket adapter for real-time streaming
        try:
            adapter = await adapter_manager.get_adapter(job_id)
            adapter_update = AdapterProgressUpdate(
                job_id=job_id,
                phase=phase,
                message=message,
                progress_percent=progress_percent,
                current_step=current_step,
                total_steps=total_steps,
                eta_seconds=eta_seconds,
                preview=preview,
                details=details,
            )
            adapter._queue.put_nowait(adapter_update)
        except Exception:
            pass  # Don't fail pipeline if WebSocket push fails

    async def _prepare_content(
        self,
        job_id: str,
        request: GenerationRequest,
    ) -> Optional[Any]:
        """
        Prepare content for pipeline execution.

        Uses SmartInputHandler to process prompt and/or files.

        Args:
            job_id: Job identifier for progress updates.
            request: Generation request.

        Returns:
            ExtractedContent object or None if preparation fails.
        """
        try:
            await self._update_progress(
                job_id=job_id,
                phase=GenerationPhase.ANALYZING,
                message="Analyzing input...",
                progress_percent=5,
            )

            # Resolve uploaded file paths
            files = []
            if request.file_ids and self.file_service:
                for file_id in request.file_ids:
                    file_path = self.file_service.get_file_path(file_id)
                    if file_path:
                        files.append(str(file_path))

            smart_input = SmartInput(
                prompt=request.prompt,
                files=files,
                guidance=request.guidance,
                target_duration_minutes=request.target_duration_minutes,
            )

            # Process input (sync call wrapped in executor)
            handler = SmartInputHandler()
            length = "standard" if request.mode == "pro" else "short"
            content = await handler.process_async(
                smart_input,
                length=length,
                target_duration_minutes=request.target_duration_minutes
            )

            await self._update_progress(
                job_id=job_id,
                phase=GenerationPhase.ANALYZING,
                message="Content prepared",
                progress_percent=10,
                preview=content.text[:200] if content.text else None,
            )

            return content

        except Exception as e:
            self.job_manager.fail_job(job_id, f"Content preparation failed: {e}")
            return None

    async def _run_normal_pipeline(
        self,
        job_id: str,
        content: Any,
    ) -> Optional[Dict]:
        """
        Run the Normal pipeline.

        Args:
            job_id: Job identifier for progress updates.
            content: Prepared content.

        Returns:
            Pipeline result dictionary.
        """
        try:
            # Get adapter while still in async context (thread-safe for sync callbacks)
            adapter = await adapter_manager.get_adapter(job_id)

            # Create progress callback that feeds both job_manager and adapter
            def progress_callback(update):
                self.job_manager.update_progress(
                    job_id=job_id,
                    phase=GenerationPhase(update.phase.value),
                    message=update.message,
                    progress_percent=update.progress_percent,
                    current_step=update.current_step,
                    total_steps=update.total_steps,
                    eta_seconds=update.eta_seconds,
                    preview=update.preview,
                    details=update.details,
                )
                # Push to WebSocket adapter (on_progress is sync-safe)
                try:
                    adapter.on_progress(update)
                except Exception:
                    pass  # Don't fail pipeline if adapter push fails

            # Create progress stream
            progress = ProgressStream(callback=progress_callback)

            # Run pipeline (use None for output_dir so pipeline uses its default)
            pipeline = NormalPipeline()
            result = await pipeline.run_with_content(content, progress=progress)

            # Convert result to dict
            return {
                "success": result.success,
                "output_path": result.output_path,
                "audio_output_path": result.audio_output_path,
                "script": result.script,
                "tts_files": [
                    {"id": f"tts_{i}", "filename": f.get("filename", ""), "path": f.get("path", ""), "type": "tts"}
                    for i, f in enumerate(result.tts_files)
                ] if result.tts_files else [],
                "bgm_files": [
                    {"id": f"bgm_{i}", "filename": f.get("filename", ""), "path": f.get("path", ""), "type": "bgm"}
                    for i, f in enumerate(result.bgm_files)
                ] if result.bgm_files else [],
                "image_files": [
                    {"id": f"img_{i}", "filename": f.get("filename", ""), "path": f.get("path", ""), "type": "image"}
                    for i, f in enumerate(result.image_files)
                ] if result.image_files else [],
                "duration_seconds": result.duration_seconds,
                "error": result.error,
            }

        except Exception as e:
            traceback.print_exc()
            return {"success": False, "error": str(e)}

    async def _run_pro_pipeline(
        self,
        job_id: str,
        content: Any,
        request: GenerationRequest,
    ) -> Optional[Dict]:
        """
        Run the Pro pipeline.

        Args:
            job_id: Job identifier for progress updates.
            content: Prepared content.
            request: Original request with config.

        Returns:
            Pipeline result dictionary.
        """
        try:
            # Create config
            config = ProConfig()
            if request.config:
                config = ProConfig.from_dict(request.config)

            # Get adapter while still in async context (thread-safe for sync callbacks)
            adapter = await adapter_manager.get_adapter(job_id)

            # Create progress callback that feeds both job_manager and adapter
            def progress_callback(update):
                self.job_manager.update_progress(
                    job_id=job_id,
                    phase=GenerationPhase(update.phase.value),
                    message=update.message,
                    progress_percent=update.progress_percent,
                    current_step=update.current_step,
                    total_steps=update.total_steps,
                    eta_seconds=update.eta_seconds,
                    preview=update.preview,
                    details=update.details,
                )
                # Push to WebSocket adapter (on_progress is sync-safe)
                try:
                    adapter.on_progress(update)
                except Exception:
                    pass  # Don't fail pipeline if adapter push fails

            # Create progress stream
            progress = ProgressStream(callback=progress_callback)

            # Run pipeline (use None for output_dir so pipeline uses its default)
            pipeline = ProPipeline(config=config)
            result = await pipeline.run_with_content(content, progress=progress)

            # Convert result to dict
            return {
                "success": result.success,
                "output_path": result.output_path,
                "audio_output_path": result.audio_output_path,
                "script": result.script,
                "tts_files": [
                    {"id": f"tts_{i}", "filename": f.get("filename", ""), "path": f.get("path", ""), "type": "tts"}
                    for i, f in enumerate(result.tts_files)
                ] if result.tts_files else [],
                "bgm_files": [
                    {"id": f"bgm_{i}", "filename": f.get("filename", ""), "path": f.get("path", ""), "type": "bgm"}
                    for i, f in enumerate(result.bgm_files)
                ] if result.bgm_files else [],
                "image_files": [
                    {"id": f"img_{i}", "filename": f.get("filename", ""), "path": f.get("path", ""), "type": "image"}
                    for i, f in enumerate(result.image_files)
                ] if result.image_files else [],
                "duration_seconds": result.duration_seconds,
                "review_history": result.review_history,
                "config_used": config.to_dict() if config else None,
                "error": result.error,
            }

        except Exception as e:
            traceback.print_exc()
            return {"success": False, "error": str(e)}

    async def cancel_job(self, job_id: str) -> None:
        """
        Cancel a running job.

        Args:
            job_id: Job identifier to cancel.
        """
        self.job_manager.request_cancellation(job_id)

        # Cancel the asyncio task if running
        task = self._running_tasks.get(job_id)
        if task and not task.done():
            task.cancel()
