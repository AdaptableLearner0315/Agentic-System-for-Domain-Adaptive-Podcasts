"""
Progress Stream
Author: Sarath

Real-time progress streaming for magical UX during podcast generation.
Provides both sync and async progress updates.
"""

import time
from typing import Dict, Any, Optional, Callable, Generator, AsyncGenerator
from dataclasses import dataclass, field
from enum import Enum
import asyncio


class GenerationPhase(Enum):
    """
    Generation phases for progress tracking.

    Normal mode: INITIALIZING -> ANALYZING -> SCRIPTING -> GENERATING_ASSETS ->
        MIXING_AUDIO -> ASSEMBLING_VIDEO -> COMPLETE

    Pro mode: INITIALIZING -> ANALYZING -> SCRIPTING -> VALIDATING ->
        GENERATING_TTS -> GENERATING_BGM -> GENERATING_IMAGES ->
        MIXING_AUDIO -> ASSEMBLING_VIDEO -> COMPLETE

    Ultra mode: INITIALIZING -> ANALYZING -> SCRIPTING -> DIRECTOR_REVIEW ->
        VALIDATING -> GENERATING_TTS -> GENERATING_BGM -> GENERATING_IMAGES ->
        MIXING_AUDIO -> ASSEMBLING_VIDEO -> COMPLETE

    GENERATING_ASSETS is a combined phase for Normal mode that tracks TTS,
    BGM, and image generation under a single phase with sub-progress in
    ``details.parallel_status``.

    DIRECTOR_REVIEW is an Ultra-only phase for the director review loop that
    can take 45-90 seconds. VALIDATING covers emotion validation and
    speaker assignment (Pro and Ultra modes).
    """
    INITIALIZING = "initializing"
    ANALYZING = "analyzing"
    SCRIPTING = "scripting"
    DIRECTOR_REVIEW = "director_review"  # Pro-only: Director review loop
    VALIDATING = "validating"  # Pro-only: Emotion validation + speaker assignment
    GENERATING_TTS = "generating_tts"
    GENERATING_BGM = "generating_bgm"
    GENERATING_IMAGES = "generating_images"
    GENERATING_ASSETS = "generating_assets"
    MIXING_AUDIO = "mixing_audio"
    ASSEMBLING_VIDEO = "assembling_video"
    COMPLETE = "complete"
    ERROR = "error"


@dataclass
class ProgressUpdate:
    """Progress update data structure."""
    phase: GenerationPhase
    message: str
    progress_percent: float = 0.0
    current_step: int = 0
    total_steps: int = 0
    eta_seconds: Optional[float] = None
    preview: Optional[str] = None  # Preview content (e.g., hook text)
    details: Dict[str, Any] = field(default_factory=dict)
    elapsed_seconds: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            'phase': self.phase.value,
            'message': self.message,
            'progress_percent': round(self.progress_percent, 1),
            'current_step': self.current_step,
            'total_steps': self.total_steps,
            'eta_seconds': round(self.eta_seconds, 1) if self.eta_seconds else None,
            'preview': self.preview,
            'details': self.details,
            'elapsed_seconds': round(self.elapsed_seconds, 1),
        }


class ProgressStream:
    """
    Real-time progress streaming for podcast generation.

    Features:
    - Phase-based progress tracking
    - ETA estimation
    - Preview content streaming
    - Callback support for UI integration
    - Mode-specific weights (Normal vs Pro)
    """

    #: Weights for overall progress calculation (Normal mode).
    #: GENERATING_ASSETS carries 60% of the weight (replacing the previous
    #: GENERATING_TTS: 25 + GENERATING_BGM: 20 + GENERATING_IMAGES: 15).
    NORMAL_PHASE_WEIGHTS = {
        GenerationPhase.INITIALIZING: 2,
        GenerationPhase.ANALYZING: 5,
        GenerationPhase.SCRIPTING: 20,
        GenerationPhase.GENERATING_ASSETS: 60,
        GenerationPhase.MIXING_AUDIO: 8,
        GenerationPhase.ASSEMBLING_VIDEO: 5,
    }

    #: Weights for Pro mode progress calculation.
    #: Pro mode skips director review for speed (~2-3 min).
    PRO_PHASE_WEIGHTS = {
        GenerationPhase.INITIALIZING: 2,
        GenerationPhase.ANALYZING: 3,
        GenerationPhase.SCRIPTING: 10,  # Single enhancement pass
        GenerationPhase.VALIDATING: 5,  # Emotion validation + speaker assignment
        GenerationPhase.GENERATING_TTS: 25,
        GenerationPhase.GENERATING_BGM: 20,
        GenerationPhase.GENERATING_IMAGES: 15,
        GenerationPhase.MIXING_AUDIO: 10,
        GenerationPhase.ASSEMBLING_VIDEO: 10,
    }

    #: Weights for Ultra mode progress calculation.
    #: Ultra mode includes full director review loop (~5-8 min).
    ULTRA_PHASE_WEIGHTS = {
        GenerationPhase.INITIALIZING: 2,
        GenerationPhase.ANALYZING: 3,
        GenerationPhase.SCRIPTING: 5,  # Initial script enhancement
        GenerationPhase.DIRECTOR_REVIEW: 15,  # Director review loop (45-90s)
        GenerationPhase.VALIDATING: 5,  # Emotion validation + speaker assignment
        GenerationPhase.GENERATING_TTS: 20,
        GenerationPhase.GENERATING_BGM: 15,
        GenerationPhase.GENERATING_IMAGES: 15,
        GenerationPhase.MIXING_AUDIO: 10,
        GenerationPhase.ASSEMBLING_VIDEO: 10,
    }

    # Backwards compatibility alias
    PHASE_WEIGHTS = NORMAL_PHASE_WEIGHTS

    def __init__(self, callback: Optional[Callable[[ProgressUpdate], None]] = None, mode: str = "normal"):
        """
        Initialize the ProgressStream.

        Args:
            callback: Optional callback for progress updates
            mode: Pipeline mode ("normal" or "pro") - affects phase weights
        """
        self._callback = callback
        self._mode = mode
        self._start_time = time.time()
        self._phase_start_time = time.time()
        self._current_phase = GenerationPhase.INITIALIZING
        self._phase_progress = {phase: 0.0 for phase in GenerationPhase}
        self._phase_durations: Dict[str, float] = {}
        self._updates = []

    def set_mode(self, mode: str):
        """Set the pipeline mode (normal or pro)."""
        self._mode = mode

    def _get_phase_weights(self) -> Dict[GenerationPhase, int]:
        """Get phase weights based on current mode."""
        if self._mode == "ultra":
            return self.ULTRA_PHASE_WEIGHTS
        if self._mode == "pro":
            return self.PRO_PHASE_WEIGHTS
        return self.NORMAL_PHASE_WEIGHTS

    def get_expected_duration_hint(self) -> Dict[str, Any]:
        """
        Get expected duration hints based on mode.

        Returns:
            Dictionary with duration hints for UI display.
        """
        if self._mode == "ultra":
            return {
                "mode": "ultra",
                "expected_minutes_min": 5,
                "expected_minutes_max": 8,
                "hint": "Ultra mode takes 5-8 minutes for premium quality",
                "phases": {
                    "scripting": "1-2 min (includes director review)",
                    "assets": "3-5 min (TTS + BGM + Images)",
                    "assembly": "1-2 min",
                }
            }
        if self._mode == "pro":
            return {
                "mode": "pro",
                "expected_minutes_min": 2,
                "expected_minutes_max": 3,
                "hint": "Pro mode takes 2-3 minutes for balanced quality",
                "phases": {
                    "scripting": "30-45 sec",
                    "assets": "1-2 min (TTS + BGM + Images)",
                    "assembly": "30-45 sec",
                }
            }
        return {
            "mode": "normal",
            "expected_minutes_min": 1,
            "expected_minutes_max": 2,
            "hint": "Normal mode takes 1-2 minutes",
            "phases": {
                "scripting": "30-45 sec",
                "assets": "45-60 sec",
                "assembly": "15-30 sec",
            }
        }

    def set_callback(self, callback: Callable[[ProgressUpdate], None]):
        """Set the progress callback."""
        self._callback = callback

    def _calculate_overall_progress(self) -> float:
        """Calculate overall progress as weighted sum of phase progress."""
        weights = self._get_phase_weights()
        total_weight = sum(weights.values())
        completed_weight = 0

        for phase, weight in weights.items():
            completed_weight += weight * self._phase_progress.get(phase, 0.0) / 100

        return (completed_weight / total_weight) * 100

    def _estimate_eta(self) -> Optional[float]:
        """Estimate time remaining based on progress."""
        elapsed = time.time() - self._start_time
        progress = self._calculate_overall_progress()

        if progress > 5:  # Need some progress to estimate
            total_estimated = elapsed / (progress / 100)
            return max(0, total_estimated - elapsed)
        return None

    def update(
        self,
        phase: GenerationPhase,
        message: str,
        step: int = 0,
        total: int = 0,
        preview: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> ProgressUpdate:
        """
        Send a progress update.

        Args:
            phase: Current generation phase
            message: Human-readable status message
            step: Current step within phase
            total: Total steps in phase
            preview: Optional preview content
            details: Optional additional details

        Returns:
            ProgressUpdate object
        """
        # Track phase change — record duration of the phase we are leaving
        if phase != self._current_phase:
            if self._current_phase not in (GenerationPhase.COMPLETE, GenerationPhase.ERROR):
                elapsed_in_phase = time.time() - self._phase_start_time
                self._phase_durations[self._current_phase.value] = round(elapsed_in_phase, 1)
            self._current_phase = phase
            self._phase_start_time = time.time()

        # Calculate phase progress
        if total > 0:
            phase_progress = (step / total) * 100
            self._phase_progress[phase] = phase_progress
        elif phase == GenerationPhase.COMPLETE:
            # Mark all phases as complete
            for p in GenerationPhase:
                if p != GenerationPhase.ERROR:
                    self._phase_progress[p] = 100.0

        # Inject phase timing into details
        phase_timing_details = {
            'phase_timings': dict(self._phase_durations),
            'current_phase_elapsed': round(time.time() - self._phase_start_time, 1),
        }
        merged_details = {**(details or {}), **phase_timing_details}

        # Create update
        update = ProgressUpdate(
            phase=phase,
            message=message,
            progress_percent=self._calculate_overall_progress(),
            current_step=step,
            total_steps=total,
            eta_seconds=self._estimate_eta(),
            preview=preview,
            details=merged_details,
            elapsed_seconds=time.time() - self._start_time,
        )

        self._updates.append(update)

        # Call callback if set
        if self._callback:
            self._callback(update)

        return update

    def start(self, message: str = "Starting generation...") -> ProgressUpdate:
        """Mark generation start."""
        self._start_time = time.time()
        duration_hint = self.get_expected_duration_hint()
        return self.update(
            GenerationPhase.INITIALIZING,
            message,
            details={"duration_hint": duration_hint}
        )

    def complete(self, output_path: str) -> ProgressUpdate:
        """Mark generation complete."""
        # Record final phase duration before completing
        if self._current_phase not in (GenerationPhase.COMPLETE, GenerationPhase.ERROR):
            elapsed_in_phase = time.time() - self._phase_start_time
            self._phase_durations[self._current_phase.value] = round(elapsed_in_phase, 1)
        return self.update(
            GenerationPhase.COMPLETE,
            "Generation complete!",
            details={'output_path': output_path}
        )

    def error(self, error_message: str) -> ProgressUpdate:
        """Report an error."""
        return self.update(
            GenerationPhase.ERROR,
            f"Error: {error_message}",
            details={'error': error_message}
        )

    def get_all_updates(self) -> list:
        """Get all progress updates."""
        return [u.to_dict() for u in self._updates]

    # Convenience methods for each phase
    def analyzing(self, message: str = "Analyzing content...") -> ProgressUpdate:
        return self.update(GenerationPhase.ANALYZING, message)

    def scripting(
        self,
        message: str = "Enhancing script...",
        preview: Optional[str] = None
    ) -> ProgressUpdate:
        return self.update(GenerationPhase.SCRIPTING, message, preview=preview)

    def director_review(
        self,
        round_num: int,
        max_rounds: int,
        sub_step: str = "reviewing",
        message: Optional[str] = None
    ) -> ProgressUpdate:
        """
        Report director review progress (Pro mode).

        Args:
            round_num: Current review round (1-indexed)
            max_rounds: Maximum number of review rounds
            sub_step: Current sub-step ("enhancing", "reviewing", "approved")
            message: Optional custom message

        Returns:
            ProgressUpdate with DIRECTOR_REVIEW phase
        """
        if message is None:
            if sub_step == "enhancing":
                message = f"Round {round_num}/{max_rounds}: Enhancing script..."
            elif sub_step == "reviewing":
                message = f"Round {round_num}/{max_rounds}: Director reviewing..."
            elif sub_step == "approved":
                message = f"Round {round_num}/{max_rounds}: Script approved!"
            else:
                message = f"Round {round_num}/{max_rounds}: {sub_step}"

        # Calculate progress within director review phase
        # Each round has 2 sub-steps: enhance (50%) + review (50%)
        round_progress = (round_num - 1) / max_rounds  # Completed rounds
        sub_progress = 0.5 if sub_step in ("reviewing", "approved") else 0
        phase_progress = ((round_progress + (sub_progress / max_rounds)) * 100)

        return self.update(
            GenerationPhase.DIRECTOR_REVIEW,
            message,
            step=round_num,
            total=max_rounds,
            details={
                "round": round_num,
                "max_rounds": max_rounds,
                "sub_step": sub_step,
                "phase_progress": phase_progress,
                "estimated_phase_duration_seconds": max_rounds * 30,  # ~30s per round
            }
        )

    def validating(
        self,
        step: str = "emotions",
        message: Optional[str] = None
    ) -> ProgressUpdate:
        """
        Report validation progress (Pro mode).

        Args:
            step: Current validation step ("emotions", "speakers", "complete")
            message: Optional custom message

        Returns:
            ProgressUpdate with VALIDATING phase
        """
        if message is None:
            if step == "emotions":
                message = "Validating emotions..."
            elif step == "speakers":
                message = "Assigning speakers..."
            elif step == "complete":
                message = "Validation complete"
            else:
                message = f"Validating: {step}"

        step_num = {"emotions": 1, "speakers": 2, "complete": 2}.get(step, 1)
        return self.update(
            GenerationPhase.VALIDATING,
            message,
            step=step_num,
            total=2,
            details={"validation_step": step}
        )

    def generating_tts(
        self,
        step: int,
        total: int,
        current_text: Optional[str] = None
    ) -> ProgressUpdate:
        return self.update(
            GenerationPhase.GENERATING_TTS,
            f"Generating voice ({step}/{total})",
            step=step,
            total=total,
            preview=current_text[:100] if current_text else None
        )

    def generating_bgm(
        self,
        step: int,
        total: int,
        segment_name: Optional[str] = None
    ) -> ProgressUpdate:
        return self.update(
            GenerationPhase.GENERATING_BGM,
            f"Generating music ({step}/{total}): {segment_name or ''}",
            step=step,
            total=total
        )

    def generating_images(
        self,
        step: int,
        total: int,
        image_name: Optional[str] = None
    ) -> ProgressUpdate:
        return self.update(
            GenerationPhase.GENERATING_IMAGES,
            f"Generating image ({step}/{total}): {image_name or ''}",
            step=step,
            total=total
        )

    def generating_assets(
        self,
        step: int = 0,
        total: int = 0,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> ProgressUpdate:
        """
        Report combined asset generation progress (Normal mode).

        Used instead of the separate generating_tts/bgm/images methods
        to avoid phase-fighting when TTS, BGM, and images run in parallel.
        Step/total reflect the grand total across all three components.

        Args:
            step: Number of assets completed across all components.
            total: Grand total of assets (TTS chunks + BGM segments + images).
            message: Optional status message; auto-generated if omitted.
            details: Optional dict; should include ``parallel_status`` with
                per-component ``{done, total}`` dicts for the frontend.

        Returns:
            ProgressUpdate with GENERATING_ASSETS phase.
        """
        msg = message or f"Generating assets ({step}/{total})"
        return self.update(
            GenerationPhase.GENERATING_ASSETS,
            msg,
            step=step,
            total=total,
            details=details
        )

    def mixing_audio(self, message: str = "Mixing audio...") -> ProgressUpdate:
        return self.update(GenerationPhase.MIXING_AUDIO, message)

    def assembling_video(self, message: str = "Creating video...") -> ProgressUpdate:
        return self.update(GenerationPhase.ASSEMBLING_VIDEO, message)


async def stream_generation(
    pipeline,
    input_path: str,
    mode: str = "normal"
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Async generator for streaming progress during generation.

    Args:
        pipeline: Pipeline instance with run_with_progress method
        input_path: Input file path
        mode: Generation mode

    Yields:
        Progress update dictionaries
    """
    progress_queue = asyncio.Queue()

    def progress_callback(update: ProgressUpdate):
        asyncio.create_task(progress_queue.put(update.to_dict()))

    # Start pipeline in background
    progress = ProgressStream(callback=progress_callback)
    task = asyncio.create_task(
        pipeline.run_with_progress(input_path, progress, mode)
    )

    # Stream updates
    while not task.done():
        try:
            update = await asyncio.wait_for(progress_queue.get(), timeout=0.5)
            yield update
        except asyncio.TimeoutError:
            continue

    # Get final result
    try:
        result = await task
        yield {
            'phase': 'complete',
            'message': 'Generation complete!',
            'output_path': result,
            'progress_percent': 100.0,
        }
    except Exception as e:
        yield {
            'phase': 'error',
            'message': str(e),
            'progress_percent': 0.0,
        }


def print_progress(update: ProgressUpdate):
    """Print progress update to console."""
    bar_width = 30
    filled = int(bar_width * update.progress_percent / 100)
    bar = '█' * filled + '░' * (bar_width - filled)

    eta_str = f" ETA: {int(update.eta_seconds)}s" if update.eta_seconds else ""
    print(f"\r[{bar}] {update.progress_percent:.1f}% - {update.message}{eta_str}", end='', flush=True)

    if update.phase in (GenerationPhase.COMPLETE, GenerationPhase.ERROR):
        print()  # New line after completion


__all__ = [
    'GenerationPhase',
    'ProgressUpdate',
    'ProgressStream',
    'stream_generation',
    'print_progress',
]
