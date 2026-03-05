"""
Normal Pipeline
Author: Sarath

Fast podcast generation pipeline targeting 60-90 seconds.
Optimizes for speed through:
- Parallel execution of TTS, BGM, and images
- Overlapped audio mixing: starts as soon as TTS + BGM finish,
  runs concurrently with image generation
- Chunk-level TTS (vs sentence-level)
- 3-segment BGM (vs 9-segment daisy-chain)
- 4 images (vs 16)
- No Director review loop
- Unified GENERATING_ASSETS progress phase with per-component sub-progress
- Stage-level timing traces for performance visibility
"""

import asyncio
import json
import uuid
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from config.modes import get_mode_config, NORMAL_BGM_SEGMENTS
from config.llm import MODEL_OPTIONS
from config.paths import OUTPUT_DIR, AUDIO_DIR, TTS_DIR, BGM_DIR, VISUALS_DIR, ensure_directories
from utils.input_router import InputRouter, ExtractedContent
from utils.parallel_executor import (
    TTSParallelExecutor,
    BGMParallelExecutor,
    ImageParallelExecutor,
)
from utils.progress_stream import ProgressStream, GenerationPhase


@dataclass
class NormalPipelineResult:
    """
    Result from Normal pipeline execution.

    Attributes:
        success: Whether the pipeline completed without errors.
        output_path: Path to the final video (or audio if no images).
        audio_output_path: Path to the mixed audio file (MP3).
        script: Enhanced script dictionary, or None on failure.
        tts_files: Per-chunk TTS generation results with paths.
        bgm_files: Per-segment BGM generation results with paths.
        image_files: Per-image generation results with paths.
        duration_seconds: Total wall-clock time of the pipeline run.
        error: Error message if success is False.
    """
    success: bool
    output_path: Optional[str]
    audio_output_path: Optional[str]
    script: Optional[Dict[str, Any]]
    tts_files: List[Dict[str, Any]]
    bgm_files: List[Dict[str, Any]]
    image_files: List[Dict[str, Any]]
    duration_seconds: float
    error: Optional[str] = None


class NormalPipeline:
    """
    Fast podcast generation pipeline.

    Target time: 60-90 seconds

    Optimization strategies:
    1. Parallel TTS generation (10 workers)
    2. Parallel BGM generation (3 segments, 3 workers)
    3. Parallel image generation (4 images, 4 workers)
    4. Overlapped execution: audio mixing starts as soon as TTS + BGM finish,
       running concurrently with image generation instead of waiting for all
       three to complete first
    5. No Director review loop
    6. Simplified script enhancement
    7. Asset library utilization
    8. Unified GENERATING_ASSETS progress phase (avoids phase-fighting)
    """

    def __init__(self, output_dir: Optional[Path] = None, job_id: Optional[str] = None):
        """
        Initialize the Normal Pipeline.

        Args:
            output_dir: Output directory for generated files
            job_id: Unique job identifier for isolating outputs (auto-generated if not provided)
        """
        self.output_dir = Path(output_dir) if output_dir else OUTPUT_DIR
        self.job_id = job_id or str(uuid.uuid4())[:8]
        self.config = get_mode_config("normal")
        self.input_router = InputRouter()

        # Ensure directories exist
        ensure_directories()

        # Shared TTSNarrator instance (avoids re-initializing per chunk)
        self._narrator = None

        # Asset managers (lazy-loaded)
        self._voice_manager = None
        self._music_manager = None
        self._image_manager = None

    @property
    def narrator(self):
        """Lazy-load shared TTSNarrator instance."""
        if self._narrator is None:
            from agents.audio_designer.tts_narrator import TTSNarrator
            self._narrator = TTSNarrator(output_dir=AUDIO_DIR / "tts")
        return self._narrator

    @property
    def voice_manager(self):
        """Lazy-load voice asset manager."""
        if self._voice_manager is None:
            from assets.voice_manager import VoiceAssetManager
            self._voice_manager = VoiceAssetManager()
        return self._voice_manager

    @property
    def music_manager(self):
        """Lazy-load music asset manager."""
        if self._music_manager is None:
            from assets.music_manager import MusicAssetManager
            self._music_manager = MusicAssetManager()
        return self._music_manager

    @property
    def image_manager(self):
        """Lazy-load image asset manager."""
        if self._image_manager is None:
            from assets.image_manager import ImageAssetManager
            self._image_manager = ImageAssetManager()
        return self._image_manager

    @property
    def use_intelligent_bgm(self) -> bool:
        """Check if intelligent BGM system should be used."""
        return self.config.get("bgm", {}).get("use_intelligent", False)

    async def run(
        self,
        input_path: str,
        user_prompt: Optional[str] = None,
        progress: Optional[ProgressStream] = None
    ) -> NormalPipelineResult:
        """
        Run the full Normal pipeline.

        Args:
            input_path: Path to input file (any supported format)
            user_prompt: Optional user context/prompt
            progress: Optional progress stream for updates

        Returns:
            NormalPipelineResult with all outputs
        """
        import time
        start_time = time.time()

        if progress:
            progress.start("Starting fast generation...")

        try:
            # Stage 1: Extract content (5-10s)
            if progress:
                progress.analyzing("Extracting content...")

            content = await self.input_router.extract_async(input_path, user_prompt)
            print(f"[NormalPipeline] Extracted {len(content.text)} characters from {content.source_type}")

            return await self._run_with_content(content, progress, start_time)

        except Exception as e:
            duration = time.time() - start_time
            if progress:
                progress.error(str(e))

            return NormalPipelineResult(
                success=False,
                output_path=None,
                audio_output_path=None,
                script=None,
                tts_files=[],
                bgm_files=[],
                image_files=[],
                duration_seconds=duration,
                error=str(e),
            )

    async def run_with_content(
        self,
        content: ExtractedContent,
        progress: Optional[ProgressStream] = None,
        on_script_ready: Optional[callable] = None
    ) -> NormalPipelineResult:
        """
        Run the pipeline with pre-extracted content.

        This allows the SmartInputHandler to pre-process content
        (generation, extraction, or hybrid) before passing to the pipeline.

        Args:
            content: Pre-extracted/generated content
            progress: Optional progress stream for updates
            on_script_ready: Optional callback called when script is enhanced.
                             Receives (job_id, script_dict) arguments.
                             Used for fire-and-forget trailer generation.

        Returns:
            NormalPipelineResult with all outputs
        """
        import time
        start_time = time.time()

        if progress:
            progress.start("Starting fast generation...")

        print(f"[NormalPipeline] Using pre-processed content: {len(content.text)} characters from {content.source_type}")

        return await self._run_with_content(content, progress, start_time, on_script_ready)

    async def _run_with_content(
        self,
        content: ExtractedContent,
        progress: Optional[ProgressStream],
        start_time: float,
        on_script_ready: Optional[callable] = None
    ) -> NormalPipelineResult:
        """
        Internal method that orchestrates the full pipeline after content extraction.

        Collects per-stage wall-clock timings in ``stage_timings`` and injects
        asset sub-timings (tts, bgm, images, mixing, video_assembly) into the
        progress stream's ``_phase_durations`` so the frontend timing breakdown
        can display them.

        Args:
            content: Extracted content to turn into a podcast.
            progress: Optional progress stream for real-time UI updates.
            start_time: ``time.time()`` captured before content extraction,
                used for total duration calculation.
            on_script_ready: Optional callback called when script is enhanced.
                             Receives (job_id, script_dict) arguments.

        Returns:
            NormalPipelineResult with output paths, script, assets, and timing.
        """
        import time

        try:
            stage_timings = {}

            # Stage 1: Quick script enhancement (25-35s)
            if progress:
                progress.scripting("Enhancing script...")

            t = time.time()
            script = await self._enhance_script_fast(content)
            stage_timings['scripting'] = round(time.time() - t, 1)

            if progress:
                hook_preview = script.get("hook", {}).get("text", "")[:100]
                progress.scripting("Script enhanced!", preview=hook_preview)

            # Fire-and-forget: notify callback that script is ready (for trailer generation)
            if on_script_ready:
                try:
                    on_script_ready(self.job_id, script)
                except Exception as e:
                    print(f"[NormalPipeline] on_script_ready callback failed: {e}")

            # Stage 2+3+4: Assets + Mix + Video (overlapped)
            tts_results, bgm_results, image_results, final_audio, final_video, asset_timings = \
                await self._generate_and_assemble(script, progress)
            stage_timings.update(asset_timings)
            stage_timings['total'] = round(time.time() - start_time, 1)

            duration = time.time() - start_time

            if progress:
                # Inject asset sub-timings into phase_durations for frontend
                for key in ('tts', 'bgm', 'images', 'mixing', 'video_assembly'):
                    if key in stage_timings:
                        progress._phase_durations[key] = stage_timings[key]
                progress.complete(final_video)

            print(f"[NormalPipeline] Stage timings: {stage_timings}")

            return NormalPipelineResult(
                success=True,
                output_path=final_video,
                audio_output_path=final_audio,
                script=script,
                tts_files=tts_results,
                bgm_files=bgm_results,
                image_files=image_results,
                duration_seconds=duration,
            )

        except Exception as e:
            import time as time_module
            duration = time_module.time() - start_time
            if progress:
                progress.error(str(e))

            return NormalPipelineResult(
                success=False,
                output_path=None,
                audio_output_path=None,
                script=None,
                tts_files=[],
                bgm_files=[],
                image_files=[],
                duration_seconds=duration,
                error=str(e),
            )

    async def _enhance_script_fast(
        self,
        content: ExtractedContent
    ) -> Dict[str, Any]:
        """
        Quick script enhancement without Director review.

        Args:
            content: Extracted content

        Returns:
            Enhanced script dictionary
        """
        from agents.script_designer_agent import ScriptDesignerAgent

        # Use model from config
        model = self.config["script"]["model"]
        model_id = MODEL_OPTIONS.get(model, MODEL_OPTIONS["sonnet"])

        enhancer = ScriptDesignerAgent(model=model_id)

        # Get target duration from content metadata (set by SmartInputHandler)
        metadata = content.metadata or {}
        target_duration = metadata.get("target_duration_minutes")
        # Get conversational style flag (set by PipelineService)
        conversational_style = metadata.get("conversational_style", False)

        # Run enhancement in thread pool
        loop = asyncio.get_event_loop()
        script = await loop.run_in_executor(
            None,
            lambda: enhancer.enhance(
                content.text,
                target_duration_minutes=target_duration,
                conversational_style=conversational_style
            )
        )

        # Save script
        script_path = self.output_dir / "enhanced_script.json"
        with open(script_path, 'w') as f:
            json.dump(script, f, indent=2)

        return script

    async def _generate_and_assemble(
        self,
        script: Dict[str, Any],
        progress: Optional[ProgressStream] = None
    ) -> tuple:
        """
        Generate assets with maximum parallelism, overlapping mix with images.

        Execution flow::

            TTS  ──────┐
            BGM  ──────┼→ Mix Audio ──┐
            Images ────────────────────┼→ Video Assembly

        Audio mixing starts as soon as TTS and BGM finish, without waiting
        for images.  Images and mixing then run concurrently, saving 10-15 s
        compared to the previous sequential approach.

        Progress is reported under a single GENERATING_ASSETS phase with
        ``parallel_status`` in details for per-component sub-progress.

        Args:
            script: Enhanced script dictionary with hook, modules, and chunks.
            progress: Optional progress stream for real-time UI updates.

        Returns:
            A 6-tuple of:
                - tts_results: List of TTS generation results.
                - bgm_results: List of BGM generation results.
                - image_results: List of image generation results.
                - final_audio: Path to mixed audio file.
                - final_video: Path to assembled video file.
                - timings: Dict with wall-clock seconds for each sub-stage:
                    ``tts``, ``bgm``, ``images`` (all from t0),
                    ``mixing`` (from mix start), ``video_assembly``.
        """
        import time
        timings = {}

        # Prepare tasks
        tts_tasks = self._prepare_tts_tasks(script)
        bgm_tasks = self._prepare_bgm_tasks(script)
        image_tasks = self._prepare_image_tasks(script)

        # Create executors
        tts_executor = TTSParallelExecutor(max_concurrent=self.config["tts"]["parallel_workers"])
        bgm_executor = BGMParallelExecutor(max_concurrent=3)
        image_executor = ImageParallelExecutor(max_concurrent=self.config["images"]["parallel_workers"])

        # Unified progress tracking for parallel asset generation
        tts_done = 0
        bgm_done = 0
        img_done = 0
        tts_total = len(tts_tasks)
        bgm_total = len(bgm_tasks)
        img_total = len(image_tasks)

        # Track the last completed item per component for preview text
        last_preview = {'tts': '', 'bgm': '', 'images': ''}

        # Track start times for elapsed calculation
        component_start_times = {'tts': None, 'bgm': None, 'images': None}

        def update_asset_progress(component: str, current: int, total: int) -> None:
            """Callback shared by all three executors to emit a single unified progress update.

            Aggregates per-component counts into one GENERATING_ASSETS phase update,
            preventing the phase-fighting that occurred when each executor called
            its own generating_tts/bgm/images method.

            Args:
                component: One of 'tts', 'bgm', or 'images'.
                current: Items completed so far for this component.
                total: Total items for this component (unused — we use the outer totals).
            """
            nonlocal tts_done, bgm_done, img_done
            now = time.time()

            # Initialize start time on first progress update for this component
            if component_start_times[component] is None:
                component_start_times[component] = now

            if component == 'tts':
                tts_done = current
            elif component == 'bgm':
                bgm_done = current
            elif component == 'images':
                img_done = current

            grand_total = tts_total + bgm_total + img_total
            grand_done = tts_done + bgm_done + img_done

            # Build preview text from current component activity
            preview = None
            if component == 'tts' and current <= len(tts_tasks):
                task = tts_tasks[min(current, len(tts_tasks)) - 1] if current > 0 else None
                if task:
                    preview = task.get('text', '')[:80]
                    last_preview['tts'] = preview
            elif component == 'images' and current <= len(image_tasks):
                task = image_tasks[min(current, len(image_tasks)) - 1] if current > 0 else None
                if task:
                    preview = task.get('prompt', '')[:80]
                    last_preview['images'] = preview

            # Calculate elapsed time per component
            def elapsed_for(comp: str) -> float:
                start = component_start_times.get(comp)
                return round(now - start, 1) if start else 0.0

            if progress:
                progress.generating_assets(
                    step=grand_done,
                    total=grand_total,
                    message=f"Generating assets ({grand_done}/{grand_total})",
                    details={
                        'parallel_status': {
                            'tts': {'done': tts_done, 'total': tts_total, 'elapsed_s': elapsed_for('tts')},
                            'bgm': {'done': bgm_done, 'total': bgm_total, 'elapsed_s': elapsed_for('bgm')},
                            'images': {'done': img_done, 'total': img_total, 'elapsed_s': elapsed_for('images')},
                        },
                        'preview': preview or last_preview.get('tts') or last_preview.get('images'),
                    }
                )

        tts_executor.set_progress_callback(
            lambda c, t: update_asset_progress('tts', c, t)
        )
        bgm_executor.set_progress_callback(
            lambda c, t: update_asset_progress('bgm', c, t)
        )
        image_executor.set_progress_callback(
            lambda c, t: update_asset_progress('images', c, t)
        )

        # Launch all three as independent tasks
        t0 = time.time()
        if progress:
            progress.generating_assets(
                step=0,
                total=tts_total + bgm_total + img_total,
                message="Generating assets..."
            )

        tts_task = asyncio.create_task(
            tts_executor.generate_batch(tts_tasks, self._generate_tts_chunk)
        )
        bgm_task = asyncio.create_task(
            bgm_executor.generate_batch(bgm_tasks, self._generate_bgm_segment)
        )
        image_task = asyncio.create_task(
            image_executor.generate_batch(image_tasks, self._generate_image)
        )

        # Wait for TTS + BGM (mixing doesn't need images)
        tts_results, bgm_results = await asyncio.gather(tts_task, bgm_task)
        timings['tts'] = round(time.time() - t0, 1)
        timings['bgm'] = round(time.time() - t0, 1)

        # Start mixing immediately (images may still be generating)
        if progress:
            progress.mixing_audio("Mixing audio...")
        mix_start = time.time()
        mix_task = asyncio.create_task(self._mix_audio(tts_results, bgm_results))

        # Wait for BOTH images and mix to complete (in parallel)
        image_results, final_audio = await asyncio.gather(image_task, mix_task)
        timings['images'] = round(time.time() - t0, 1)
        timings['mixing'] = round(time.time() - mix_start, 1)

        # Cleanup executors
        tts_executor.shutdown()
        bgm_executor.shutdown()
        image_executor.shutdown()

        # Video assembly (needs both audio + images)
        if progress:
            progress.assembling_video("Creating video...")
        video_start = time.time()
        try:
            final_video = await self._assemble_video(final_audio, image_results, self.job_id)
        except Exception as video_err:
            print(f"[NormalPipeline] Video assembly failed, returning audio: {video_err}")
            final_video = final_audio
        timings['video_assembly'] = round(time.time() - video_start, 1)

        return tts_results, bgm_results, image_results, final_audio, final_video, timings

    def _prepare_tts_tasks(self, script: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Prepare TTS tasks (chunk-level for speed)."""
        tasks = []

        # Hook as single chunk
        hook = script.get("hook", {})
        if hook.get("text"):
            tasks.append({
                "id": "hook",
                "text": hook["text"],
                "filename": "hook",
                "section": "hook",
            })

        # Each module as chunks
        for module in script.get("modules", []):
            module_id = module.get("id", 0)
            for chunk_idx, chunk in enumerate(module.get("chunks", [])):
                if chunk.get("text"):
                    tasks.append({
                        "id": f"module_{module_id}_chunk_{chunk_idx}",
                        "text": chunk["text"],
                        "filename": f"module_{module_id}_chunk_{chunk_idx + 1}",
                        "section": f"module_{module_id}",
                        "emotion": chunk.get("emotion", "neutral"),
                    })

        return tasks

    def _extract_emotions_from_script(self, script: Dict[str, Any]) -> List[str]:
        """Extract emotion timeline from script for BGM selection."""
        emotions = []
        if script.get("hook", {}).get("emotion"):
            emotions.append(script["hook"]["emotion"])

        for module in script.get("modules", []):
            for chunk in module.get("chunks", []):
                if chunk.get("emotion"):
                    emotions.append(chunk["emotion"])

        return emotions if emotions else ["neutral"]

    async def _generate_bgm_intelligent(self, script: Dict[str, Any]) -> Optional[str]:
        """
        Generate BGM using the Music Intelligence System.

        Uses emotion-aware track selection and intelligent crossfades for
        a more cohesive soundtrack. Falls back to existing stem mixing
        or API generation if MusicIntelligence fails.

        Args:
            script: Enhanced script dictionary with emotions per chunk.

        Returns:
            Path to the generated BGM file, or None if generation failed.
        """
        try:
            from agents.music_intelligence import MusicIntelligence

            print("[NormalPipeline] Using Music Intelligence System for BGM")
            mi = MusicIntelligence(mode="normal")

            # Extract emotion timeline from script
            timeline = mi.extract_emotion_timeline(script)

            if not timeline:
                print("[NormalPipeline] No emotion timeline extracted, using fallback")
                return None

            print(f"[NormalPipeline] Extracted {len(timeline)} emotion segments")

            # Compose BGM using Normal mode (fast track selection)
            bgm_path = mi.compose_for_normal(timeline)

            if bgm_path and Path(bgm_path).exists():
                print(f"[NormalPipeline] Music Intelligence generated BGM: {bgm_path}")
                return bgm_path
            else:
                print("[NormalPipeline] Music Intelligence returned invalid path")
                return None

        except ImportError as e:
            print(f"[NormalPipeline] Music Intelligence not available: {e}")
            return None
        except Exception as e:
            print(f"[NormalPipeline] Music Intelligence failed, using fallback: {e}")
            return None

    def _generate_bgm_fallback(
        self,
        script: Dict[str, Any],
        emotions: List[str],
        output_filename: str
    ) -> Optional[str]:
        """
        Fallback BGM generation using stems or API.

        Called when Music Intelligence System is disabled or fails.

        Args:
            script: Enhanced script dictionary.
            emotions: List of emotions extracted from script.
            output_filename: Output filename for the generated BGM.

        Returns:
            Path to the generated BGM file, or None if generation failed.
        """
        # Try stem mixing first (MUCH faster: 2-5s vs 20-30s)
        if self.config["bgm"]["use_stems"] and self.music_manager.has_stems():
            return self._mix_bgm_from_stems(emotions, output_filename)

        # Fall back to API generation
        from agents.audio_designer.bgm_generator import BGMGenerator
        generator = BGMGenerator(output_dir=AUDIO_DIR / "bgm")

        # Generate first segment as representative BGM
        seg_config = NORMAL_BGM_SEGMENTS.get(1, {})
        emotion = emotions[0] if emotions else "neutral"
        return generator.generate_bgm(
            emotion,
            output_filename,
            seg_config.get("duration", 30)
        )

    def _prepare_bgm_tasks(self, script: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Prepare BGM tasks - use intelligent system, stems, or API generation.

        Priority order:
        1. Music Intelligence System (if use_intelligent=True in config)
        2. Pre-generated stems (if use_stems=True and stems available)
        3. API generation (fallback)
        """
        emotions = self._extract_emotions_from_script(script)

        # Check if Music Intelligence System should be used
        if self.use_intelligent_bgm:
            print("[NormalPipeline] Music Intelligence enabled, using intelligent BGM task")
            # Return a single task that will use the intelligent system
            return [{
                "id": "bgm_intelligent",
                "segment_id": 0,  # Special marker for intelligent system
                "filename": "bgm_intelligent",
                "emotions": emotions,
                "use_intelligent": True,
                "script": script,  # Pass script for emotion timeline extraction
            }]

        # Check if we should use pre-generated stems (MUCH faster: 2-5s vs 20-30s)
        if self.config["bgm"]["use_stems"] and self.music_manager.has_stems():
            stem_count = self.music_manager.get_available_stem_count()
            print(f"[NormalPipeline] Using pre-generated stems ({stem_count} available)")

            # Return a single task that will mix stems locally
            return [{
                "id": "bgm_stems",
                "segment_id": 0,  # Special marker for stem mixing
                "filename": "bgm_from_stems",
                "emotions": emotions,
                "use_stems": True,
            }]

        # Fall back to API generation (3 segments)
        print("[NormalPipeline] No stems available, using API generation")
        tasks = []
        for seg_id, seg_config in NORMAL_BGM_SEGMENTS.items():
            emotion_idx = (seg_id - 1) * (len(emotions) // 3) if emotions else 0
            emotion = emotions[emotion_idx] if emotion_idx < len(emotions) else "neutral"

            tasks.append({
                "id": f"bgm_{seg_id}",
                "segment_id": seg_id,
                "filename": f"segment_{seg_id}_{seg_config['name'].lower()}",
                "emotion": emotion,
                "duration": seg_config["duration"],
                "prompt": seg_config["prompt"],
            })

        return tasks

    def _prepare_image_tasks(self, script: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Prepare image tasks based on config count."""
        tasks = []
        image_count = self.config["images"]["count"]

        # Collect visual cues
        visual_cues = []

        # Hook visual
        hook_keywords = script.get("hook", {}).get("keywords", [])
        if hook_keywords:
            visual_cues.append(" ".join(hook_keywords[:3]))

        # Module visuals (one per module)
        for module in script.get("modules", []):
            for chunk in module.get("chunks", []):
                cues = chunk.get("visual_cues", [])
                if cues:
                    visual_cues.append(cues[0])
                    break

        # Take configured number of cues
        for i, cue in enumerate(visual_cues[:image_count]):
            tasks.append({
                "id": f"image_{i}",
                "prompt": cue + ", cinematic photography, documentary style, photorealistic, film grain",
                "filename": f"image_{i + 1}",
            })

        return tasks

    def _generate_tts_chunk(self, text: str, filename: str) -> Optional[str]:
        """Generate TTS for a single chunk - with caching if enabled."""
        # Check cache first if asset library is enabled
        if self.config["tts"]["use_asset_library"]:
            cached = self.voice_manager.get_phrase_path(text)
            if cached:
                print(f"    [TTS Cache HIT] {text[:40]}...")
                return cached

        # Generate new audio
        path = self.narrator.generate_speech(text, filename)

        # Cache for future use if enabled
        if path and self.config["tts"]["use_asset_library"]:
            self.voice_manager.add_to_cache(text, path)

        return path

    def _generate_bgm_segment(
        self,
        emotion: str,
        output_filename: str,
        duration: int,
        **kwargs
    ) -> Optional[str]:
        """
        Generate BGM segment - via intelligent system, stems, or API.

        Args:
            emotion: Primary emotion for BGM generation.
            output_filename: Output filename for the generated BGM.
            duration: Duration in seconds for API-generated BGM.
            **kwargs: Additional arguments including:
                - use_intelligent: Use Music Intelligence System
                - use_stems: Use pre-generated stem mixing
                - emotions: List of emotions for stem selection
                - script: Script dict for intelligent system

        Returns:
            Path to the generated BGM file, or None if generation failed.
        """
        # Check if this is a Music Intelligence task
        if kwargs.get("use_intelligent"):
            script = kwargs.get("script", {})
            emotions = kwargs.get("emotions", [emotion])

            # Run intelligent generation synchronously (it's designed to be fast)
            import asyncio
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # We're already in an async context, run directly
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(self._run_intelligent_bgm_sync, script)
                    bgm_path = future.result()
            else:
                bgm_path = loop.run_until_complete(
                    self._generate_bgm_intelligent(script)
                )

            # If intelligent system succeeded, return the path
            if bgm_path:
                return bgm_path

            # Fall back to existing approaches
            print("[NormalPipeline] Intelligent BGM failed, trying fallback")
            return self._generate_bgm_fallback(script, emotions, output_filename)

        # Check if this is a stem-mixing task
        if kwargs.get("use_stems"):
            return self._mix_bgm_from_stems(
                kwargs.get("emotions", [emotion]),
                output_filename
            )

        # Standard API generation
        from agents.audio_designer.bgm_generator import BGMGenerator
        generator = BGMGenerator(output_dir=AUDIO_DIR / "bgm")
        return generator.generate_bgm(emotion, output_filename, duration)

    def _run_intelligent_bgm_sync(self, script: Dict[str, Any]) -> Optional[str]:
        """
        Synchronous wrapper for intelligent BGM generation.

        Used when running from within an async context where we need
        to execute the intelligent system in a thread pool.

        Args:
            script: Enhanced script dictionary.

        Returns:
            Path to generated BGM file, or None if failed.
        """
        try:
            from agents.music_intelligence import MusicIntelligence

            mi = MusicIntelligence(mode="normal")
            timeline = mi.extract_emotion_timeline(script)

            if not timeline:
                return None

            bgm_path = mi.compose_for_normal(timeline)

            if bgm_path and Path(bgm_path).exists():
                return bgm_path
            return None

        except Exception as e:
            print(f"[NormalPipeline] Sync intelligent BGM failed: {e}")
            return None

    def _mix_bgm_from_stems(
        self,
        emotions: List[str],
        output_filename: str
    ) -> Optional[str]:
        """Mix pre-generated stems into a single BGM track (2-5s vs 20-30s API)."""
        import time
        start = time.time()

        # Select best stems for the emotion timeline
        stems = self.music_manager.select_stems_for_emotions(emotions)

        # Check we have at least some stems
        valid_stems = {k: v for k, v in stems.items() if v}
        if not valid_stems:
            print("[NormalPipeline] No valid stems found, falling back to empty")
            return None

        print(f"[NormalPipeline] Selected stems: {list(valid_stems.keys())}")

        # Mix stems locally
        output_dir = AUDIO_DIR / "bgm"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = str(output_dir / f"{output_filename}.wav")

        result = self.music_manager.mix_stems(stems, output_path)

        elapsed = time.time() - start
        print(f"[NormalPipeline] Stem mixing completed in {elapsed:.1f}s")

        return result

    def _generate_image(self, prompt: str, filename: str) -> Optional[str]:
        """Generate a single image."""
        import fal_client
        import requests

        # Include job_id in path to avoid overwriting images from other jobs
        output_dir = VISUALS_DIR / "normal_mode" / self.job_id
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{filename}.png"

        try:
            result = fal_client.subscribe(
                "fal-ai/flux/dev",
                arguments={
                    "prompt": prompt,
                    "image_size": "landscape_16_9",
                    "num_images": 1,
                },
                with_logs=False
            )

            images = result.get("images", [])
            if images:
                image_url = images[0].get("url")
                if image_url:
                    response = requests.get(image_url)
                    with open(output_path, 'wb') as f:
                        f.write(response.content)
                    return str(output_path)

        except Exception as e:
            print(f"[NormalPipeline] Image generation error: {e}")

        return None

    async def _mix_audio(
        self,
        tts_results: List[Dict[str, Any]],
        bgm_results: List[Dict[str, Any]]
    ) -> str:
        """Mix TTS and BGM into final audio."""
        from agents.audio_designer.audio_mixer import AudioMixer

        mixer = AudioMixer()

        # Filter successful results and adapt to mixer's expected format
        tts_files = []
        for r in tts_results:
            if not r.get("path"):
                continue
            entry = dict(r)
            task_id = r.get("id", "")
            section = r.get("section", "")
            if section == "hook" or task_id == "hook":
                entry["type"] = "hook_sentence"
                entry.setdefault("sentence_idx", 0)
            else:
                entry["type"] = "chunk_sentence"
                # Parse module_id and chunk_idx from id like "module_1_chunk_2"
                parts = task_id.split("_")
                try:
                    entry["module_id"] = int(parts[1]) if len(parts) > 1 else 1
                    entry["chunk_idx"] = int(parts[3]) if len(parts) > 3 else 0
                except (ValueError, IndexError):
                    entry["module_id"] = 1
                    entry["chunk_idx"] = 0
                entry.setdefault("sentence_idx", 0)
            tts_files.append(entry)

        bgm_files = []
        for r in bgm_results:
            if not r.get("path"):
                continue
            entry = dict(r)
            # Parse module_id from segment_id (segment 1->hook area, 2->module 1, 3->module 2, etc.)
            seg_id = r.get("segment_id", 1)
            entry["module_id"] = seg_id
            bgm_files.append(entry)

        # Run mixing in thread pool
        loop = asyncio.get_event_loop()
        output_path = await loop.run_in_executor(
            None,
            lambda: mixer.mix_podcast_sentence_level(
                tts_files,
                bgm_files,
                output_filename="final_normal_mode"
            )
        )

        return output_path

    async def _assemble_video(
        self,
        audio_path: str,
        image_results: List[Dict[str, Any]],
        job_id: Optional[str] = None
    ) -> str:
        """Assemble final video from audio and images."""
        from utils.video_assembler import create_podcast_video

        # Filter successful images
        images = [r.get("path") for r in image_results if r.get("path")]

        if not images:
            # Return audio-only path
            return audio_path

        # Include job_id in path to avoid overwriting videos from other jobs
        job_suffix = job_id or self.job_id
        output_dir = VISUALS_DIR / "normal_mode" / job_suffix
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"final_podcast_{job_suffix}.mp4"

        # Run assembly in thread pool (single-pass, no Ken Burns for speed)
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: create_podcast_video(
                audio_path,
                images,
                str(output_path),
                crossfade_duration=0.5,
                use_ken_burns=False,
                fps=24,
                quality="fast",
            )
        )

        return str(output_path)


def run_normal_pipeline(
    input_path: str,
    user_prompt: Optional[str] = None,
    show_progress: bool = True,
    job_id: Optional[str] = None
) -> NormalPipelineResult:
    """
    Convenience function to run the Normal pipeline.

    Args:
        input_path: Input file path
        user_prompt: Optional user context
        show_progress: Show progress in console
        job_id: Optional job ID for isolating outputs (auto-generated if not provided)

    Returns:
        NormalPipelineResult
    """
    from utils.progress_stream import print_progress

    pipeline = NormalPipeline(job_id=job_id)
    progress = None

    if show_progress:
        progress = ProgressStream(callback=print_progress)

    return asyncio.run(pipeline.run(input_path, user_prompt, progress))


__all__ = ['NormalPipeline', 'NormalPipelineResult', 'run_normal_pipeline']
