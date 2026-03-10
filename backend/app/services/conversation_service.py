"""
Conversation service for interactive podcast discussions.

Manages chat sessions with podcast context awareness,
handling message flow, Claude integration, and streaming responses.
"""

import uuid
import asyncio
import json
from datetime import datetime
from typing import Dict, List, Optional, AsyncIterator
from dataclasses import dataclass, field
import threading

from anthropic import Anthropic, AsyncAnthropic

from ..models.interactive import (
    ChatMessage,
    MessageRole,
    SessionResponse,
    HistoryResponse,
    SessionInfo,
)
from ..logging_config import get_logger
from ..config import get_settings
from .memory_service import get_memory_service

logger = get_logger("conversation_service")

# Session ID length (8 characters for readability)
SESSION_ID_LENGTH = 8

# Claude model for conversations (Sonnet for speed)
CONVERSATION_MODEL = "claude-sonnet-4-6"

# Maximum messages to keep in context
MAX_CONTEXT_MESSAGES = 20

# Maximum script context tokens (approximate)
MAX_SCRIPT_CONTEXT_CHARS = 12000


@dataclass
class SessionState:
    """
    Internal session state representation.

    Attributes:
        id: Unique session identifier
        job_id: Associated podcast job ID
        created_at: Session creation timestamp
        messages: Conversation history
        script_context: Podcast script for context
        voice_id: Voice ID used in podcast (for TTS responses)
        is_active: Whether session is still active
        user_id: Optional user ID for memory personalization
    """
    id: str
    job_id: str
    created_at: datetime
    messages: List[ChatMessage] = field(default_factory=list)
    script_context: Optional[str] = None
    voice_id: Optional[str] = None
    is_active: bool = True
    user_id: Optional[str] = None


class ConversationService:
    """
    Manages interactive conversations with podcast context.

    Provides session management, message handling, and
    streaming responses using Claude.

    Attributes:
        _sessions: Dictionary mapping session IDs to session state
        _job_sessions: Dictionary mapping job IDs to session IDs
        _lock: Thread lock for safe concurrent access
        _client: Anthropic client for streaming
    """

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the conversation service.

        Args:
            api_key: Anthropic API key. Uses settings if not provided.
        """
        self._sessions: Dict[str, SessionState] = {}
        self._job_sessions: Dict[str, str] = {}
        self._lock = threading.RLock()

        # Get API key from parameter or settings
        settings = get_settings()
        actual_api_key = api_key or settings.anthropic_api_key

        if not actual_api_key:
            logger.warning(
                "No Anthropic API key configured. "
                "Interactive chat will not work until ANTHROPIC_API_KEY is set."
            )
            self._client = None
        else:
            self._client = AsyncAnthropic(
                api_key=actual_api_key,
                timeout=120.0
            )

    async def start_session(
        self,
        job_id: str,
        script: Optional[Dict] = None,
        voice_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> SessionResponse:
        """
        Start a new interactive session for a podcast.

        Args:
            job_id: Podcast job ID for context.
            script: Enhanced script data (if available).
            voice_id: Voice ID from podcast (for TTS responses).
            user_id: Optional user ID for memory personalization.

        Returns:
            SessionResponse with session details and welcome message.
        """
        # Check for existing session
        with self._lock:
            existing_session_id = self._job_sessions.get(job_id)
            if existing_session_id and existing_session_id in self._sessions:
                session = self._sessions[existing_session_id]
                if session.is_active:
                    # Return existing session
                    welcome = session.messages[0] if session.messages else self._create_welcome_message(existing_session_id)
                    return SessionResponse(
                        session_id=existing_session_id,
                        job_id=job_id,
                        created_at=session.created_at,
                        welcome_message=welcome,
                    )

        # Create new session
        session_id = str(uuid.uuid4())[:SESSION_ID_LENGTH]

        # Build script context
        script_context = self._build_script_context(script) if script else None

        # Create session state
        session_state = SessionState(
            id=session_id,
            job_id=job_id,
            created_at=datetime.utcnow(),
            script_context=script_context,
            voice_id=voice_id,
            is_active=True,
            user_id=user_id,
        )

        # Create welcome message
        welcome_message = self._create_welcome_message(session_id)
        session_state.messages.append(welcome_message)

        # Store session
        with self._lock:
            self._sessions[session_id] = session_state
            self._job_sessions[job_id] = session_id

        logger.info("Started session %s for job %s", session_id, job_id)

        return SessionResponse(
            session_id=session_id,
            job_id=job_id,
            created_at=session_state.created_at,
            welcome_message=welcome_message,
        )

    async def send_message(
        self,
        session_id: str,
        content: str,
    ) -> AsyncIterator[str]:
        """
        Send a message and stream the response.

        Args:
            session_id: Session identifier.
            content: User's message text.

        Yields:
            Response text chunks as they arrive.

        Raises:
            ValueError: If session not found or inactive.
        """
        with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                raise ValueError(f"Session not found: {session_id}")
            if not session.is_active:
                raise ValueError(f"Session is no longer active: {session_id}")

        # Create user message
        user_message = ChatMessage(
            id=str(uuid.uuid4())[:SESSION_ID_LENGTH],
            role=MessageRole.USER,
            content=content,
            timestamp=datetime.utcnow(),
        )

        # Add to history
        with self._lock:
            session.messages.append(user_message)

        # Build messages for Claude
        claude_messages = self._build_claude_messages(session)

        # Build system prompt with podcast context
        system_prompt = self._build_system_prompt(session)

        # Generate response ID
        response_id = str(uuid.uuid4())[:SESSION_ID_LENGTH]
        full_response = ""

        # Check if client is available
        if self._client is None:
            error_text = "Chat is unavailable. Please check API key configuration."
            logger.error("Anthropic client not initialized - API key missing")
            yield error_text
            # Create and store error message
            assistant_message = ChatMessage(
                id=response_id,
                role=MessageRole.ASSISTANT,
                content=error_text,
                timestamp=datetime.utcnow(),
            )
            with self._lock:
                session.messages.append(assistant_message)
            return

        try:
            # Stream response from Claude
            async with self._client.messages.stream(
                model=CONVERSATION_MODEL,
                max_tokens=1024,
                system=system_prompt,
                messages=claude_messages,
            ) as stream:
                async for text in stream.text_stream:
                    full_response += text
                    yield text

        except Exception as e:
            logger.error(
                "Error streaming response for session %s: %s: %s",
                session_id,
                type(e).__name__,
                str(e),
                exc_info=True
            )
            error_text = "I apologize, but I encountered an error. Please try again."
            full_response = error_text
            yield error_text

        # Create assistant message and add to history
        assistant_message = ChatMessage(
            id=response_id,
            role=MessageRole.ASSISTANT,
            content=full_response,
            timestamp=datetime.utcnow(),
        )

        with self._lock:
            session.messages.append(assistant_message)

        logger.debug("Completed response for session %s, message %s", session_id, response_id)

    async def send_message_sync(
        self,
        session_id: str,
        content: str,
    ) -> ChatMessage:
        """
        Send a message and return the complete response (non-streaming).

        Args:
            session_id: Session identifier.
            content: User's message text.

        Returns:
            Assistant's response message.

        Raises:
            ValueError: If session not found or inactive.
        """
        full_response = ""
        async for chunk in self.send_message(session_id, content):
            full_response += chunk

        # Get the assistant message from session
        with self._lock:
            session = self._sessions.get(session_id)
            if session and session.messages:
                return session.messages[-1]

        # Fallback
        return ChatMessage(
            id=str(uuid.uuid4())[:SESSION_ID_LENGTH],
            role=MessageRole.ASSISTANT,
            content=full_response,
            timestamp=datetime.utcnow(),
        )

    def get_history(self, session_id: str) -> HistoryResponse:
        """
        Get conversation history for a session.

        Args:
            session_id: Session identifier.

        Returns:
            HistoryResponse with all messages.

        Raises:
            ValueError: If session not found.
        """
        with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                raise ValueError(f"Session not found: {session_id}")

            return HistoryResponse(
                session_id=session_id,
                messages=list(session.messages),
                total=len(session.messages),
            )

    def get_session(self, session_id: str) -> Optional[SessionInfo]:
        """
        Get session information.

        Args:
            session_id: Session identifier.

        Returns:
            SessionInfo if found, None otherwise.
        """
        with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                return None

            return SessionInfo(
                session_id=session.id,
                job_id=session.job_id,
                created_at=session.created_at,
                message_count=len(session.messages),
                is_active=session.is_active,
            )

    def get_session_for_job(self, job_id: str) -> Optional[str]:
        """
        Get active session ID for a job.

        Args:
            job_id: Podcast job ID.

        Returns:
            Session ID if active session exists, None otherwise.
        """
        with self._lock:
            session_id = self._job_sessions.get(job_id)
            if session_id and session_id in self._sessions:
                session = self._sessions[session_id]
                if session.is_active:
                    return session_id
        return None

    def get_voice_id(self, session_id: str) -> Optional[str]:
        """
        Get the voice ID for a session.

        Args:
            session_id: Session identifier.

        Returns:
            Voice ID if set, None otherwise.
        """
        with self._lock:
            session = self._sessions.get(session_id)
            return session.voice_id if session else None

    def get_last_assistant_message(self, session_id: str) -> Optional[ChatMessage]:
        """
        Get the last assistant message for a session.

        Args:
            session_id: Session identifier.

        Returns:
            Last assistant message if found.
        """
        with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                return None

            for msg in reversed(session.messages):
                if msg.role == MessageRole.ASSISTANT:
                    return msg
        return None

    def update_message_audio(
        self,
        session_id: str,
        message_id: str,
        audio_url: str,
    ) -> bool:
        """
        Update a message with audio URL.

        Args:
            session_id: Session identifier.
            message_id: Message identifier.
            audio_url: URL to TTS audio.

        Returns:
            True if message was updated.
        """
        with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                return False

            for msg in session.messages:
                if msg.id == message_id:
                    msg.audio_url = audio_url
                    return True
        return False

    def end_session(self, session_id: str) -> bool:
        """
        End an interactive session.

        Args:
            session_id: Session identifier.

        Returns:
            True if session was ended.
        """
        with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                return False

            session.is_active = False

            # Remove from job mapping
            if session.job_id in self._job_sessions:
                if self._job_sessions[session.job_id] == session_id:
                    del self._job_sessions[session.job_id]

        logger.info("Ended session %s", session_id)
        return True

    def _create_welcome_message(self, session_id: str) -> ChatMessage:
        """Create the initial welcome message."""
        return ChatMessage(
            id=str(uuid.uuid4())[:SESSION_ID_LENGTH],
            role=MessageRole.ASSISTANT,
            content=(
                "Hello! I'm here to discuss the podcast with you. "
                "Feel free to ask me anything about the content, "
                "request clarifications, or explore topics further. "
                "How can I help you?"
            ),
            timestamp=datetime.utcnow(),
        )

    def _build_script_context(self, script: Dict) -> str:
        """
        Build a condensed context string from the script.

        Args:
            script: Enhanced script data.

        Returns:
            Condensed script context for Claude.
        """
        context_parts = []

        # Add title and hook
        if "title" in script:
            context_parts.append(f"Title: {script['title']}")

        if "hook" in script:
            hook = script["hook"]
            if isinstance(hook, dict):
                hook_text = hook.get("text", "")
            else:
                hook_text = str(hook)
            context_parts.append(f"Introduction: {hook_text[:500]}")

        # Add module summaries
        if "modules" in script:
            for i, module in enumerate(script["modules"], 1):
                module_title = module.get("title", f"Section {i}")
                context_parts.append(f"\n--- {module_title} ---")

                # Add chunks
                if "chunks" in module:
                    for chunk in module["chunks"]:
                        chunk_text = chunk.get("text", "")
                        context_parts.append(chunk_text[:300])

        # Add conclusion
        if "conclusion" in script:
            conclusion = script["conclusion"]
            if isinstance(conclusion, dict):
                conclusion_text = conclusion.get("text", "")
            else:
                conclusion_text = str(conclusion)
            context_parts.append(f"\nConclusion: {conclusion_text[:500]}")

        full_context = "\n".join(context_parts)

        # Truncate if too long
        if len(full_context) > MAX_SCRIPT_CONTEXT_CHARS:
            full_context = full_context[:MAX_SCRIPT_CONTEXT_CHARS] + "..."

        return full_context

    def _build_system_prompt(self, session: SessionState) -> str:
        """
        Build the system prompt with podcast context and user memory.

        Args:
            session: Session state.

        Returns:
            System prompt for Claude.
        """
        base_prompt = """You are Nell, a warm and knowledgeable AI assistant discussing podcasts.
You have full knowledge of the podcast content and can answer questions,
provide clarifications, and engage in deeper discussions about the topics covered.

Guidelines:
- Be conversational and friendly, like talking to a thoughtful friend
- Reference specific parts of the podcast when relevant
- Provide additional context or explanations when asked
- Keep responses concise but informative (2-4 sentences typically)
- If asked about something not in the podcast, acknowledge it and provide general knowledge
- Encourage exploration of the topics
- If the user interrupts you, adapt gracefully and listen to what they want to say"""

        prompt_parts = [base_prompt]

        # Add user memory context if available
        if session.user_id:
            try:
                memory_service = get_memory_service()
                memory_prompt = memory_service.build_memory_prompt(session.user_id)
                if memory_prompt:
                    prompt_parts.append(f"""
=== ABOUT THIS USER ===
{memory_prompt}

Use this context to personalize your responses. Reference past conversations
naturally when relevant (e.g., "You mentioned before..." or "Since you're interested in...").
=== END USER CONTEXT ===""")
            except Exception as e:
                logger.warning("Failed to load user memory: %s", str(e))

        # Add podcast content
        if session.script_context:
            prompt_parts.append(f"""
=== PODCAST CONTENT ===
{session.script_context}
=== END PODCAST CONTENT ===

Use the podcast content above to inform your responses.
When referencing specific sections, you can mention them naturally in conversation.""")

        return "\n".join(prompt_parts)

    def _build_claude_messages(self, session: SessionState) -> List[Dict]:
        """
        Build message list for Claude API.

        Args:
            session: Session state.

        Returns:
            List of message dicts for Claude.
        """
        messages = []

        # Get recent messages (skip system/welcome)
        recent_messages = session.messages[-MAX_CONTEXT_MESSAGES:]

        for msg in recent_messages:
            if msg.role == MessageRole.USER:
                messages.append({
                    "role": "user",
                    "content": msg.content,
                })
            elif msg.role == MessageRole.ASSISTANT:
                messages.append({
                    "role": "assistant",
                    "content": msg.content,
                })

        return messages


# Global conversation service singleton
_conversation_service: Optional[ConversationService] = None


def get_conversation_service() -> ConversationService:
    """Get or create the conversation service singleton."""
    global _conversation_service
    if _conversation_service is None:
        _conversation_service = ConversationService()
    return _conversation_service
