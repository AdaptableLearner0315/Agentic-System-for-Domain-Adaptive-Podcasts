"""
WebSocket endpoint for interactive podcast conversations.

Provides real-time bidirectional communication for chat streaming,
voice transcription updates, and TTS audio delivery.
"""

import asyncio
import json
from typing import Dict, Set, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ..models.interactive import (
    StreamMessage,
    StreamEventType,
    ClientMessage,
    ChatMessage,
    MessageRole,
)
from ..services.conversation_service import get_conversation_service
from ..logging_config import get_logger

logger = get_logger("interactive_websocket")

router = APIRouter()


class InteractiveConnectionManager:
    """
    Manages WebSocket connections for interactive chat.

    Handles connection lifecycle, message streaming, and
    cleanup of disconnected clients.

    Attributes:
        _connections: Dictionary mapping session IDs to WebSockets
        _lock: Lock for thread-safe connection management
    """

    def __init__(self):
        """Initialize the connection manager."""
        self._connections: Dict[str, Set[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, session_id: str, websocket: WebSocket) -> None:
        """
        Accept a new WebSocket connection for a session.

        Args:
            session_id: Session identifier to subscribe to.
            websocket: WebSocket connection.
        """
        await websocket.accept()

        async with self._lock:
            if session_id not in self._connections:
                self._connections[session_id] = set()
            self._connections[session_id].add(websocket)

        logger.debug("WebSocket connected for session %s", session_id)

    async def disconnect(self, session_id: str, websocket: WebSocket) -> None:
        """
        Remove a WebSocket connection.

        Args:
            session_id: Session identifier.
            websocket: WebSocket connection to remove.
        """
        async with self._lock:
            if session_id in self._connections:
                self._connections[session_id].discard(websocket)
                if not self._connections[session_id]:
                    del self._connections[session_id]

        logger.debug("WebSocket disconnected for session %s", session_id)

    async def send_message(
        self,
        session_id: str,
        websocket: WebSocket,
        message: StreamMessage,
    ) -> bool:
        """
        Send a message to a specific WebSocket.

        Args:
            session_id: Session identifier.
            websocket: Target WebSocket.
            message: Message to send.

        Returns:
            True if message was sent successfully.
        """
        try:
            await websocket.send_json(message.model_dump(mode="json"))
            return True
        except Exception as e:
            logger.warning("Failed to send message to session %s: %s", session_id, e)
            await self.disconnect(session_id, websocket)
            return False

    async def broadcast(self, session_id: str, message: StreamMessage) -> None:
        """
        Broadcast a message to all connections for a session.

        Args:
            session_id: Session identifier.
            message: Message to broadcast.
        """
        async with self._lock:
            connections = self._connections.get(session_id, set()).copy()

        dead_connections = set()

        for websocket in connections:
            try:
                await websocket.send_json(message.model_dump(mode="json"))
            except Exception:
                dead_connections.add(websocket)

        # Clean up dead connections
        for websocket in dead_connections:
            await self.disconnect(session_id, websocket)

    def get_connection_count(self, session_id: str) -> int:
        """
        Get the number of connections for a session.

        Args:
            session_id: Session identifier.

        Returns:
            Number of active connections.
        """
        return len(self._connections.get(session_id, set()))


# Global connection manager
interactive_manager = InteractiveConnectionManager()


@router.websocket("/{session_id}")
async def interactive_websocket(
    websocket: WebSocket,
    session_id: str,
):
    """
    WebSocket endpoint for interactive chat streaming.

    Clients connect to this endpoint for real-time bidirectional
    communication during podcast conversations.

    Message types from client:
    - message: User sends a text message
    - ping: Keep-alive ping
    - end_session: End the conversation

    Message types to client:
    - session_started: Connection established
    - assistant_start: AI response starting
    - assistant_chunk: Partial response text
    - assistant_end: AI response complete
    - audio_ready: TTS audio available
    - error: An error occurred
    - session_ended: Session terminated

    Args:
        websocket: WebSocket connection.
        session_id: Session identifier to connect to.
    """
    conversation_service = get_conversation_service()

    # Verify session exists
    session_info = conversation_service.get_session(session_id)
    if not session_info:
        await websocket.accept()
        await websocket.send_json({
            "type": "error",
            "session_id": session_id,
            "error": "Session not found",
        })
        await websocket.close(code=4004, reason="Session not found")
        return

    if not session_info.is_active:
        await websocket.accept()
        await websocket.send_json({
            "type": "error",
            "session_id": session_id,
            "error": "Session has ended",
        })
        await websocket.close(code=4003, reason="Session ended")
        return

    # Accept connection
    await interactive_manager.connect(session_id, websocket)

    try:
        # Send session started message
        await websocket.send_json(
            StreamMessage(
                type=StreamEventType.SESSION_STARTED,
                session_id=session_id,
            ).model_dump(mode="json")
        )

        # Main message loop
        while True:
            try:
                # Wait for client message with timeout for heartbeat
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=30.0,
                )

                try:
                    client_msg = ClientMessage.model_validate_json(data)
                except Exception:
                    # Try parsing as plain JSON
                    try:
                        msg_dict = json.loads(data)
                        client_msg = ClientMessage(**msg_dict)
                    except Exception:
                        await websocket.send_json({
                            "type": "error",
                            "session_id": session_id,
                            "error": "Invalid message format",
                        })
                        continue

                # Handle message types
                if client_msg.type == "ping":
                    await websocket.send_json({"type": "pong", "session_id": session_id})

                elif client_msg.type == "end_session":
                    conversation_service.end_session(session_id)
                    await websocket.send_json(
                        StreamMessage(
                            type=StreamEventType.SESSION_ENDED,
                            session_id=session_id,
                        ).model_dump(mode="json")
                    )
                    break

                elif client_msg.type == "message":
                    if not client_msg.content:
                        await websocket.send_json({
                            "type": "error",
                            "session_id": session_id,
                            "error": "Message content is required",
                        })
                        continue

                    # Handle the message with streaming
                    await handle_streaming_message(
                        websocket,
                        session_id,
                        client_msg.content,
                        client_msg.generate_audio,
                        conversation_service,
                    )

            except asyncio.TimeoutError:
                # Send heartbeat
                try:
                    await websocket.send_json({"type": "heartbeat", "session_id": session_id})
                except Exception:
                    break
                continue

    except WebSocketDisconnect:
        logger.debug("WebSocket disconnected for session %s", session_id)
    except Exception as e:
        logger.error("WebSocket error for session %s: %s", session_id, e)
        try:
            await websocket.send_json({
                "type": "error",
                "session_id": session_id,
                "error": str(e),
            })
        except Exception:
            pass
    finally:
        await interactive_manager.disconnect(session_id, websocket)


async def handle_streaming_message(
    websocket: WebSocket,
    session_id: str,
    content: str,
    generate_audio: bool,
    conversation_service,
) -> None:
    """
    Handle a user message with streaming response.

    Args:
        websocket: WebSocket connection.
        session_id: Session identifier.
        content: User's message text.
        generate_audio: Whether to generate TTS audio.
        conversation_service: Conversation service instance.
    """
    import uuid

    # Generate message ID for tracking
    message_id = str(uuid.uuid4())[:8]

    # Send start event
    await websocket.send_json(
        StreamMessage(
            type=StreamEventType.ASSISTANT_START,
            session_id=session_id,
            message_id=message_id,
        ).model_dump(mode="json")
    )

    full_response = ""

    try:
        # Stream response chunks
        async for chunk in conversation_service.send_message(session_id, content):
            full_response += chunk
            await websocket.send_json(
                StreamMessage(
                    type=StreamEventType.ASSISTANT_CHUNK,
                    session_id=session_id,
                    message_id=message_id,
                    content=chunk,
                ).model_dump(mode="json")
            )

    except Exception as e:
        logger.error("Error streaming response: %s", e)
        await websocket.send_json(
            StreamMessage(
                type=StreamEventType.ERROR,
                session_id=session_id,
                error=str(e),
            ).model_dump(mode="json")
        )
        return

    # Send end event
    await websocket.send_json(
        StreamMessage(
            type=StreamEventType.ASSISTANT_END,
            session_id=session_id,
            message_id=message_id,
            content=full_response,
        ).model_dump(mode="json")
    )

    # Generate TTS audio if requested (fire-and-forget task)
    if generate_audio and full_response:
        asyncio.create_task(
            generate_and_send_audio(
                websocket,
                session_id,
                message_id,
                full_response,
                conversation_service,
            )
        )


async def generate_and_send_audio(
    websocket: WebSocket,
    session_id: str,
    message_id: str,
    text: str,
    conversation_service,
) -> None:
    """
    Generate TTS audio and send audio_ready event.

    This runs as a background task after text streaming completes.

    Args:
        websocket: WebSocket connection.
        session_id: Session identifier.
        message_id: Message identifier.
        text: Text to convert to speech.
        conversation_service: Conversation service instance.
    """
    try:
        # Import TTS service lazily to avoid circular imports
        from ..services.interactive_tts_service import generate_response_audio

        voice_id = conversation_service.get_voice_id(session_id)

        # Generate audio
        audio_url = await generate_response_audio(
            text=text,
            message_id=message_id,
            voice_id=voice_id,
        )

        if audio_url:
            # Update message with audio URL
            conversation_service.update_message_audio(session_id, message_id, audio_url)

            # Send audio ready event
            await websocket.send_json(
                StreamMessage(
                    type=StreamEventType.AUDIO_READY,
                    session_id=session_id,
                    message_id=message_id,
                    audio_url=audio_url,
                ).model_dump(mode="json")
            )

    except Exception as e:
        logger.warning("Failed to generate audio for message %s: %s", message_id, e)
        # Don't send error - audio is optional enhancement
