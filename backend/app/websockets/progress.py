"""
WebSocket endpoint for real-time progress streaming.

Provides WebSocket connections for clients to receive real-time
progress updates during podcast generation.
"""

import asyncio
import json
from typing import Dict, Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends

from ..dependencies import get_job_manager
from ..services.job_manager import JobManager
from ..services.progress_adapter import adapter_manager
from ..models.enums import JobStatus, GenerationPhase

router = APIRouter()


class ConnectionManager:
    """
    Manages WebSocket connections for progress streaming.

    Handles connection lifecycle, message broadcasting, and
    cleanup of disconnected clients.

    Attributes:
        _connections: Dictionary mapping job IDs to connected WebSockets
        _lock: Lock for thread-safe connection management
    """

    def __init__(self):
        """Initialize the connection manager."""
        self._connections: Dict[str, Set[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, job_id: str, websocket: WebSocket) -> None:
        """
        Accept a new WebSocket connection for a job.

        Args:
            job_id: Job identifier to subscribe to.
            websocket: WebSocket connection.
        """
        await websocket.accept()

        async with self._lock:
            if job_id not in self._connections:
                self._connections[job_id] = set()
            self._connections[job_id].add(websocket)

    async def disconnect(self, job_id: str, websocket: WebSocket) -> None:
        """
        Remove a WebSocket connection.

        Args:
            job_id: Job identifier.
            websocket: WebSocket connection to remove.
        """
        async with self._lock:
            if job_id in self._connections:
                self._connections[job_id].discard(websocket)
                if not self._connections[job_id]:
                    del self._connections[job_id]

    async def broadcast(self, job_id: str, message: dict) -> None:
        """
        Broadcast a message to all connections for a job.

        Args:
            job_id: Job identifier.
            message: Message dictionary to broadcast.
        """
        async with self._lock:
            connections = self._connections.get(job_id, set()).copy()

        dead_connections = set()

        for websocket in connections:
            try:
                await websocket.send_json(message)
            except Exception:
                dead_connections.add(websocket)

        # Clean up dead connections
        for websocket in dead_connections:
            await self.disconnect(job_id, websocket)

    async def broadcast_all(self, message: dict) -> None:
        """
        Broadcast a message to all connections.

        Args:
            message: Message dictionary to broadcast.
        """
        async with self._lock:
            all_connections = [
                (job_id, ws)
                for job_id, connections in self._connections.items()
                for ws in connections
            ]

        for job_id, websocket in all_connections:
            try:
                await websocket.send_json(message)
            except Exception:
                await self.disconnect(job_id, websocket)

    def get_connection_count(self, job_id: str) -> int:
        """
        Get the number of connections for a job.

        Args:
            job_id: Job identifier.

        Returns:
            Number of active connections.
        """
        return len(self._connections.get(job_id, set()))


# Global connection manager
manager = ConnectionManager()


@router.websocket("/{job_id}/progress")
async def progress_websocket(
    websocket: WebSocket,
    job_id: str,
):
    """
    WebSocket endpoint for job progress streaming.

    Clients connect to this endpoint to receive real-time progress
    updates for a specific job. The connection remains open until
    the job completes or the client disconnects.

    Messages are JSON objects with the following structure:
    ```json
    {
        "type": "progress" | "complete" | "error",
        "job_id": "string",
        "phase": "initializing" | "scripting" | ... | "complete" | "error",
        "message": "string",
        "progress_percent": 0-100,
        "current_step": number,
        "total_steps": number,
        "eta_seconds": number | null,
        "preview": "string" | null
    }
    ```

    Args:
        websocket: WebSocket connection.
        job_id: Job identifier to subscribe to.
    """
    # Get job manager
    from ..dependencies import get_job_manager
    job_manager = get_job_manager()

    # Verify job exists (must accept before closing per WebSocket protocol)
    job = job_manager.get_job(job_id)
    if not job:
        await websocket.accept()
        await websocket.send_json({"type": "error", "job_id": job_id, "error": "Job not found"})
        await websocket.close(code=4004, reason="Job not found")
        return

    # Accept connection
    await manager.connect(job_id, websocket)

    # Start the adapter's queue processor as a background task
    adapter = await adapter_manager.get_adapter(job_id)
    queue_task = asyncio.create_task(adapter.process_queue())

    # Define listener before try block so it's always in scope for finally
    send_update = None

    try:
        # Send initial status
        progress = job_manager.get_progress(job_id)
        if progress:
            await websocket.send_json({
                "type": "progress",
                "job_id": job_id,
                "phase": progress.phase.value,
                "message": progress.message,
                "progress_percent": progress.progress_percent,
                "current_step": progress.current_step,
                "total_steps": progress.total_steps,
                "eta_seconds": progress.eta_seconds,
                "preview": progress.preview,
                "elapsed_seconds": progress.elapsed_seconds,
                "details": progress.details,
            })

        # Set up progress listener that sends to this WebSocket
        async def send_update(update):
            try:
                await websocket.send_json({
                    "type": "progress",
                    **update.to_dict(),
                })
            except Exception:
                pass

        await adapter.add_listener(send_update)

        # Poll for updates until job completes
        while True:
            # Check job status
            job = job_manager.get_job(job_id)
            if not job:
                break

            if job.status in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED):
                # Send final status
                if job.status == JobStatus.COMPLETED:
                    result = job_manager.get_result(job_id)
                    await websocket.send_json({
                        "type": "complete",
                        "job_id": job_id,
                        "success": True,
                        "output_path": result.output_path if result else None,
                        "video_url": result.video_url if result else None,
                        "duration_seconds": result.duration_seconds if result else None,
                    })
                elif job.status == JobStatus.FAILED:
                    await websocket.send_json({
                        "type": "error",
                        "job_id": job_id,
                        "error": job.error or "Job failed",
                    })
                else:
                    await websocket.send_json({
                        "type": "cancelled",
                        "job_id": job_id,
                    })
                break

            # Wait for updates or timeout
            try:
                # Wait for client ping/pong to detect disconnection
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=30.0
                )

                # Handle client messages (ping, cancel request, etc.)
                try:
                    message = json.loads(data)
                    if message.get("type") == "ping":
                        await websocket.send_json({"type": "pong"})
                    elif message.get("type") == "cancel":
                        job_manager.request_cancellation(job_id)
                        await websocket.send_json({
                            "type": "cancelling",
                            "job_id": job_id,
                        })
                except json.JSONDecodeError:
                    pass

            except asyncio.TimeoutError:
                # Send heartbeat
                await websocket.send_json({"type": "heartbeat"})
                continue

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json({
                "type": "error",
                "job_id": job_id,
                "error": str(e),
            })
        except Exception:
            pass
    finally:
        # Cancel the queue processor and clean up
        queue_task.cancel()
        try:
            await queue_task
        except asyncio.CancelledError:
            pass
        if send_update is not None:
            await adapter.remove_listener(send_update)
        await manager.disconnect(job_id, websocket)


async def broadcast_progress(job_id: str, progress: dict) -> None:
    """
    Broadcast progress update to all WebSocket connections for a job.

    This function is called by the pipeline service when progress
    updates occur.

    Args:
        job_id: Job identifier.
        progress: Progress update dictionary.
    """
    await manager.broadcast(job_id, {
        "type": "progress",
        **progress,
    })
