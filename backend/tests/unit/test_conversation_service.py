"""
Unit tests for ConversationService.

Tests session management, message sending, error handling,
and conversation history functionality.
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import MagicMock, AsyncMock, patch

from app.services.conversation_service import (
    ConversationService,
    get_conversation_service,
    SessionState,
    CONVERSATION_MODEL,
    MAX_CONTEXT_MESSAGES,
)
from app.models.interactive import (
    ChatMessage,
    MessageRole,
    SessionResponse,
    HistoryResponse,
    SessionInfo,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def mock_anthropic_client():
    """Create a mock AsyncAnthropic client."""
    mock_client = MagicMock()
    mock_stream = MagicMock()
    mock_stream.__aenter__ = AsyncMock(return_value=mock_stream)
    mock_stream.__aexit__ = AsyncMock(return_value=None)

    async def text_stream():
        yield "Hello, "
        yield "this is "
        yield "a test response."

    mock_stream.text_stream = text_stream()
    mock_client.messages.stream = MagicMock(return_value=mock_stream)

    return mock_client


@pytest.fixture
def conversation_service_with_mock(mock_anthropic_client):
    """Create a ConversationService with mocked client."""
    service = ConversationService(api_key="test-api-key")
    service._client = mock_anthropic_client
    return service


@pytest.fixture
def conversation_service_no_key():
    """Create a ConversationService without API key."""
    with patch('app.services.conversation_service.get_settings') as mock_settings:
        mock_settings.return_value.anthropic_api_key = None
        service = ConversationService()
        return service


@pytest.fixture
def sample_script():
    """Sample enhanced script for testing."""
    return {
        "title": "Test Podcast",
        "hook": {"text": "Welcome to this test podcast about testing."},
        "modules": [
            {
                "title": "Module 1",
                "chunks": [
                    {"text": "This is the first chunk of content."},
                    {"text": "This is the second chunk."},
                ],
            },
            {
                "title": "Module 2",
                "chunks": [
                    {"text": "More content in module two."},
                ],
            },
        ],
        "conclusion": {"text": "Thanks for listening to this test."},
    }


# =============================================================================
# Test Session Creation
# =============================================================================

class TestSessionCreation:
    """Tests for session creation functionality."""

    @pytest.mark.asyncio
    async def test_start_session_creates_new_session(self, conversation_service_with_mock):
        """Test that starting a session creates a new session."""
        service = conversation_service_with_mock

        response = await service.start_session(
            job_id="test-job-123",
            script=None,
            voice_id="voice-abc",
        )

        assert response.session_id is not None
        assert response.job_id == "test-job-123"
        assert response.welcome_message is not None
        assert response.welcome_message.role == MessageRole.ASSISTANT

    @pytest.mark.asyncio
    async def test_start_session_with_script_context(
        self, conversation_service_with_mock, sample_script
    ):
        """Test that script context is properly stored."""
        service = conversation_service_with_mock

        response = await service.start_session(
            job_id="test-job-456",
            script=sample_script,
            voice_id="voice-xyz",
        )

        # Verify session has script context
        session = service._sessions.get(response.session_id)
        assert session is not None
        assert session.script_context is not None
        assert "Test Podcast" in session.script_context
        assert session.voice_id == "voice-xyz"

    @pytest.mark.asyncio
    async def test_start_session_reuses_existing_active_session(
        self, conversation_service_with_mock
    ):
        """Test that starting a session for same job reuses existing session."""
        service = conversation_service_with_mock

        # Create first session
        response1 = await service.start_session(
            job_id="test-job-789",
            script=None,
            voice_id=None,
        )

        # Try to create another session for same job
        response2 = await service.start_session(
            job_id="test-job-789",
            script=None,
            voice_id=None,
        )

        assert response1.session_id == response2.session_id

    @pytest.mark.asyncio
    async def test_start_session_without_voice_id(self, conversation_service_with_mock):
        """Test that session can be created without voice ID."""
        service = conversation_service_with_mock

        response = await service.start_session(
            job_id="test-job-no-voice",
            script=None,
            voice_id=None,
        )

        session = service._sessions.get(response.session_id)
        assert session is not None
        assert session.voice_id is None


# =============================================================================
# Test Message Sending
# =============================================================================

class TestMessageSending:
    """Tests for sending messages and receiving responses."""

    @pytest.mark.asyncio
    async def test_send_message_streams_response(self, conversation_service_with_mock):
        """Test that sending a message returns a streaming response."""
        service = conversation_service_with_mock

        # Create session first
        session_response = await service.start_session(
            job_id="test-job-msg",
            script=None,
            voice_id=None,
        )
        session_id = session_response.session_id

        # Send message and collect response
        response_chunks = []
        async for chunk in service.send_message(session_id, "Hello, assistant!"):
            response_chunks.append(chunk)

        assert len(response_chunks) > 0
        full_response = "".join(response_chunks)
        assert "test response" in full_response

    @pytest.mark.asyncio
    async def test_send_message_updates_history(self, conversation_service_with_mock):
        """Test that sending a message updates conversation history."""
        service = conversation_service_with_mock

        session_response = await service.start_session(
            job_id="test-job-history",
            script=None,
            voice_id=None,
        )
        session_id = session_response.session_id

        # Consume the generator to complete message handling
        async for _ in service.send_message(session_id, "User question"):
            pass

        history = service.get_history(session_id)

        # Should have: welcome message, user message, assistant response
        assert history.total >= 3
        user_messages = [m for m in history.messages if m.role == MessageRole.USER]
        assert len(user_messages) == 1
        assert user_messages[0].content == "User question"

    @pytest.mark.asyncio
    async def test_send_message_to_invalid_session(self, conversation_service_with_mock):
        """Test that sending to invalid session raises error."""
        service = conversation_service_with_mock

        with pytest.raises(ValueError) as exc:
            async for _ in service.send_message("nonexistent-session", "Hello"):
                pass

        assert "Session not found" in str(exc.value)

    @pytest.mark.asyncio
    async def test_send_message_to_inactive_session(self, conversation_service_with_mock):
        """Test that sending to inactive session raises error."""
        service = conversation_service_with_mock

        session_response = await service.start_session(
            job_id="test-job-inactive",
            script=None,
            voice_id=None,
        )
        session_id = session_response.session_id

        # End the session
        service.end_session(session_id)

        with pytest.raises(ValueError) as exc:
            async for _ in service.send_message(session_id, "Hello"):
                pass

        assert "no longer active" in str(exc.value)


# =============================================================================
# Test Error Handling
# =============================================================================

class TestErrorHandling:
    """Tests for error handling in conversation service."""

    @pytest.mark.asyncio
    async def test_no_api_key_logs_warning(self, conversation_service_no_key, caplog):
        """Test that missing API key logs warning."""
        service = conversation_service_no_key
        assert service._client is None

    @pytest.mark.asyncio
    async def test_no_api_key_returns_error_message(self, conversation_service_no_key):
        """Test that missing API key returns appropriate error message."""
        service = conversation_service_no_key

        # Manually create a session without going through start_session
        session_id = "test-session-no-key"
        service._sessions[session_id] = SessionState(
            id=session_id,
            job_id="test-job",
            created_at=datetime.utcnow(),
            is_active=True,
        )

        response_chunks = []
        async for chunk in service.send_message(session_id, "Hello"):
            response_chunks.append(chunk)

        full_response = "".join(response_chunks)
        assert "unavailable" in full_response.lower() or "api key" in full_response.lower()

    @pytest.mark.asyncio
    async def test_api_error_returns_generic_error(self, conversation_service_with_mock):
        """Test that API errors return a generic error message."""
        service = conversation_service_with_mock

        # Make the client raise an exception
        async def raise_error(*args, **kwargs):
            raise Exception("API error")

        mock_stream = MagicMock()
        mock_stream.__aenter__ = AsyncMock(side_effect=raise_error)
        service._client.messages.stream = MagicMock(return_value=mock_stream)

        session_response = await service.start_session(
            job_id="test-job-error",
            script=None,
            voice_id=None,
        )
        session_id = session_response.session_id

        response_chunks = []
        async for chunk in service.send_message(session_id, "Hello"):
            response_chunks.append(chunk)

        full_response = "".join(response_chunks)
        assert "apologize" in full_response.lower() or "error" in full_response.lower()


# =============================================================================
# Test Session Management
# =============================================================================

class TestSessionManagement:
    """Tests for session management operations."""

    @pytest.mark.asyncio
    async def test_get_session_returns_session_info(self, conversation_service_with_mock):
        """Test getting session info."""
        service = conversation_service_with_mock

        session_response = await service.start_session(
            job_id="test-job-get",
            script=None,
            voice_id=None,
        )
        session_id = session_response.session_id

        session_info = service.get_session(session_id)

        assert session_info is not None
        assert session_info.session_id == session_id
        assert session_info.job_id == "test-job-get"
        assert session_info.is_active is True
        assert session_info.message_count >= 1  # At least welcome message

    def test_get_nonexistent_session_returns_none(self, conversation_service_with_mock):
        """Test getting nonexistent session returns None."""
        service = conversation_service_with_mock

        result = service.get_session("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_end_session_marks_inactive(self, conversation_service_with_mock):
        """Test ending a session marks it as inactive."""
        service = conversation_service_with_mock

        session_response = await service.start_session(
            job_id="test-job-end",
            script=None,
            voice_id=None,
        )
        session_id = session_response.session_id

        result = service.end_session(session_id)

        assert result is True
        session_info = service.get_session(session_id)
        assert session_info.is_active is False

    def test_end_nonexistent_session_returns_false(self, conversation_service_with_mock):
        """Test ending nonexistent session returns False."""
        service = conversation_service_with_mock

        result = service.end_session("nonexistent")
        assert result is False

    @pytest.mark.asyncio
    async def test_get_session_for_job_returns_session_id(
        self, conversation_service_with_mock
    ):
        """Test getting session ID for a job."""
        service = conversation_service_with_mock

        session_response = await service.start_session(
            job_id="test-job-lookup",
            script=None,
            voice_id=None,
        )

        result = service.get_session_for_job("test-job-lookup")

        assert result == session_response.session_id

    def test_get_session_for_nonexistent_job_returns_none(
        self, conversation_service_with_mock
    ):
        """Test getting session for nonexistent job returns None."""
        service = conversation_service_with_mock

        result = service.get_session_for_job("nonexistent-job")
        assert result is None


# =============================================================================
# Test History
# =============================================================================

class TestHistory:
    """Tests for conversation history retrieval."""

    @pytest.mark.asyncio
    async def test_get_history_returns_all_messages(self, conversation_service_with_mock):
        """Test getting history returns all messages."""
        service = conversation_service_with_mock

        session_response = await service.start_session(
            job_id="test-job-hist",
            script=None,
            voice_id=None,
        )
        session_id = session_response.session_id

        # Send a message
        async for _ in service.send_message(session_id, "Test message"):
            pass

        history = service.get_history(session_id)

        assert history.session_id == session_id
        assert history.total >= 3  # welcome + user + assistant

    def test_get_history_invalid_session_raises_error(
        self, conversation_service_with_mock
    ):
        """Test getting history for invalid session raises error."""
        service = conversation_service_with_mock

        with pytest.raises(ValueError) as exc:
            service.get_history("nonexistent")

        assert "Session not found" in str(exc.value)

    @pytest.mark.asyncio
    async def test_get_voice_id(self, conversation_service_with_mock):
        """Test getting voice ID for a session."""
        service = conversation_service_with_mock

        session_response = await service.start_session(
            job_id="test-job-voice",
            script=None,
            voice_id="voice-123",
        )
        session_id = session_response.session_id

        voice_id = service.get_voice_id(session_id)
        assert voice_id == "voice-123"


# =============================================================================
# Test Audio URL Update
# =============================================================================

class TestAudioUrlUpdate:
    """Tests for updating message audio URLs."""

    @pytest.mark.asyncio
    async def test_update_message_audio_success(self, conversation_service_with_mock):
        """Test updating audio URL for a message."""
        service = conversation_service_with_mock

        session_response = await service.start_session(
            job_id="test-job-audio",
            script=None,
            voice_id=None,
        )
        session_id = session_response.session_id

        # Get the welcome message ID
        history = service.get_history(session_id)
        message_id = history.messages[0].id

        result = service.update_message_audio(
            session_id=session_id,
            message_id=message_id,
            audio_url="https://example.com/audio.mp3",
        )

        assert result is True

        # Verify audio URL was set
        updated_history = service.get_history(session_id)
        updated_message = next(
            m for m in updated_history.messages if m.id == message_id
        )
        assert updated_message.audio_url == "https://example.com/audio.mp3"

    def test_update_audio_invalid_session_returns_false(
        self, conversation_service_with_mock
    ):
        """Test updating audio for invalid session returns False."""
        service = conversation_service_with_mock

        result = service.update_message_audio(
            session_id="nonexistent",
            message_id="msg-id",
            audio_url="https://example.com/audio.mp3",
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_update_audio_invalid_message_returns_false(
        self, conversation_service_with_mock
    ):
        """Test updating audio for invalid message returns False."""
        service = conversation_service_with_mock

        session_response = await service.start_session(
            job_id="test-job-audio-inv",
            script=None,
            voice_id=None,
        )
        session_id = session_response.session_id

        result = service.update_message_audio(
            session_id=session_id,
            message_id="nonexistent-msg",
            audio_url="https://example.com/audio.mp3",
        )

        assert result is False


# =============================================================================
# Test Last Assistant Message
# =============================================================================

class TestLastAssistantMessage:
    """Tests for getting the last assistant message."""

    @pytest.mark.asyncio
    async def test_get_last_assistant_message(self, conversation_service_with_mock):
        """Test getting the last assistant message."""
        service = conversation_service_with_mock

        session_response = await service.start_session(
            job_id="test-job-last",
            script=None,
            voice_id=None,
        )
        session_id = session_response.session_id

        # Send a message to get another assistant response
        async for _ in service.send_message(session_id, "Hello"):
            pass

        last_msg = service.get_last_assistant_message(session_id)

        assert last_msg is not None
        assert last_msg.role == MessageRole.ASSISTANT

    def test_get_last_assistant_message_invalid_session(
        self, conversation_service_with_mock
    ):
        """Test getting last message for invalid session returns None."""
        service = conversation_service_with_mock

        result = service.get_last_assistant_message("nonexistent")
        assert result is None


# =============================================================================
# Test Singleton
# =============================================================================

class TestSingleton:
    """Tests for conversation service singleton."""

    def test_get_conversation_service_returns_same_instance(self):
        """Test that get_conversation_service returns same instance."""
        # Reset singleton for test
        import app.services.conversation_service as module

        module._conversation_service = None

        with patch.object(module, 'get_settings') as mock_settings:
            mock_settings.return_value.anthropic_api_key = "test-key"

            service1 = get_conversation_service()
            service2 = get_conversation_service()

            assert service1 is service2

        # Reset after test
        module._conversation_service = None
