"""
Interactive conversation routes for podcast discussions.

Handles:
- POST /{job_id}/session: Start a conversation session
- POST /{job_id}/message: Send a text message
- POST /{job_id}/voice: Send a voice message
- GET /{job_id}/history: Get conversation history
- DELETE /{job_id}/session: End the session
- GET /{job_id}/audio/{message_id}: Get TTS audio for a message
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from fastapi.responses import FileResponse

from ..models.interactive import (
    SessionRequest,
    SessionResponse,
    MessageRequest,
    MessageResponse,
    VoiceMessageRequest,
    TranscriptionResponse,
    HistoryResponse,
    ChatMessage,
    MessageRole,
)
from ..models.responses import ErrorResponse
from ..services.conversation_service import ConversationService, get_conversation_service
from ..services.job_manager import JobManager
from ..dependencies import get_job_manager
from ..models.enums import JobStatus
from ..logging_config import get_logger

logger = get_logger("interactive_routes")

router = APIRouter()


def get_conversation() -> ConversationService:
    """Get the conversation service singleton."""
    return get_conversation_service()


@router.post(
    "/{job_id}/session",
    response_model=SessionResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Job not found"},
        400: {"model": ErrorResponse, "description": "Job not completed"},
    },
    summary="Start interactive session",
    description="Start a new interactive conversation session for a completed podcast.",
)
async def start_session(
    job_id: str,
    job_manager: JobManager = Depends(get_job_manager),
    conversation_service: ConversationService = Depends(get_conversation),
) -> SessionResponse:
    """
    Start a new interactive conversation session.

    Args:
        job_id: Podcast job ID.
        job_manager: Job management service.
        conversation_service: Conversation management service.

    Returns:
        SessionResponse with session ID and welcome message.

    Raises:
        HTTPException: If job not found or not completed.
    """
    # Verify job exists
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")

    # Verify job is completed
    if job.status != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"Job is not completed. Current status: {job.status}"
        )

    # Get script from result for context
    result = job_manager.get_result(job_id)
    script = result.script if result else None

    # Get voice ID from config if available
    voice_id = None
    if result and result.config_used:
        voice_id = result.config_used.get("voice_id")

    # Start session
    session = await conversation_service.start_session(
        job_id=job_id,
        script=script,
        voice_id=voice_id,
    )

    return session


@router.post(
    "/{job_id}/message",
    response_model=MessageResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Session not found"},
        400: {"model": ErrorResponse, "description": "Invalid request"},
    },
    summary="Send text message",
    description="Send a text message and receive a response. For streaming, use the WebSocket endpoint.",
)
async def send_message(
    job_id: str,
    request: MessageRequest,
    conversation_service: ConversationService = Depends(get_conversation),
) -> MessageResponse:
    """
    Send a text message and receive a response.

    Note: This is the non-streaming endpoint. For real-time streaming,
    use the WebSocket endpoint at /api/ws/interactive/{session_id}.

    Args:
        job_id: Podcast job ID.
        request: Message request with content.
        conversation_service: Conversation management service.

    Returns:
        MessageResponse with user and assistant messages.

    Raises:
        HTTPException: If session not found or error processing.
    """
    # Get session for job
    session_id = conversation_service.get_session_for_job(job_id)
    if not session_id:
        raise HTTPException(
            status_code=404,
            detail=f"No active session for job: {job_id}. Start a session first."
        )

    try:
        # Get history before to find user message
        history_before = conversation_service.get_history(session_id)
        user_message_count = len([m for m in history_before.messages if m.role == MessageRole.USER])

        # Send message (non-streaming)
        assistant_message = await conversation_service.send_message_sync(
            session_id=session_id,
            content=request.content,
        )

        # Get updated history
        history = conversation_service.get_history(session_id)

        # Find the user message we just sent
        user_messages = [m for m in history.messages if m.role == MessageRole.USER]
        user_message = user_messages[-1] if user_messages else ChatMessage(
            id="unknown",
            role=MessageRole.USER,
            content=request.content,
        )

        return MessageResponse(
            user_message=user_message,
            assistant_message=assistant_message,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Error processing message: %s", e)
        raise HTTPException(status_code=500, detail="Error processing message")


@router.post(
    "/{job_id}/voice",
    response_model=TranscriptionResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Session not found"},
        400: {"model": ErrorResponse, "description": "Invalid audio"},
    },
    summary="Send voice message",
    description="Upload voice audio for transcription. The transcribed text will be sent as a message.",
)
async def send_voice_message(
    job_id: str,
    audio: UploadFile = File(..., description="Audio file (webm, wav, mp3)"),
    generate_audio: bool = True,
    conversation_service: ConversationService = Depends(get_conversation),
) -> TranscriptionResponse:
    """
    Send a voice message by uploading audio.

    The audio is transcribed using Whisper, then the transcription
    is sent as a text message.

    Args:
        job_id: Podcast job ID.
        audio: Audio file upload.
        generate_audio: Whether to generate TTS for response.
        conversation_service: Conversation management service.

    Returns:
        TranscriptionResponse with transcribed text.

    Raises:
        HTTPException: If session not found or transcription fails.
    """
    # Get session for job
    session_id = conversation_service.get_session_for_job(job_id)
    if not session_id:
        raise HTTPException(
            status_code=404,
            detail=f"No active session for job: {job_id}. Start a session first."
        )

    # Validate content type
    allowed_types = ["audio/webm", "audio/wav", "audio/mp3", "audio/mpeg", "audio/ogg"]
    if audio.content_type and audio.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid audio format: {audio.content_type}. Allowed: {', '.join(allowed_types)}"
        )

    try:
        # Read audio data
        audio_data = await audio.read()

        # Transcribe using STT service
        from ..services.stt_service import get_stt_service
        stt_service = get_stt_service()

        result = await stt_service.transcribe(audio_data)

        return TranscriptionResponse(
            transcription=result["text"],
            confidence=result.get("confidence", 0.9),
            duration_seconds=result.get("duration"),
        )

    except ImportError:
        raise HTTPException(
            status_code=501,
            detail="Speech-to-text service not available"
        )
    except Exception as e:
        logger.error("Error transcribing audio: %s", e)
        raise HTTPException(status_code=500, detail="Error transcribing audio")


@router.get(
    "/{job_id}/history",
    response_model=HistoryResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Session not found"},
    },
    summary="Get conversation history",
    description="Get the full conversation history for the active session.",
)
async def get_history(
    job_id: str,
    conversation_service: ConversationService = Depends(get_conversation),
) -> HistoryResponse:
    """
    Get conversation history for the active session.

    Args:
        job_id: Podcast job ID.
        conversation_service: Conversation management service.

    Returns:
        HistoryResponse with all messages.

    Raises:
        HTTPException: If no active session found.
    """
    session_id = conversation_service.get_session_for_job(job_id)
    if not session_id:
        raise HTTPException(
            status_code=404,
            detail=f"No active session for job: {job_id}"
        )

    return conversation_service.get_history(session_id)


@router.delete(
    "/{job_id}/session",
    responses={
        404: {"model": ErrorResponse, "description": "Session not found"},
    },
    summary="End session",
    description="End the active conversation session for a job.",
)
async def end_session(
    job_id: str,
    conversation_service: ConversationService = Depends(get_conversation),
) -> dict:
    """
    End the active conversation session.

    Args:
        job_id: Podcast job ID.
        conversation_service: Conversation management service.

    Returns:
        Confirmation message.

    Raises:
        HTTPException: If no active session found.
    """
    session_id = conversation_service.get_session_for_job(job_id)
    if not session_id:
        raise HTTPException(
            status_code=404,
            detail=f"No active session for job: {job_id}"
        )

    conversation_service.end_session(session_id)

    return {"message": "Session ended", "session_id": session_id}


@router.get(
    "/{job_id}/session",
    responses={
        404: {"model": ErrorResponse, "description": "Session not found"},
    },
    summary="Get session info",
    description="Get information about the active session for a job.",
)
async def get_session_info(
    job_id: str,
    conversation_service: ConversationService = Depends(get_conversation),
) -> dict:
    """
    Get information about the active session.

    Args:
        job_id: Podcast job ID.
        conversation_service: Conversation management service.

    Returns:
        Session information.

    Raises:
        HTTPException: If no active session found.
    """
    session_id = conversation_service.get_session_for_job(job_id)
    if not session_id:
        raise HTTPException(
            status_code=404,
            detail=f"No active session for job: {job_id}"
        )

    info = conversation_service.get_session(session_id)
    if not info:
        raise HTTPException(status_code=404, detail="Session not found")

    return {
        "session_id": info.session_id,
        "job_id": info.job_id,
        "created_at": info.created_at.isoformat(),
        "message_count": info.message_count,
        "is_active": info.is_active,
    }


@router.get(
    "/audio/{message_id}",
    responses={
        404: {"model": ErrorResponse, "description": "Audio not found"},
    },
    summary="Get TTS audio",
    description="Get the generated TTS audio file for a message.",
)
async def get_audio(
    message_id: str,
) -> FileResponse:
    """
    Get the TTS audio file for a message.

    Args:
        message_id: Message identifier.

    Returns:
        Audio file (WAV format).

    Raises:
        HTTPException: If audio file not found.
    """
    from ..services.interactive_tts_service import get_interactive_tts_service

    tts_service = get_interactive_tts_service()
    audio_path = tts_service.get_audio_path(message_id)

    if not audio_path or not audio_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Audio not found for message: {message_id}"
        )

    return FileResponse(
        path=str(audio_path),
        media_type="audio/wav",
        filename=f"{message_id}.wav",
    )
