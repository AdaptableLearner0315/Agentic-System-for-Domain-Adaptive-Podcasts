"""
Progress stream adapter for WebSocket broadcasting.

Bridges the existing ProgressStream callback system to WebSocket
connections, enabling real-time progress updates to clients.
"""

import asyncio
import json
from typing import Callable, Dict, Any, List, Optional
from dataclasses import dataclass

from ..models.enums import GenerationPhase
from ..models.responses import ProgressResponse


@dataclass
class ProgressUpdate:
    """
    Progress update message for WebSocket broadcast.

    Attributes:
        job_id: Job identifier
        phase: Current generation phase
        message: Status message
        progress_percent: Overall progress (0-100)
        current_step: Current step number
        total_steps: Total number of steps
        eta_seconds: Estimated time remaining
        preview: Preview content
        elapsed_seconds: Time elapsed since start
        details: Additional details
    """
    job_id: str
    phase: GenerationPhase
    message: str
    progress_percent: float = 0.0
    current_step: int = 0
    total_steps: int = 0
    eta_seconds: Optional[float] = None
    preview: Optional[str] = None
    elapsed_seconds: float = 0.0
    details: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "job_id": self.job_id,
            "phase": self.phase.value,
            "message": self.message,
            "progress_percent": self.progress_percent,
            "current_step": self.current_step,
            "total_steps": self.total_steps,
            "eta_seconds": self.eta_seconds,
            "preview": self.preview,
            "elapsed_seconds": self.elapsed_seconds,
            "details": self.details,
        }

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())


class ProgressAdapter:
    """
    Adapts ProgressStream callbacks to async WebSocket broadcasting.

    This class bridges the synchronous callback-based ProgressStream
    used by the pipelines to the async WebSocket connections used
    by the frontend.

    Usage:
        adapter = ProgressAdapter(job_id)
        adapter.add_listener(websocket_send)

        # Create ProgressStream with adapter callback
        progress = ProgressStream(callback=adapter.on_progress)

        # Run pipeline
        await pipeline.run(content, progress=progress)

    Attributes:
        job_id: Job identifier
        _listeners: List of async callback functions
        _queue: Asyncio queue for progress updates
        _lock: Lock for thread-safe listener management
    """

    def __init__(self, job_id: str):
        """
        Initialize the progress adapter.

        Args:
            job_id: Unique job identifier.
        """
        self.job_id = job_id
        self._listeners: List[Callable] = []
        self._queue: asyncio.Queue = asyncio.Queue()
        self._lock = asyncio.Lock()
        # Dedup state: skip updates where phase and percent haven't changed
        self._last_phase: Optional[GenerationPhase] = None
        self._last_percent: Optional[float] = None

    def on_progress(self, update: Any) -> None:
        """
        Callback handler for ProgressStream updates.

        This method is called synchronously by the pipeline's
        ProgressStream. It converts the update and queues it
        for async broadcasting. Deduplicates updates to avoid
        flooding: only sends if phase changed or percent changed by >1%.

        Args:
            update: ProgressUpdate from ProgressStream.
        """
        phase = GenerationPhase(update.phase.value)
        percent = update.progress_percent

        # Dedup: only send if phase changed or percent changed by >1%
        if (self._last_phase == phase
                and self._last_percent is not None
                and abs(percent - self._last_percent) < 1.0):
            return

        self._last_phase = phase
        self._last_percent = percent

        # Convert to our ProgressUpdate format
        progress_update = ProgressUpdate(
            job_id=self.job_id,
            phase=phase,
            message=update.message,
            progress_percent=percent,
            current_step=update.current_step,
            total_steps=update.total_steps,
            eta_seconds=update.eta_seconds,
            preview=update.preview,
            elapsed_seconds=update.elapsed_seconds,
            details=update.details if hasattr(update, "details") else None,
        )

        # Queue for async processing
        try:
            self._queue.put_nowait(progress_update)
        except asyncio.QueueFull:
            pass  # Drop update if queue is full

    async def add_listener(self, callback: Callable) -> None:
        """
        Add a listener for progress updates.

        Args:
            callback: Async callable that receives ProgressUpdate.
        """
        async with self._lock:
            self._listeners.append(callback)

    async def remove_listener(self, callback: Callable) -> None:
        """
        Remove a listener.

        Args:
            callback: Previously added callback to remove.
        """
        async with self._lock:
            if callback in self._listeners:
                self._listeners.remove(callback)

    async def broadcast(self, update: ProgressUpdate) -> None:
        """
        Broadcast a progress update to all listeners.

        Args:
            update: Progress update to broadcast.
        """
        async with self._lock:
            listeners = list(self._listeners)

        for listener in listeners:
            try:
                await listener(update)
            except Exception:
                # Remove failed listener
                await self.remove_listener(listener)

    async def process_queue(self) -> None:
        """
        Process queued progress updates.

        This coroutine should be run as a background task to
        continuously process and broadcast queued updates.
        """
        while True:
            try:
                update = await asyncio.wait_for(
                    self._queue.get(),
                    timeout=0.1
                )
                await self.broadcast(update)
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break

    def to_response(self, update: ProgressUpdate) -> ProgressResponse:
        """
        Convert ProgressUpdate to ProgressResponse.

        Args:
            update: Progress update.

        Returns:
            ProgressResponse for API output.
        """
        return ProgressResponse(
            job_id=update.job_id,
            phase=update.phase,
            message=update.message,
            progress_percent=update.progress_percent,
            current_step=update.current_step,
            total_steps=update.total_steps,
            eta_seconds=update.eta_seconds,
            preview=update.preview,
            elapsed_seconds=update.elapsed_seconds,
            details=update.details,
        )


class ProgressAdapterManager:
    """
    Manages ProgressAdapter instances for multiple jobs.

    Provides a centralized way to create, access, and cleanup
    progress adapters for running jobs.

    Attributes:
        _adapters: Dictionary mapping job IDs to adapters
        _lock: Lock for thread-safe adapter management
    """

    def __init__(self):
        """Initialize the adapter manager."""
        self._adapters: Dict[str, ProgressAdapter] = {}
        self._lock = asyncio.Lock()

    async def get_adapter(self, job_id: str) -> ProgressAdapter:
        """
        Get or create a progress adapter for a job.

        Args:
            job_id: Unique job identifier.

        Returns:
            ProgressAdapter for the job.
        """
        async with self._lock:
            if job_id not in self._adapters:
                self._adapters[job_id] = ProgressAdapter(job_id)
            return self._adapters[job_id]

    async def remove_adapter(self, job_id: str) -> None:
        """
        Remove a progress adapter.

        Args:
            job_id: Job identifier.
        """
        async with self._lock:
            if job_id in self._adapters:
                del self._adapters[job_id]

    async def cleanup(self) -> None:
        """Remove all adapters."""
        async with self._lock:
            self._adapters.clear()


# Global adapter manager instance
adapter_manager = ProgressAdapterManager()
