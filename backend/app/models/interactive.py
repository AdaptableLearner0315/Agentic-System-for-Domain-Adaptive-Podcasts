"""
Pydantic models for interactive podcast conversations.

These models define the structure for chat sessions, messages,
and WebSocket streaming events.
"""

from typing import Optional, List, Literal
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class MessageRole(str, Enum):
    """
    Role of a chat message participant.

    Attributes:
        USER: Message from the user
        ASSISTANT: Response from the AI assistant
        SYSTEM: System-generated messages (e.g., session start)
    """
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class StreamEventType(str, Enum):
    """
    Types of WebSocket streaming events.

    Attributes:
        ASSISTANT_START: AI response starting
        ASSISTANT_CHUNK: Partial response text
        ASSISTANT_END: AI response complete
        AUDIO_READY: TTS audio available
        ERROR: An error occurred
        SESSION_STARTED: Session initialized
        SESSION_ENDED: Session terminated
    """
    ASSISTANT_START = "assistant_start"
    ASSISTANT_CHUNK = "assistant_chunk"
    ASSISTANT_END = "assistant_end"
    AUDIO_READY = "audio_ready"
    ERROR = "error"
    SESSION_STARTED = "session_started"
    SESSION_ENDED = "session_ended"


# ============================================================
# Chat Message Models
# ============================================================

class ChatMessage(BaseModel):
    """
    A single message in the conversation.

    Attributes:
        id: Unique message identifier
        role: Who sent the message
        content: Text content of the message
        timestamp: When the message was sent
        audio_url: URL to TTS audio (assistant messages only)
    """
    id: str = Field(..., description="Unique message identifier")
    role: MessageRole = Field(..., description="Message sender role")
    content: str = Field(..., description="Message text content")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    audio_url: Optional[str] = Field(None, description="TTS audio URL for playback")


# ============================================================
# Session Models
# ============================================================

class SessionRequest(BaseModel):
    """
    Request to start a new interactive session.

    Attributes:
        job_id: Job ID of the podcast to discuss
    """
    job_id: str = Field(..., description="Podcast job ID for context")


class SessionResponse(BaseModel):
    """
    Response after starting a session.

    Attributes:
        session_id: Unique session identifier
        job_id: Associated podcast job ID
        created_at: Session creation time
        welcome_message: Initial greeting from assistant
    """
    session_id: str = Field(..., description="Unique session identifier")
    job_id: str = Field(..., description="Associated podcast job ID")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    welcome_message: ChatMessage = Field(..., description="Initial assistant greeting")


# ============================================================
# Message Request/Response Models
# ============================================================

class MessageRequest(BaseModel):
    """
    Request to send a text message.

    Attributes:
        content: User's message text
        generate_audio: Whether to generate TTS response audio
    """
    content: str = Field(..., min_length=1, max_length=2000, description="Message text")
    generate_audio: bool = Field(True, description="Generate TTS for response")


class MessageResponse(BaseModel):
    """
    Response to a user message (non-streaming).

    Attributes:
        user_message: The user's message that was sent
        assistant_message: The AI's response
    """
    user_message: ChatMessage = Field(..., description="User's sent message")
    assistant_message: ChatMessage = Field(..., description="AI response")


class VoiceMessageRequest(BaseModel):
    """
    Request metadata for voice message upload.

    Attributes:
        generate_audio: Whether to generate TTS response audio
    """
    generate_audio: bool = Field(True, description="Generate TTS for response")


class TranscriptionResponse(BaseModel):
    """
    Response from voice transcription.

    Attributes:
        transcription: Transcribed text from audio
        confidence: Transcription confidence score (0-1)
        duration_seconds: Audio duration
    """
    transcription: str = Field(..., description="Transcribed text")
    confidence: float = Field(..., ge=0, le=1, description="Confidence score")
    duration_seconds: Optional[float] = Field(None, description="Audio duration")


# ============================================================
# History Models
# ============================================================

class HistoryResponse(BaseModel):
    """
    Conversation history for a session.

    Attributes:
        session_id: Session identifier
        messages: List of messages in chronological order
        total: Total message count
    """
    session_id: str = Field(..., description="Session identifier")
    messages: List[ChatMessage] = Field(default_factory=list)
    total: int = Field(0, ge=0)


# ============================================================
# WebSocket Stream Models
# ============================================================

class StreamMessage(BaseModel):
    """
    WebSocket message for real-time streaming.

    Attributes:
        type: Event type
        session_id: Session this event belongs to
        message_id: Message ID (for chunk events)
        content: Text content (for chunk events)
        audio_url: Audio URL (for audio_ready events)
        error: Error message (for error events)
    """
    type: StreamEventType = Field(..., description="Event type")
    session_id: str = Field(..., description="Session identifier")
    message_id: Optional[str] = Field(None, description="Message ID")
    content: Optional[str] = Field(None, description="Text content")
    audio_url: Optional[str] = Field(None, description="Audio URL")
    error: Optional[str] = Field(None, description="Error message")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ClientMessage(BaseModel):
    """
    Message from WebSocket client.

    Attributes:
        type: Message type (message, ping, end_session)
        content: Message content (for message type)
        generate_audio: Whether to generate TTS
    """
    type: Literal["message", "ping", "end_session"] = Field(..., description="Message type")
    content: Optional[str] = Field(None, description="Message content")
    generate_audio: bool = Field(True, description="Generate TTS for response")


# ============================================================
# Session Info Models
# ============================================================

class SessionInfo(BaseModel):
    """
    Information about an active session.

    Attributes:
        session_id: Session identifier
        job_id: Associated podcast job ID
        created_at: When session started
        message_count: Number of messages exchanged
        is_active: Whether session is still active
    """
    session_id: str
    job_id: str
    created_at: datetime
    message_count: int = 0
    is_active: bool = True
