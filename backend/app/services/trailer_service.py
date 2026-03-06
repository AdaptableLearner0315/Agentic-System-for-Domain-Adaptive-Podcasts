"""
Trailer Service - Generate quick preview trailer from script hook.

Author: Sarath

Generates a 15-20 second trailer from the script's hook section
immediately after script enhancement completes. This gives users
playable content at ~55s while the full podcast continues generating.

The trailer runs as fire-and-forget - failures don't affect the main pipeline.
"""

import asyncio
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass
import time

# Add project root to path for importing existing modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from config.paths import AUDIO_DIR, VISUALS_DIR
from ..logging_config import get_logger

logger = get_logger("trailer")


@dataclass
class TrailerResult:
    """Result from trailer generation."""
    success: bool
    video_path: Optional[str] = None
    audio_path: Optional[str] = None
    image_path: Optional[str] = None  # For reuse by main pipeline
    duration_seconds: float = 0.0
    error: Optional[str] = None


class TrailerService:
    """
    Generate quick trailer from script hook.

    Generates trailer assets in parallel:
    - TTS for hook text (~8s via fal.ai)
    - Image for hook (~5s via fal.ai)
    - BGM stem (~2s from pre-cached stems)

    Then quickly mixes and assembles into a short video.
    """

    def __init__(self, job_id: str, output_dir: Optional[Path] = None):
        """
        Initialize trailer service.

        Args:
            job_id: Job identifier for file naming and isolation.
            output_dir: Output directory for trailer files.
        """
        self.job_id = job_id
        self.output_dir = Path(output_dir) if output_dir else Path("Output")

        # Create trailer-specific subdirectory
        self.trailer_dir = self.output_dir / job_id / "trailer"
        self.trailer_dir.mkdir(parents=True, exist_ok=True)

        # Lazy-loaded components
        self._narrator = None
        self._music_manager = None

    @property
    def narrator(self):
        """Lazy-load TTS narrator."""
        if self._narrator is None:
            from agents.audio_designer.tts_narrator import TTSNarrator
            self._narrator = TTSNarrator(output_dir=self.trailer_dir)
        return self._narrator

    @property
    def music_manager(self):
        """Lazy-load music asset manager."""
        if self._music_manager is None:
            from assets.music_manager import MusicAssetManager
            self._music_manager = MusicAssetManager()
        return self._music_manager

    async def generate_trailer(self, script: Dict[str, Any]) -> TrailerResult:
        """
        Generate trailer from script hook.

        Runs TTS, image, and BGM generation in parallel, then mixes and
        assembles into a short video.

        Args:
            script: Enhanced script dictionary with hook section.

        Returns:
            TrailerResult with paths to generated files.
        """
        start_time = time.time()

        try:
            # Extract hook data
            hook = script.get("hook", {})
            hook_text = hook.get("text", "")

            if not hook_text:
                return TrailerResult(
                    success=False,
                    error="No hook text in script"
                )

            hook_emotion = hook.get("emotion", "intrigue")
            hook_keywords = hook.get("keywords", [])

            logger.info(f"[Trailer] Generating trailer for job {self.job_id}")
            logger.info(f"[Trailer] Hook text: {hook_text[:100]}...")

            # Generate assets in parallel
            tts_task = self._generate_hook_tts(hook_text, hook_emotion)
            image_task = self._generate_hook_image(hook_keywords, hook_text)
            bgm_task = self._get_bgm_stem(hook_emotion)

            tts_path, image_path, bgm_path = await asyncio.gather(
                tts_task, image_task, bgm_task,
                return_exceptions=True
            )

            # Handle exceptions from parallel tasks
            if isinstance(tts_path, Exception):
                logger.warning(f"[Trailer] TTS failed: {tts_path}")
                tts_path = None
            if isinstance(image_path, Exception):
                logger.warning(f"[Trailer] Image failed: {image_path}")
                image_path = None
            if isinstance(bgm_path, Exception):
                logger.warning(f"[Trailer] BGM failed: {bgm_path}")
                bgm_path = None

            # Must have at least TTS to proceed
            if not tts_path:
                return TrailerResult(
                    success=False,
                    error="Failed to generate hook TTS"
                )

            # Mix audio (TTS + BGM if available)
            audio_path = await self._quick_mix(tts_path, bgm_path)

            # Create video if we have an image, otherwise return audio
            if image_path and audio_path:
                video_path = await self._quick_video(audio_path, image_path)
            else:
                video_path = None

            duration = time.time() - start_time
            logger.info(f"[Trailer] Generated in {duration:.1f}s")

            return TrailerResult(
                success=True,
                video_path=video_path,
                audio_path=audio_path,
                image_path=image_path,  # Store for reuse by main pipeline
                duration_seconds=duration,
            )

        except Exception as e:
            logger.error(f"[Trailer] Generation failed: {e}", exc_info=True)
            return TrailerResult(
                success=False,
                error=str(e),
                duration_seconds=time.time() - start_time,
            )

    async def _generate_hook_tts(
        self,
        text: str,
        emotion: str = "intrigue"
    ) -> Optional[str]:
        """
        Generate TTS for hook text.

        Args:
            text: Hook text to convert to speech.
            emotion: Emotion for voice styling.

        Returns:
            Path to generated audio file.
        """
        loop = asyncio.get_event_loop()

        def _generate():
            return self.narrator.generate_speech(
                text=text,
                output_filename=f"trailer_hook_{self.job_id}",
                emotion=emotion,
            )

        return await loop.run_in_executor(None, _generate)

    async def _generate_hook_image(
        self,
        keywords: list,
        hook_text: str
    ) -> Optional[str]:
        """
        Generate image for hook section.

        Args:
            keywords: Keywords from hook for visual prompt.
            hook_text: Full hook text for context.

        Returns:
            Path to generated image file.
        """
        import fal_client
        import requests

        # Build prompt from keywords or extract from text
        if keywords:
            visual_prompt = " ".join(keywords[:5])
        else:
            # Extract key concepts from hook text
            words = hook_text.split()[:10]
            visual_prompt = " ".join(words)

        # Add cinematic style
        full_prompt = (
            f"{visual_prompt}, cinematic photography, documentary style, "
            "photorealistic, film grain, dramatic lighting, 35mm film aesthetic"
        )

        output_path = self.trailer_dir / f"trailer_image_{self.job_id}.png"

        try:
            loop = asyncio.get_event_loop()

            def _generate():
                result = fal_client.subscribe(
                    "fal-ai/flux/schnell",  # Use schnell for speed (~3s vs ~8s)
                    arguments={
                        "prompt": full_prompt,
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
                return None

            return await loop.run_in_executor(None, _generate)

        except Exception as e:
            logger.warning(f"[Trailer] Image generation error: {e}")
            return None

    async def _get_bgm_stem(self, emotion: str = "intrigue") -> Optional[str]:
        """
        Get pre-cached BGM stem for quick background music.

        Uses the intro stem from the music manager if available,
        falling back to generating a short clip if needed.

        Args:
            emotion: Emotion for stem selection.

        Returns:
            Path to BGM audio file.
        """
        try:
            # Try to get pre-generated intro stem
            stem_path = self.music_manager.select_best_stem("intro", emotion)
            if stem_path:
                logger.info(f"[Trailer] Using cached BGM stem: {stem_path}")
                return stem_path

            # No cached stem available
            logger.info("[Trailer] No cached BGM stem, skipping BGM")
            return None

        except Exception as e:
            logger.warning(f"[Trailer] BGM stem error: {e}")
            return None

    async def _quick_mix(
        self,
        tts_path: str,
        bgm_path: Optional[str]
    ) -> str:
        """
        Quick mix of TTS and BGM.

        Uses pydub for simple overlay - faster than full audio mixer.

        Args:
            tts_path: Path to TTS audio.
            bgm_path: Optional path to BGM audio.

        Returns:
            Path to mixed audio file.
        """
        output_path = self.trailer_dir / f"trailer_mixed_{self.job_id}.mp3"

        loop = asyncio.get_event_loop()

        def _mix():
            try:
                from pydub import AudioSegment

                # Load TTS
                tts = AudioSegment.from_file(tts_path)

                if bgm_path:
                    # Load and trim BGM to match TTS length
                    bgm = AudioSegment.from_file(bgm_path)

                    # Trim BGM 500ms from start (avoid artifacts per CLAUDE.md)
                    bgm = bgm[500:]

                    # Loop or trim BGM to match TTS duration
                    tts_duration = len(tts)
                    if len(bgm) < tts_duration:
                        # Loop BGM
                        loops_needed = (tts_duration // len(bgm)) + 1
                        bgm = bgm * loops_needed
                    bgm = bgm[:tts_duration]

                    # Apply fade in (2s as per CLAUDE.md)
                    bgm = bgm.fade_in(2000)

                    # Apply fade out
                    bgm = bgm.fade_out(1000)

                    # Lower BGM volume for mixing
                    bgm = bgm - 12  # -12dB

                    # Overlay
                    mixed = tts.overlay(bgm)
                else:
                    mixed = tts

                # Export
                mixed.export(str(output_path), format="mp3")
                return str(output_path)

            except Exception as e:
                logger.warning(f"[Trailer] Mix failed: {e}, using TTS only")
                return tts_path

        return await loop.run_in_executor(None, _mix)

    async def _quick_video(
        self,
        audio_path: str,
        image_path: str
    ) -> Optional[str]:
        """
        Quick video assembly from image and audio.

        Creates a simple video with the image and audio,
        using fast encoding for speed.

        Args:
            audio_path: Path to mixed audio.
            image_path: Path to image.

        Returns:
            Path to video file.
        """
        from utils.video_assembler import create_podcast_video

        output_path = self.trailer_dir / f"trailer_{self.job_id}.mp4"

        loop = asyncio.get_event_loop()

        def _assemble():
            try:
                return create_podcast_video(
                    audio_path=audio_path,
                    image_paths=[image_path],
                    output_path=str(output_path),
                    crossfade_duration=0.0,  # Single image, no crossfade
                    use_ken_burns=False,  # Static for speed
                    fps=24,
                    quality="fast",
                )
            except Exception as e:
                logger.error(f"[Trailer] Video assembly failed: {e}")
                return None

        return await loop.run_in_executor(None, _assemble)


__all__ = ['TrailerService', 'TrailerResult']
