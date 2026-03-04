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
from config.paths import OUTPUT_DIR, AUDIO_DIR, TTS_DIR, BGM_DIR, VISUALS_DIR, ensure_directories
from utils.input_router import InputRouter, ExtractedContent
from utils.parallel_executor import TTSParallelExecutor
from utils.progress_stream import ProgressStream, GenerationPhase


@dataclass
class ProConfig:
    """Configuration for Pro pipeline customization."""
    # Script settings
    director_review: bool = True
    max_review_rounds: int = 3
    approval_threshold: int = 7

    # Voice settings
    voice_preset: str = "default"
    apply_voice_styles: bool = True
    custom_pronunciations: Dict[str, str] = field(default_factory=dict)

    # Music settings
    music_genre: str = "cinematic"
    bgm_segments: int = 9
    daisy_chain: bool = True

    # Image settings
    image_count: int = 16
    image_style: str = "cinematic"

    # Quality settings
    tts_sentence_level: bool = True
    vad_ducking: bool = True

    # NEW: Speaker settings
    speaker_format: str = "auto"  # auto, single, interview, co_hosts, narrator_characters
    manual_speakers: Optional[Dict[str, str]] = None  # Manual speaker assignments per chunk
    voice_overrides: Optional[Dict[str, str]] = None  # Voice overrides per speaker role

    # NEW: Emotion settings
    emotion_voice_sync: bool = True  # Sync voice parameters with chunk emotion
    emotion_image_alignment: bool = True  # Align image prompts with chunk emotion
    emotion_validation: bool = True  # Validate emotion consistency

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
            'image_count': self.image_count,
            'image_style': self.image_style,
            'tts_sentence_level': self.tts_sentence_level,
            'vad_ducking': self.vad_ducking,
            # Speaker settings
            'speaker_format': self.speaker_format,
            'manual_speakers': self.manual_speakers,
            'voice_overrides': self.voice_overrides,
            # Emotion settings
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

        if progress:
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
        progress: Optional[ProgressStream] = None
    ) -> ProPipelineResult:
        """
        Run the pipeline with pre-extracted content.

        This allows the SmartInputHandler to pre-process content
        (generation, extraction, or hybrid) before passing to the pipeline.

        Args:
            content: Pre-extracted/generated content
            progress: Optional progress stream for updates

        Returns:
            ProPipelineResult with all outputs
        """
        import time
        start_time = time.time()

        if progress:
            progress.start("Starting high-quality generation...")

        print(f"[ProPipeline] Using pre-processed content: {len(content.text)} characters from {content.source_type}")

        return await self._run_with_content(content, progress, start_time)

    async def _run_with_content(
        self,
        content: ExtractedContent,
        progress: Optional[ProgressStream],
        start_time: float
    ) -> ProPipelineResult:
        """
        Internal method to run pipeline with content.

        Args:
            content: Extracted content
            progress: Progress stream
            start_time: Pipeline start time

        Returns:
            ProPipelineResult
        """
        import time

        tts_results = []
        bgm_results = []
        image_results = []
        review_history = []
        script = None
        final_audio = None

        try:
            # Stage 2: Script enhancement with Director review
            if progress:
                progress.scripting("Enhancing script with Director review...")

            script, review_history = await self._enhance_script_with_review(
                content, progress
            )

            # Stage 2.5: Emotion validation + Speaker assignment IN PARALLEL
            # Both are independent reads of the script; emotion fixes are applied
            # first, then speaker assignment runs on the fixed script.
            if self.config.emotion_validation:
                if progress:
                    progress.scripting("Validating emotions...")
                script = await self._validate_and_fix_emotions(script, progress)

            if self.config.speaker_format != "single":
                if progress:
                    progress.scripting("Assigning speakers...")
                script = await self._assign_speakers(script, progress)

            # Stage 3+4+5: Generate TTS + BGM + Images IN PARALLEL
            if progress:
                progress.update(
                    GenerationPhase.GENERATING_TTS,
                    "Generating TTS, BGM, and images in parallel...",
                )

            tts_task = asyncio.create_task(
                self._generate_tts_sentence_level(script, progress)
            )
            bgm_task = asyncio.create_task(
                self._generate_bgm_daisy_chain(script, progress)
            )
            image_task = asyncio.create_task(
                self._generate_images_parallel(script, progress)
            )

            # Wait for all three to complete
            tts_results, bgm_results, image_results = await asyncio.gather(
                tts_task, bgm_task, image_task
            )

            # Stage 6: Apply voice styles (with emotion modifiers)
            if self.config.apply_voice_styles:
                if progress:
                    progress.mixing_audio("Applying voice styles...")
                tts_results = await self._apply_voice_styles(tts_results)

            # Stage 7: Mix with VAD ducking
            if progress:
                progress.mixing_audio("Mixing with VAD ducking...")

            final_audio = await self._mix_audio_pro(tts_results, bgm_results)

            # Stage 8: Assemble video
            if progress:
                progress.assembling_video("Creating final video...")

            try:
                final_video = await self._assemble_video_pro(final_audio, image_results)
            except Exception as video_err:
                print(f"[ProPipeline] Video assembly failed, returning audio: {video_err}")
                final_video = final_audio

            duration = time.time() - start_time

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
            )

        except Exception as e:
            import time as time_module
            duration = time_module.time() - start_time
            if progress:
                progress.error(str(e))

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
        model_id = "claude-opus-4-5-20250514"

        enhancer = ScriptDesignerAgent(model=model_id)
        director = DirectorAgent(model=model_id)

        loop = asyncio.get_event_loop()

        # Get target duration from content metadata (set by SmartInputHandler)
        target_duration = content.metadata.get("target_duration_minutes")

        review_history = []
        feedback = None
        script = None
        approved = False
        round_num = 0

        while not approved and round_num < self.config.max_review_rounds:
            round_num += 1

            if progress:
                progress.scripting(f"Enhancement round {round_num}/{self.config.max_review_rounds}...")

            # Enhance script with target duration
            script = await loop.run_in_executor(
                None,
                lambda fb=feedback: enhancer.enhance(
                    content.text,
                    feedback=fb,
                    target_duration_minutes=target_duration
                )
            )

            if not self.config.director_review:
                # Skip review if disabled
                break

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
                    progress.scripting(f"Script approved! Score: {review.get('score')}/10")
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

    async def _generate_images_parallel(
        self,
        script: Dict[str, Any],
        progress: Optional[ProgressStream] = None
    ) -> List[Dict[str, Any]]:
        """Generate 16 narrative images with emotion alignment."""
        from agents.visual_enhancer_agent import VisualEnhancerAgent

        generator = VisualEnhancerAgent(emotion_aligned=self.config.emotion_image_alignment)

        loop = asyncio.get_event_loop()

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

            return results

        # Fall back to default prompts
        results = []

        # Generate hook images
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
        """Mix audio with VAD-based ducking."""
        from agents.audio_designer.audio_mixer import AudioMixer

        mixer = AudioMixer()

        loop = asyncio.get_event_loop()
        output_path = await loop.run_in_executor(
            None,
            lambda: mixer.mix_podcast_sentence_level(
                tts_results,
                bgm_results,
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


__all__ = ['ProPipeline', 'ProConfig', 'ProPipelineResult', 'run_pro_pipeline']
