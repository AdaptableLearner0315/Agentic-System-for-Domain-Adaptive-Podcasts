"""
Pro Pipeline
Author: Sarath

High-quality podcast generation pipeline targeting 5-8 minutes.
Provides full customization and quality features:
- Director review loop
- Sentence-level TTS with emotion-responsive voice
- 9-segment daisy-chain BGM
- 16 narrative images with emotion alignment
- Full voice styling
- VAD-based ducking
- Multi-speaker support
- Emotion validation
"""

import asyncio
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field

from config.modes import get_mode_config
from config.llm import MODEL_OPTIONS
from config.paths import OUTPUT_DIR, AUDIO_DIR, TTS_DIR, BGM_DIR, VISUALS_DIR, ensure_directories
from utils.input_router import InputRouter, ExtractedContent
from utils.parallel_executor import TTSParallelExecutor
from utils.progress_stream import ProgressStream, GenerationPhase
from utils.quality_evaluator import QualityEvaluator
from utils.evaluation_store import EvaluationStore, get_evaluation_store
from utils.quality_trace import QualityTraceReport


@dataclass
class ProConfig:
    """
    Configuration for Pro pipeline customization.

    Pro mode is optimized for balanced quality/speed (~2-3 min):
    - No director review loop (1 enhancement pass)
    - 8 images instead of 16
    - 5 BGM segments instead of 9
    - Simple ducking instead of VAD-based
    """
    # Script settings
    director_review: bool = False  # Skip review for speed
    max_review_rounds: int = 0
    approval_threshold: int = 7

    # Voice settings
    voice_preset: str = "default"
    apply_voice_styles: bool = True  # Basic voice styling
    custom_pronunciations: Dict[str, str] = field(default_factory=dict)

    # Music settings
    music_genre: str = "cinematic"
    bgm_segments: int = 5  # Reduced from 9
    daisy_chain: bool = False  # Parallel for speed
    bgm_intelligent: bool = True  # Use Music Intelligence System for BGM

    # Image settings
    image_count: int = 8  # Reduced from 16
    image_style: str = "cinematic"

    # Quality settings
    tts_sentence_level: bool = True
    vad_ducking: bool = False  # Simple ducking for speed

    # Speaker settings
    speaker_format: str = "auto"  # auto, single, interview, co_hosts, narrator_characters
    manual_speakers: Optional[Dict[str, str]] = None
    voice_overrides: Optional[Dict[str, str]] = None

    # Emotion settings
    emotion_voice_sync: bool = True
    emotion_image_alignment: bool = True
    emotion_validation: bool = True

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProConfig':
        """Create config from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            'director_review': self.director_review,
            'max_review_rounds': self.max_review_rounds,
            'approval_threshold': self.approval_threshold,
            'voice_preset': self.voice_preset,
            'apply_voice_styles': self.apply_voice_styles,
            'custom_pronunciations': self.custom_pronunciations,
            'music_genre': self.music_genre,
            'bgm_segments': self.bgm_segments,
            'daisy_chain': self.daisy_chain,
            'bgm_intelligent': self.bgm_intelligent,
            'image_count': self.image_count,
            'image_style': self.image_style,
            'tts_sentence_level': self.tts_sentence_level,
            'vad_ducking': self.vad_ducking,
            'speaker_format': self.speaker_format,
            'manual_speakers': self.manual_speakers,
            'voice_overrides': self.voice_overrides,
            'emotion_voice_sync': self.emotion_voice_sync,
            'emotion_image_alignment': self.emotion_image_alignment,
            'emotion_validation': self.emotion_validation,
        }


@dataclass
class UltraConfig:
    """
    Configuration for Ultra pipeline customization.

    Ultra mode provides premium quality (~5-8 min):
    - Full 3-round director review loop
    - 16 narrative images with emotion alignment
    - 9-segment daisy-chain BGM
    - VAD-based ducking
    - Full voice styling
    """
    # Script settings
    director_review: bool = True  # Full review loop
    max_review_rounds: int = 3
    approval_threshold: int = 7

    # Voice settings
    voice_preset: str = "default"
    apply_voice_styles: bool = True  # Full 5-persona voice styling
    custom_pronunciations: Dict[str, str] = field(default_factory=dict)

    # Music settings
    music_genre: str = "cinematic"
    bgm_segments: int = 9  # Full daisy-chain
    daisy_chain: bool = True
    bgm_intelligent: bool = True

    # Image settings
    image_count: int = 16  # Full 16 narrative images
    image_style: str = "cinematic"

    # Quality settings
    tts_sentence_level: bool = True
    vad_ducking: bool = True  # Full VAD-based ducking

    # Speaker settings
    speaker_format: str = "auto"
    manual_speakers: Optional[Dict[str, str]] = None
    voice_overrides: Optional[Dict[str, str]] = None

    # Emotion settings
    emotion_voice_sync: bool = True
    emotion_image_alignment: bool = True
    emotion_validation: bool = True

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UltraConfig':
        """Create config from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            'director_review': self.director_review,
            'max_review_rounds': self.max_review_rounds,
            'approval_threshold': self.approval_threshold,
            'voice_preset': self.voice_preset,
            'apply_voice_styles': self.apply_voice_styles,
            'custom_pronunciations': self.custom_pronunciations,
            'music_genre': self.music_genre,
            'bgm_segments': self.bgm_segments,
            'daisy_chain': self.daisy_chain,
            'bgm_intelligent': self.bgm_intelligent,
            'image_count': self.image_count,
            'image_style': self.image_style,
            'tts_sentence_level': self.tts_sentence_level,
            'vad_ducking': self.vad_ducking,
            'speaker_format': self.speaker_format,
            'manual_speakers': self.manual_speakers,
            'voice_overrides': self.voice_overrides,
            'emotion_voice_sync': self.emotion_voice_sync,
            'emotion_image_alignment': self.emotion_image_alignment,
            'emotion_validation': self.emotion_validation,
        }


@dataclass
class ProPipelineResult:
    """Result from Pro pipeline execution."""
    success: bool
    output_path: Optional[str]
    audio_output_path: Optional[str]
    script: Optional[Dict[str, Any]]
    review_history: List[Dict[str, Any]]
    tts_files: List[Dict[str, Any]]
    bgm_files: List[Dict[str, Any]]
    image_files: List[Dict[str, Any]]
    duration_seconds: float
    config_used: Optional[ProConfig] = None
    error: Optional[str] = None
    quality_report: Optional[Dict[str, Any]] = None


def _update_quality_dimension(
    evaluator: 'QualityEvaluator',
    progress: Optional['ProgressStream'],
    dimension: str,
    metrics,
    job_id: str,
    store: Optional['EvaluationStore'] = None
) -> None:
    """
    Helper to update progress stream with quality score and trace for a dimension.

    Builds a full QualityTrace with reasoning, strengths, weaknesses, and
    persists to SQLite for observability.

    Args:
        evaluator: QualityEvaluator instance for trace building
        progress: Optional progress stream for real-time updates
        dimension: Quality dimension name (script, voice, bgm, etc.)
        metrics: Metrics object with score() method and issues list
        job_id: Job identifier for trace storage
        store: Optional EvaluationStore instance (uses global if not provided)
    """
    if not hasattr(metrics, 'score'):
        return

    # Build full trace with reasoning
    trace_builder = {
        'script': evaluator.build_script_trace,
        'voice': evaluator.build_voice_trace,
        'pacing': evaluator.build_pacing_trace,
        'bgm': evaluator.build_bgm_trace,
        'audio_mix': evaluator.build_audio_mix_trace,
        'video': evaluator.build_video_trace,
        'ending': evaluator.build_ending_trace,
    }

    trace = None
    if dimension in trace_builder:
        try:
            trace = trace_builder[dimension]()
        except Exception as e:
            print(f"[Pipeline] Warning: Failed to build {dimension} trace: {e}")

    score = int(metrics.score())
    grade = evaluator.metrics.get_grade(score)
    issues = getattr(metrics, 'issues', [])

    # Update progress stream with full trace
    if progress:
        if trace:
            progress.update_quality_trace(dimension, trace.to_dict())
        else:
            progress.update_quality_dimension(dimension, score, grade, 'complete', issues)

        # Add any issues to the overall list
        for issue in issues:
            progress.add_quality_issue(f"[{dimension}] {issue}")

    # Persist trace to SQLite
    if trace:
        try:
            eval_store = store or get_evaluation_store()
            eval_store.save_trace(job_id, trace)

            # Also persist issues
            for issue in issues:
                severity = "error" if any(w in issue.lower() for w in ["fail", "error", "missing"]) else "warning"
                eval_store.add_issue(job_id, dimension, severity, issue)
        except Exception as e:
            print(f"[Pipeline] Warning: Failed to persist {dimension} trace: {e}")


class ProPipeline:
    """
    High-quality podcast generation pipeline.

    Target time: 5-8 minutes

    Features:
    - Full Director review loop
    - Sentence-level TTS for precision
    - 9-segment daisy-chain BGM
    - 16 narrative-driven images
    - Module-specific voice styling
    - VAD-based ducking
    - Full customization via ProConfig
    """

    def __init__(
        self,
        config: Optional[ProConfig] = None,
        output_dir: Optional[Path] = None
    ):
        """
        Initialize the Pro Pipeline.

        Args:
            config: Pro configuration (uses defaults if not provided)
            output_dir: Output directory for generated files
        """
        self.config = config or ProConfig()
        self.output_dir = Path(output_dir) if output_dir else OUTPUT_DIR
        self.mode_config = get_mode_config("pro")
        self.input_router = InputRouter()

        # Ensure directories exist
        ensure_directories()

        # Quality evaluator (created during run())
        self._evaluator = None
        self._job_id = None  # Set during run

        # Evaluation store for trace persistence
        self._eval_store = None

    def _ensure_eval_store(self) -> EvaluationStore:
        """Ensure evaluation store exists, creating if needed."""
        if self._eval_store is None:
            self._eval_store = get_evaluation_store()
        return self._eval_store

    def _ensure_evaluator(self, job_id: str) -> QualityEvaluator:
        """Ensure quality evaluator exists, creating if needed."""
        if self._evaluator is None or self._job_id != job_id:
            self._evaluator = QualityEvaluator(
                job_id=job_id,
                output_dir=self.output_dir
            )
            self._job_id = job_id
        return self._evaluator

    async def _evaluate_script_quality(
        self,
        script: Dict[str, Any],
        job_id: str,
        progress: Optional[ProgressStream]
    ) -> None:
        """Evaluate script quality immediately after enhancement."""
        evaluator = self._ensure_evaluator(job_id)
        store = self._ensure_eval_store()
        if progress:
            progress.set_quality_evaluating('script')
        loop = asyncio.get_event_loop()
        metrics = await loop.run_in_executor(
            None, lambda: evaluator.analyze_script(script)
        )
        _update_quality_dimension(evaluator, progress, 'script', metrics, job_id, store)

    async def _evaluate_voice_quality(
        self,
        tts_results: List[Dict[str, Any]],
        job_id: str,
        progress: Optional[ProgressStream]
    ) -> None:
        """Evaluate voice and pacing quality after TTS completes."""
        evaluator = self._ensure_evaluator(job_id)
        store = self._ensure_eval_store()
        loop = asyncio.get_event_loop()

        # Evaluate voice
        if progress:
            progress.set_quality_evaluating('voice')
        voice_metrics = await loop.run_in_executor(
            None, lambda: evaluator.analyze_voice(tts_results)
        )
        _update_quality_dimension(evaluator, progress, 'voice', voice_metrics, job_id, store)

        # Evaluate pacing
        if progress:
            progress.set_quality_evaluating('pacing')
        pacing_metrics = await loop.run_in_executor(
            None, lambda: evaluator.analyze_pacing(tts_results, None)
        )
        _update_quality_dimension(evaluator, progress, 'pacing', pacing_metrics, job_id, store)

    async def _evaluate_bgm_quality(
        self,
        bgm_results: List[Dict[str, Any]],
        job_id: str,
        progress: Optional[ProgressStream]
    ) -> None:
        """Evaluate BGM quality after BGM generation completes."""
        evaluator = self._ensure_evaluator(job_id)
        store = self._ensure_eval_store()
        if progress:
            progress.set_quality_evaluating('bgm')
        loop = asyncio.get_event_loop()
        metrics = await loop.run_in_executor(
            None, lambda: evaluator.analyze_bgm(bgm_results, None)
        )
        _update_quality_dimension(evaluator, progress, 'bgm', metrics, job_id, store)

    async def _evaluate_audio_quality(
        self,
        script: Dict[str, Any],
        final_audio: str,
        job_id: str,
        progress: Optional[ProgressStream]
    ) -> None:
        """Evaluate audio mix, ending, and duration after mixing."""
        if not final_audio:
            return

        evaluator = self._ensure_evaluator(job_id)
        store = self._ensure_eval_store()
        loop = asyncio.get_event_loop()

        # Evaluate audio mix
        if progress:
            progress.set_quality_evaluating('audio_mix')
        audio_mix_metrics = await loop.run_in_executor(
            None, lambda: evaluator.analyze_audio_mix(final_audio)
        )
        _update_quality_dimension(evaluator, progress, 'audio_mix', audio_mix_metrics, job_id, store)

        # Evaluate ending
        if progress:
            progress.set_quality_evaluating('ending')
        ending_metrics = await loop.run_in_executor(
            None, lambda: evaluator.analyze_ending(final_audio)
        )
        _update_quality_dimension(evaluator, progress, 'ending', ending_metrics, job_id, store)

    async def _evaluate_video_quality(
        self,
        final_video: str,
        final_audio: str,
        image_results: List[Dict[str, Any]],
        job_id: str,
        progress: Optional[ProgressStream]
    ) -> None:
        """Evaluate video quality after video assembly."""
        if not final_video or final_video == final_audio:
            return

        evaluator = self._ensure_evaluator(job_id)
        store = self._ensure_eval_store()
        if progress:
            progress.set_quality_evaluating('video')
        loop = asyncio.get_event_loop()
        metrics = await loop.run_in_executor(
            None, lambda: evaluator.analyze_video(final_video, image_results)
        )
        _update_quality_dimension(evaluator, progress, 'video', metrics, job_id, store)

    async def run(
        self,
        input_path: str,
        user_prompt: Optional[str] = None,
        progress: Optional[ProgressStream] = None
    ) -> ProPipelineResult:
        """
        Run the full Pro pipeline.

        Args:
            input_path: Path to input file
            user_prompt: Optional user context
            progress: Optional progress stream

        Returns:
            ProPipelineResult with all outputs
        """
        import time
        start_time = time.time()

        # Set Pro mode first so duration hints are correct
        if progress:
            progress.set_mode("pro")
            progress.start("Starting high-quality generation...")

        try:
            # Stage 1: Extract content
            if progress:
                progress.analyzing("Extracting content...")

            content = await self.input_router.extract_async(input_path, user_prompt)
            print(f"[ProPipeline] Extracted {len(content.text)} characters")

            return await self._run_with_content(content, progress, start_time)

        except Exception as e:
            duration = time.time() - start_time
            if progress:
                progress.error(str(e))

            return ProPipelineResult(
                success=False,
                output_path=None,
                audio_output_path=None,
                script=None,
                review_history=[],
                tts_files=[],
                bgm_files=[],
                image_files=[],
                duration_seconds=duration,
                config_used=self.config,
                error=str(e),
            )

    async def run_with_content(
        self,
        content: ExtractedContent,
        progress: Optional[ProgressStream] = None,
        on_script_ready: Optional[callable] = None,
        trailer_image_path: Optional[str] = None
    ) -> ProPipelineResult:
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
            trailer_image_path: Optional path to trailer image to reuse as
                                first image for visual consistency.

        Returns:
            ProPipelineResult with all outputs
        """
        import time
        start_time = time.time()

        # Set Pro mode first so duration hints are correct
        if progress:
            progress.set_mode("pro")
            progress.start("Starting high-quality generation...")

        print(f"[ProPipeline] Using pre-processed content: {len(content.text)} characters from {content.source_type}")

        return await self._run_with_content(content, progress, start_time, on_script_ready, trailer_image_path)

    async def _run_with_content(
        self,
        content: ExtractedContent,
        progress: Optional[ProgressStream],
        start_time: float,
        on_script_ready: Optional[callable] = None,
        trailer_image_path: Optional[str] = None
    ) -> ProPipelineResult:
        """
        Internal method to run pipeline with content.

        Args:
            content: Extracted content
            progress: Progress stream
            start_time: Pipeline start time
            on_script_ready: Optional callback called when script is enhanced.
            trailer_image_path: Optional path to trailer image for visual consistency.

        Returns:
            ProPipelineResult
        """
        import time
        import uuid

        # Generate a job_id for ProPipeline (similar to NormalPipeline)
        job_id = str(uuid.uuid4())[:8]

        tts_results = []
        bgm_results = []
        image_results = []
        review_history = []
        script = None
        final_audio = None

        try:
            # Initialize job record in evaluation store
            store = self._ensure_eval_store()
            prompt = content.text[:200] if content.text else None
            store.create_job(
                job_id=job_id,
                mode="pro",
                prompt=prompt,
                output_dir=str(self.output_dir)
            )
            # Stage 2: Script enhancement with Director review
            if progress:
                progress.scripting("Starting script enhancement...")

            script, review_history = await self._enhance_script_with_review(
                content, progress
            )

            # INCREMENTAL QUALITY: Evaluate script immediately after enhancement
            await self._evaluate_script_quality(script, job_id, progress)

            # Fire-and-forget: notify callback that script is ready (for trailer generation)
            if on_script_ready:
                try:
                    on_script_ready(job_id, script)
                except Exception as e:
                    print(f"[ProPipeline] on_script_ready callback failed: {e}")

            # Stage 2.5: Emotion validation + Speaker assignment
            # Both are independent reads of the script; emotion fixes are applied
            # first, then speaker assignment runs on the fixed script.
            if self.config.emotion_validation:
                if progress:
                    progress.validating("emotions", "Validating emotions...")
                script = await self._validate_and_fix_emotions(script, progress)

            if self.config.speaker_format != "single":
                if progress:
                    progress.validating("speakers", "Assigning speakers...")
                script = await self._assign_speakers(script, progress)

            if progress:
                progress.validating("complete", "Validation complete")

            # Stage 3+4+5: Generate TTS + BGM + Images IN PARALLEL
            if progress:
                progress.update(
                    GenerationPhase.GENERATING_TTS,
                    "Generating TTS, BGM, and images in parallel...",
                )

            tts_task = asyncio.create_task(
                self._generate_tts_sentence_level(script, progress)
            )

            # Use intelligent BGM generation if enabled, otherwise fall back to daisy chain
            if self.config.bgm_intelligent:
                bgm_task = asyncio.create_task(
                    self._generate_bgm_intelligent(script, progress)
                )
            else:
                bgm_task = asyncio.create_task(
                    self._generate_bgm_daisy_chain(script, progress)
                )

            image_task = asyncio.create_task(
                self._generate_images_parallel(script, progress, trailer_image_path)
            )

            # Wait for all three to complete - use return_exceptions=True to prevent
            # cascade failures where one task failing cancels all others
            results = await asyncio.gather(
                tts_task, bgm_task, image_task,
                return_exceptions=True
            )

            # Handle results with graceful degradation
            tts_results, bgm_results, image_results = self._handle_parallel_results(results)

            # INCREMENTAL QUALITY: Evaluate voice, pacing, and BGM after asset generation
            await self._evaluate_voice_quality(tts_results, job_id, progress)
            await self._evaluate_bgm_quality(bgm_results, job_id, progress)

            # Stage 6: Apply voice styles (with emotion modifiers)
            if self.config.apply_voice_styles:
                if progress:
                    progress.mixing_audio("Applying voice styles...")
                tts_results = await self._apply_voice_styles(tts_results)

            # Stage 7: Mix with VAD ducking
            if progress:
                progress.mixing_audio("Mixing with VAD ducking...")

            final_audio = await self._mix_audio_pro(tts_results, bgm_results)

            # INCREMENTAL QUALITY: Evaluate audio_mix, ending, duration after mixing
            await self._evaluate_audio_quality(script, final_audio, job_id, progress)

            # Stage 8: Assemble video
            if progress:
                progress.assembling_video("Creating final video...")

            try:
                final_video = await self._assemble_video_pro(final_audio, image_results)
            except Exception as video_err:
                print(f"[ProPipeline] Video assembly failed, returning audio: {video_err}")
                final_video = final_audio

            # INCREMENTAL QUALITY: Evaluate video after assembly
            await self._evaluate_video_quality(final_video, final_audio, image_results, job_id, progress)

            duration = time.time() - start_time

            # Stage 9: Generate final quality report
            quality_report = await self._evaluate_quality(
                job_id=job_id,
                script=script,
                tts_results=tts_results,
                bgm_results=bgm_results,
                image_results=image_results,
                final_audio=final_audio,
                final_video=final_video,
                progress=progress,
                duration_seconds=duration,
            )

            if progress:
                progress.complete(final_video)

            return ProPipelineResult(
                success=True,
                output_path=final_video,
                audio_output_path=final_audio,
                script=script,
                review_history=review_history,
                tts_files=tts_results,
                bgm_files=bgm_results,
                image_files=image_results,
                duration_seconds=duration,
                config_used=self.config,
                quality_report=quality_report,
            )

        except Exception as e:
            import time as time_module
            duration = time_module.time() - start_time
            if progress:
                progress.error(str(e))

            # Mark job as failed in evaluation store
            try:
                store = self._ensure_eval_store()
                store.fail_job(job_id, str(e))
            except Exception:
                pass  # Don't fail on store error

            # Return partial results if we have any
            partial_output = final_audio if final_audio else None

            return ProPipelineResult(
                success=False,
                output_path=partial_output,
                audio_output_path=final_audio,
                script=script,
                review_history=review_history,
                tts_files=tts_results,
                bgm_files=bgm_results,
                image_files=image_results,
                duration_seconds=duration,
                config_used=self.config,
                error=str(e),
            )

    def _handle_parallel_results(
        self,
        results: tuple
    ) -> tuple:
        """
        Handle results from asyncio.gather with return_exceptions=True.

        Provides graceful degradation when some tasks fail - the pipeline
        continues with partial results rather than failing completely.

        Args:
            results: Tuple of (tts_result, bgm_result, image_result)
                     Each can be a list of results or an Exception.

        Returns:
            Tuple of (tts_results, bgm_results, image_results) with
            empty lists for failed tasks.
        """
        tts_raw, bgm_raw, image_raw = results

        # Handle TTS results
        if isinstance(tts_raw, Exception):
            print(f"[ProPipeline] TTS generation failed: {tts_raw}")
            tts_results = []
        else:
            tts_results = tts_raw or []
            # Count successful TTS items
            success_count = sum(1 for r in tts_results if r.get('path'))
            print(f"[ProPipeline] TTS: {success_count}/{len(tts_results)} successful")

        # Handle BGM results
        if isinstance(bgm_raw, Exception):
            print(f"[ProPipeline] BGM generation failed: {bgm_raw}")
            bgm_results = []
        else:
            bgm_results = bgm_raw or []
            success_count = sum(1 for r in bgm_results if r.get('path'))
            print(f"[ProPipeline] BGM: {success_count}/{len(bgm_results)} successful")

        # Handle Image results
        if isinstance(image_raw, Exception):
            print(f"[ProPipeline] Image generation failed: {image_raw}")
            image_results = []
        else:
            image_results = image_raw or []
            success_count = sum(1 for r in image_results if r.get('path'))
            print(f"[ProPipeline] Images: {success_count}/{len(image_results)} successful")

        # Check if we have minimum viable results
        tts_success = [r for r in tts_results if r.get('path')]
        if not tts_success:
            raise Exception("TTS generation completely failed - cannot create podcast without voice")

        # BGM and images are optional - we can continue without them
        if not bgm_results or not any(r.get('path') for r in bgm_results):
            print("[ProPipeline] Warning: No BGM available, proceeding with voice-only")

        if not image_results or not any(r.get('path') for r in image_results):
            print("[ProPipeline] Warning: No images available, will create audio-only output")

        return tts_results, bgm_results, image_results

    async def _validate_and_fix_emotions(
        self,
        script: Dict[str, Any],
        progress: Optional[ProgressStream] = None
    ) -> Dict[str, Any]:
        """
        Validate emotions in script and auto-fix issues.

        Returns:
            Script with validated/fixed emotions
        """
        from agents.emotion_validator import EmotionValidator

        validator = EmotionValidator()
        loop = asyncio.get_event_loop()

        result = await loop.run_in_executor(
            None,
            lambda: validator.validate_script(script)
        )

        if not result.is_valid:
            print(f"[ProPipeline] Emotion validation found {result.errors_count} errors, {result.warnings_count} warnings")

            # Auto-fix if possible
            fixes = validator.suggest_emotion_fixes(result.issues)
            if fixes:
                print(f"[ProPipeline] Applying {len(fixes)} auto-fixes")
                script = validator.apply_fixes(script, fixes)

        return script

    async def _assign_speakers(
        self,
        script: Dict[str, Any],
        progress: Optional[ProgressStream] = None
    ) -> Dict[str, Any]:
        """
        Assign speakers to script chunks.

        Returns:
            Script with speaker assignments
        """
        from agents.speaker_assignment_agent import SpeakerAssignmentAgent

        agent = SpeakerAssignmentAgent()
        loop = asyncio.get_event_loop()

        # Determine format
        format_id = self.config.speaker_format
        if format_id == "auto":
            format_id = None  # Let agent auto-detect

        result = await loop.run_in_executor(
            None,
            lambda: agent.assign_speakers(
                script,
                format_id=format_id,
                manual_assignments=self.config.manual_speakers,
                voice_overrides=self.config.voice_overrides
            )
        )

        return result

    async def _enhance_script_with_review(
        self,
        content: ExtractedContent,
        progress: Optional[ProgressStream] = None
    ) -> tuple:
        """
        Enhance script with Director review loop.

        Returns:
            Tuple of (enhanced_script, review_history)
        """
        from agents.script_designer_agent import ScriptDesignerAgent
        from agents.director_agent import DirectorAgent

        # Use opus for highest quality
        model_id = MODEL_OPTIONS["opus"]

        enhancer = ScriptDesignerAgent(model=model_id)
        director = DirectorAgent(model=model_id)

        loop = asyncio.get_event_loop()

        # Get target duration from content metadata (set by SmartInputHandler)
        metadata = content.metadata or {}
        target_duration = metadata.get("target_duration_minutes")
        # Get conversational style flag (set by PipelineService)
        conversational_style = metadata.get("conversational_style", False)

        review_history = []
        feedback = None
        script = None
        approved = False
        round_num = 0
        max_rounds = self.config.max_review_rounds

        while not approved and round_num < max_rounds:
            round_num += 1

            # Report enhancing sub-step
            if progress:
                progress.director_review(
                    round_num, max_rounds, "enhancing",
                    f"Round {round_num}/{max_rounds}: Enhancing script..."
                )

            # Enhance script with target duration and conversational style
            script = await loop.run_in_executor(
                None,
                lambda fb=feedback: enhancer.enhance(
                    content.text,
                    feedback=fb,
                    target_duration_minutes=target_duration,
                    conversational_style=conversational_style
                )
            )

            if not self.config.director_review:
                # Skip review if disabled
                break

            # Report reviewing sub-step
            if progress:
                progress.director_review(
                    round_num, max_rounds, "reviewing",
                    f"Round {round_num}/{max_rounds}: Director reviewing..."
                )

            # Review script
            review = await loop.run_in_executor(
                None,
                lambda: director.review(script)
            )

            review_entry = {
                "round": round_num,
                "score": review.get("score", 0),
                "approved": review.get("approved", False),
                "feedback": review.get("feedback", ""),
            }
            review_history.append(review_entry)

            if review.get("approved") or review.get("score", 0) >= self.config.approval_threshold:
                approved = True
                if progress:
                    progress.director_review(
                        round_num, max_rounds, "approved",
                        f"Script approved! Score: {review.get('score')}/10"
                    )
            else:
                feedback = review.get("feedback", "")

        # Add review history to script
        script["review_history"] = review_history
        script["final_status"] = {
            "approved": approved,
            "total_rounds": round_num,
            "final_score": review_history[-1]["score"] if review_history else 0
        }

        # Save script
        script_path = self.output_dir / "enhanced_script.json"
        with open(script_path, 'w') as f:
            json.dump(script, f, indent=2)

        return script, review_history

    async def _generate_tts_sentence_level(
        self,
        script: Dict[str, Any],
        progress: Optional[ProgressStream] = None
    ) -> List[Dict[str, Any]]:
        """Generate sentence-level TTS with parallel execution (10 workers)."""
        from agents.audio_designer.tts_narrator import TTSNarrator
        from utils.text_processing import split_into_sentences, get_intensity_for_sentence

        narrator = TTSNarrator(output_dir=AUDIO_DIR / "tts")
        narrator.set_emotion_voice_enabled(self.config.emotion_voice_sync)

        # Build sentence-level tasks from script
        tts_tasks = []
        task_metadata = []

        # Hook sentences
        hook = script.get("hook", {})
        if hook.get("text"):
            hook_sentences = split_into_sentences(hook["text"])
            hook_emotion = hook.get("emotion", "intrigue")
            hook_voice_id = hook.get("voice_id")
            hook_speaker = hook.get("speaker")

            for sent_idx, sentence in enumerate(hook_sentences):
                intensity = get_intensity_for_sentence(sentence, tension_level=3)
                tts_tasks.append({
                    "id": f"hook_sent_{sent_idx}",
                    "text": sentence,
                    "filename": f"hook_sent_{sent_idx + 1}",
                })
                task_metadata.append({
                    "type": "hook_sentence",
                    "sentence_idx": sent_idx,
                    "total_sentences": len(hook_sentences),
                    "text": sentence,
                    "emotion": hook_emotion,
                    "speaker": hook_speaker,
                    "voice_id": hook_voice_id,
                    "intensity_boost_percent": intensity,
                    "is_emphasis": intensity > 0,
                })

        # Module sentences
        for module in script.get("modules", []):
            module_id = module.get("id", 0)
            for chunk_idx, chunk in enumerate(module.get("chunks", [])):
                text = chunk.get("text", "")
                if not text:
                    continue

                tension_level = chunk.get("tension_level", 2)
                chunk_emotion = chunk.get("emotion", "neutral")
                chunk_voice_id = chunk.get("voice_id")
                chunk_speaker = chunk.get("speaker")
                sentences = split_into_sentences(text)

                for sent_idx, sentence in enumerate(sentences):
                    intensity = get_intensity_for_sentence(sentence, tension_level)
                    tts_tasks.append({
                        "id": f"m{module_id}_c{chunk_idx}_s{sent_idx}",
                        "text": sentence,
                        "filename": f"module_{module_id}_chunk_{chunk_idx + 1}_sent_{sent_idx + 1}",
                    })
                    task_metadata.append({
                        "type": "chunk_sentence",
                        "module_id": module_id,
                        "chunk_idx": chunk_idx,
                        "sentence_idx": sent_idx,
                        "total_sentences": len(sentences),
                        "text": sentence,
                        "emotion": chunk_emotion,
                        "speaker": chunk_speaker,
                        "voice_id": chunk_voice_id,
                        "tension_level": tension_level,
                        "intensity_boost_percent": intensity,
                        "is_emphasis": intensity > 0,
                        "module_title": module.get("title", ""),
                    })

        total = len(tts_tasks)
        print(f"[ProPipeline] Generating {total} sentences with 10 parallel workers")

        # Generate function that uses the shared narrator
        def generate_single_sentence(text: str, filename: str) -> Optional[str]:
            idx = next(
                i for i, t in enumerate(tts_tasks) if t["filename"] == filename
            )
            meta = task_metadata[idx]
            return narrator.generate_speech(
                text,
                filename,
                is_emphasis=meta.get("is_emphasis", False),
                emotion=meta.get("emotion", "neutral"),
                voice_id=meta.get("voice_id"),
                speaker=meta.get("speaker"),
            )

        # Use TTSParallelExecutor with 10 workers
        tts_executor = TTSParallelExecutor(max_concurrent=10)
        if progress:
            tts_executor.set_progress_callback(
                lambda done, tot: progress.generating_tts(done, tot)
            )

        raw_results = await tts_executor.generate_batch(tts_tasks, generate_single_sentence)
        tts_executor.shutdown()

        # Merge parallel results with metadata
        results = []
        for raw, meta in zip(raw_results, task_metadata):
            entry = {**meta, "path": raw.get("path")}
            if raw.get("error"):
                entry["error"] = raw["error"]
            results.append(entry)

        return results

    async def _generate_bgm_daisy_chain(
        self,
        script: Dict[str, Any],
        progress: Optional[ProgressStream] = None
    ) -> List[Dict[str, Any]]:
        """Generate 9-segment daisy-chain BGM."""
        from agents.audio_designer.bgm_generator import BGMGenerator

        generator = BGMGenerator(output_dir=AUDIO_DIR / "bgm_v2_daisy")

        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(
            None,
            lambda: generator.generate_all_segments(
                use_daisy_chain=self.config.daisy_chain,
                conditioning_strength=0.35
            )
        )

        return results

    async def _generate_bgm_intelligent(
        self,
        script: Dict[str, Any],
        progress: Optional[ProgressStream] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate BGM using Music Intelligence System (Pro mode).

        Uses emotion timeline extraction and dynamic stem composition
        for emotionally responsive background music.

        Args:
            script: Enhanced script with emotion annotations
            progress: Optional progress stream for updates

        Returns:
            List of BGM segment dictionaries in expected mixer format
        """
        try:
            from agents.music_intelligence import MusicIntelligence

            if progress:
                progress.generating_bgm(1, 2, "Extracting emotion timeline...")

            mi = MusicIntelligence(mode="pro")
            timeline = mi.extract_emotion_timeline(script)

            if progress:
                progress.generating_bgm(2, 2, "Composing intelligent BGM...")

            bgm_path = mi.compose_for_pro(timeline)

            if bgm_path and Path(bgm_path).exists():
                print(f"[ProPipeline] Music Intelligence generated BGM: {bgm_path}")
                # Return in expected format for the mixer
                return [{
                    "segment_id": 1,
                    "name": "intelligent_bgm",
                    "path": bgm_path,
                    "phase": "full"
                }]
            else:
                print("[ProPipeline] Music Intelligence returned invalid path, falling back")

        except Exception as e:
            print(f"[ProPipeline] Music Intelligence failed: {e}, falling back to daisy chain")

        # Fallback to daisy chain
        return await self._generate_bgm_daisy_chain(script, progress)

    async def _generate_images_parallel(
        self,
        script: Dict[str, Any],
        progress: Optional[ProgressStream] = None,
        trailer_image_path: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Generate narrative images with emotion alignment.

        If a trailer image exists, it will be used as the first image
        to ensure visual consistency between the preview and full video.

        Args:
            script: Enhanced script with emotion annotations
            progress: Optional progress stream for updates
            trailer_image_path: Optional path to trailer image to reuse as first image

        Returns:
            List of image result dictionaries
        """
        from agents.visual_enhancer_agent import VisualEnhancerAgent
        import os

        generator = VisualEnhancerAgent(emotion_aligned=self.config.emotion_image_alignment)

        loop = asyncio.get_event_loop()

        # Check if trailer image exists and can be reused
        use_trailer_image = (
            trailer_image_path and
            os.path.exists(trailer_image_path)
        )

        if use_trailer_image:
            print(f"[ProPipeline] Reusing trailer image as first image: {trailer_image_path}")

        # Use emotion-aligned generation if script has visual_cues and emotions
        if self.config.emotion_image_alignment and script.get("modules"):
            # Use script-based generation with emotion alignment
            all_results = await loop.run_in_executor(
                None,
                lambda: generator.generate_images_from_script(script)
            )

            # Flatten results
            results = all_results.get("hook", [])
            for module_id, module_images in all_results.get("modules", {}).items():
                results.extend(module_images)

            # Replace first image with trailer image if available
            if use_trailer_image and results:
                results[0] = {
                    "path": trailer_image_path,
                    "type": "hook",
                    "emotion": results[0].get("emotion", "intrigue"),
                    "reused_from_trailer": True
                }

            return results

        # Fall back to default prompts
        results = []

        # Generate hook images (or reuse trailer image for first)
        if use_trailer_image:
            # Add trailer image as first hook image
            results.append({
                "path": trailer_image_path,
                "type": "hook",
                "emotion": "intrigue",
                "reused_from_trailer": True
            })
            # Generate remaining hook images (if generator normally creates multiple)
            hook_results = await loop.run_in_executor(
                None,
                generator.generate_hook_images
            )
            # Skip first hook result since we're using trailer image
            if len(hook_results) > 1:
                results.extend(hook_results[1:])
        else:
            hook_results = await loop.run_in_executor(
                None,
                generator.generate_hook_images
            )
            results.extend(hook_results)

        # Generate module images
        for module_id in [1, 2, 3, 4]:
            module_results = await loop.run_in_executor(
                None,
                lambda mid=module_id: generator.generate_module_images(mid)
            )
            results.extend(module_results)

        return results

    async def _apply_voice_styles(
        self,
        tts_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Apply module-specific voice styles with emotion modifiers."""
        from agents.audio_designer.voice_style_engine import VoiceStyleEngine

        engine = VoiceStyleEngine()

        loop = asyncio.get_event_loop()

        # Apply styles with emotion modifiers enabled based on config
        styled_results = await loop.run_in_executor(
            None,
            lambda: engine.apply_styles_to_all(
                tts_results,
                apply_emotion=self.config.emotion_voice_sync
            )
        )

        return styled_results

    async def _mix_audio_pro(
        self,
        tts_results: List[Dict[str, Any]],
        bgm_results: List[Dict[str, Any]]
    ) -> str:
        """
        Mix audio with VAD-based ducking.

        Filters out failed TTS/BGM items before mixing to handle
        partial failures gracefully.
        """
        from agents.audio_designer.audio_mixer import AudioMixer

        # Filter out failed TTS items (no path = failed generation)
        valid_tts = [r for r in tts_results if r.get('path')]
        failed_tts = len(tts_results) - len(valid_tts)
        if failed_tts > 0:
            print(f"[ProPipeline] Filtering {failed_tts} failed TTS items from mix")

        # Filter out failed BGM items
        valid_bgm = [r for r in bgm_results if r.get('path')]
        failed_bgm = len(bgm_results) - len(valid_bgm)
        if failed_bgm > 0:
            print(f"[ProPipeline] Filtering {failed_bgm} failed BGM items from mix")

        if not valid_tts:
            raise Exception("No valid TTS files available for mixing")

        mixer = AudioMixer()

        loop = asyncio.get_event_loop()
        output_path = await loop.run_in_executor(
            None,
            lambda: mixer.mix_podcast_sentence_level(
                valid_tts,
                valid_bgm,
                output_filename="final_pro_mode"
            )
        )

        return output_path

    async def _assemble_video_pro(
        self,
        audio_path: str,
        image_results: List[Dict[str, Any]]
    ) -> str:
        """Assemble final video with all 16 images."""
        from utils.video_assembler import create_podcast_video

        images = [r.get("path") for r in image_results if r.get("path")]

        if not images:
            return audio_path

        output_dir = VISUALS_DIR / "pro_mode"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "final_podcast_pro.mp4"

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: create_podcast_video(
                audio_path,
                images,
                str(output_path),
                crossfade_duration=2.0,
                use_ken_burns=True,
                fps=24,
                quality="quality",
            )
        )

        return str(output_path)

    async def _evaluate_quality(
        self,
        job_id: str,
        script: Dict[str, Any],
        tts_results: List[Dict[str, Any]],
        bgm_results: List[Dict[str, Any]],
        image_results: List[Dict[str, Any]],
        final_audio: str,
        final_video: str,
        progress: Optional[ProgressStream] = None,
        duration_seconds: float = 0.0,
    ) -> Dict[str, Any]:
        """
        Generate final quality report from incrementally-evaluated metrics.

        NOTE: Individual quality dimensions (script, voice, pacing, bgm, audio_mix,
        ending, video) are now evaluated incrementally during their
        respective pipeline stages. This method builds the final trace report,
        saves to JSON, and updates the job in the evaluation store.

        Args:
            job_id: Job identifier
            script: Enhanced script (unused - already evaluated)
            tts_results: TTS generation results (unused - already evaluated)
            bgm_results: BGM generation results (unused - already evaluated)
            image_results: Image generation results (unused - already evaluated)
            final_audio: Path to final audio (unused - already evaluated)
            final_video: Path to final video (unused - already evaluated)
            progress: Optional progress stream for recommendations
            duration_seconds: Total pipeline duration for job record

        Returns:
            Quality report dictionary
        """
        try:
            # Get the evaluator that was used for incremental evaluations
            evaluator = self._ensure_evaluator(job_id)
            store = self._ensure_eval_store()

            # Generate and save report from already-populated metrics
            report = evaluator.generate_report()
            evaluator.save_report(f"quality_report_{job_id}")
            evaluator.log_summary()

            # Build and save trace report to JSON
            try:
                trace_report = evaluator.build_trace_report(mode="pro")
                trace_report.job_id = job_id

                # Save to output directory as quality_trace.json
                trace_path = trace_report.save(self.output_dir)
                print(f"[ProPipeline] Quality trace saved to: {trace_path}")

                # Complete job in evaluation store
                store.complete_job(
                    job_id=job_id,
                    overall_score=trace_report.overall_score,
                    overall_grade=trace_report.overall_grade,
                    duration_seconds=duration_seconds
                )
            except Exception as e:
                print(f"[ProPipeline] Warning: Failed to save trace report: {e}")

            # Add recommendations to progress stream
            if progress:
                for rec in report.get('recommendations', []):
                    progress.add_quality_recommendation(rec)

            return report

        except Exception as e:
            print(f"[ProPipeline] Quality report generation error: {e}")
            return {"error": str(e), "job_id": job_id}


def run_pro_pipeline(
    input_path: str,
    config: Optional[ProConfig] = None,
    user_prompt: Optional[str] = None,
    show_progress: bool = True
) -> ProPipelineResult:
    """
    Convenience function to run the Pro pipeline.

    Args:
        input_path: Input file path
        config: Pro configuration
        user_prompt: Optional user context
        show_progress: Show progress in console

    Returns:
        ProPipelineResult
    """
    from utils.progress_stream import print_progress

    pipeline = ProPipeline(config=config)
    progress = None

    if show_progress:
        progress = ProgressStream(callback=print_progress)

    return asyncio.run(pipeline.run(input_path, user_prompt, progress))


__all__ = ['ProPipeline', 'ProConfig', 'UltraConfig', 'ProPipelineResult', 'run_pro_pipeline']
