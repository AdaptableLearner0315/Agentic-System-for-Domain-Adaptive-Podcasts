"""
Interactive TTS service for voice responses.

Generates speech audio for interactive conversation responses
using the same voice as the podcast narrator.
"""

import os
import asyncio
import tempfile
import uuid
from pathlib import Path
from typing import Optional, Dict

from ..logging_config import get_logger
from ..config import get_settings

logger = get_logger("interactive_tts_service")

# Default voice for interactive responses
DEFAULT_INTERACTIVE_VOICE = "Friendly_Female_English"


class InteractiveTTSService:
    """
    TTS service for interactive conversation responses.

    Generates speech audio using MiniMax Speech-01-HD,
    matching the podcast narrator voice.

    Attributes:
        _voice_id: Default voice ID for responses
        _output_dir: Directory for generated audio files
    """

    def __init__(
        self,
        voice_id: Optional[str] = None,
        output_dir: Optional[Path] = None,
    ):
        """
        Initialize the interactive TTS service.

        Args:
            voice_id: MiniMax voice ID (defaults to Friendly_Female_English).
            output_dir: Directory for audio files.
        """
        self._voice_id = voice_id or DEFAULT_INTERACTIVE_VOICE
        settings = get_settings()
        self._output_dir = output_dir or (settings.output_path / "interactive_audio")
        self._output_dir.mkdir(parents=True, exist_ok=True)

    async def generate_response_audio(
        self,
        text: str,
        message_id: str,
        voice_id: Optional[str] = None,
    ) -> Optional[str]:
        """
        Generate TTS audio for a response message.

        Args:
            text: Text to convert to speech.
            message_id: Message ID for file naming.
            voice_id: Override voice ID (uses session voice if not provided).

        Returns:
            URL path to the audio file, or None if generation fails.
        """
        try:
            import fal_client
            import requests
        except ImportError:
            logger.error("fal_client or requests not installed")
            return None

        if not os.environ.get("FAL_KEY"):
            logger.error("FAL_KEY environment variable is not set")
            return None

        # Use provided voice or default
        actual_voice_id = voice_id or self._voice_id

        # Preprocess text for TTS
        processed_text = self._preprocess_text(text)

        # Generate unique filename
        filename = f"response_{message_id}.wav"
        output_path = self._output_dir / filename

        logger.debug("Generating TTS for message %s...", message_id)

        try:
            # Call Fal AI MiniMax Speech-01-HD
            result = await asyncio.to_thread(
                fal_client.subscribe,
                'fal-ai/minimax/speech-01-hd',
                arguments={
                    'text': processed_text,
                    'voice_id': actual_voice_id,
                    'speed': 1.0,
                },
                with_logs=False,
            )

            # Extract audio URL from response
            audio_url = self._extract_audio_url(result)

            if not audio_url:
                logger.error("No audio URL in TTS response")
                return None

            # Download audio file
            response = await asyncio.to_thread(requests.get, audio_url)

            if response.status_code != 200:
                logger.error("Failed to download audio: %s", response.status_code)
                return None

            # Save audio file
            with open(output_path, 'wb') as f:
                f.write(response.content)

            logger.info("Generated audio: %s", output_path.name)

            # Return URL path for API access
            return f"/api/interactive/audio/{message_id}"

        except Exception as e:
            logger.error("TTS generation failed: %s", e)
            return None

    def get_audio_path(self, message_id: str) -> Optional[Path]:
        """
        Get the file path for a message's audio.

        Args:
            message_id: Message identifier.

        Returns:
            Path to audio file if it exists.
        """
        filename = f"response_{message_id}.wav"
        path = self._output_dir / filename

        if path.exists():
            return path
        return None

    def _preprocess_text(self, text: str) -> str:
        """
        Preprocess text for better TTS output.

        Args:
            text: Raw text.

        Returns:
            Processed text.
        """
        # Remove markdown formatting
        processed = text.replace('**', '')
        processed = processed.replace('*', '')
        processed = processed.replace('`', '')
        processed = processed.replace('#', '')

        # Handle common TTS issues
        replacements = {
            ' - ': ', ',
            '...': '.',
            '!!': '!',
            '??': '?',
        }

        for old, new in replacements.items():
            processed = processed.replace(old, new)

        return processed.strip()

    def _extract_audio_url(self, result: Dict) -> Optional[str]:
        """
        Extract audio URL from Fal AI response.

        Args:
            result: Response dictionary.

        Returns:
            Audio URL or None.
        """
        if not isinstance(result, dict):
            return None

        # Try different response formats
        audio_url = result.get('audio_url')

        if not audio_url:
            audio = result.get('audio')
            if isinstance(audio, dict):
                audio_url = audio.get('url')
            elif isinstance(audio, str):
                audio_url = audio

        if not audio_url:
            audio_file = result.get('audio_file')
            if isinstance(audio_file, dict):
                audio_url = audio_file.get('url')

        return audio_url


# Global service singleton
_tts_service: Optional[InteractiveTTSService] = None


def get_interactive_tts_service() -> InteractiveTTSService:
    """Get or create the interactive TTS service singleton."""
    global _tts_service
    if _tts_service is None:
        _tts_service = InteractiveTTSService()
    return _tts_service


async def generate_response_audio(
    text: str,
    message_id: str,
    voice_id: Optional[str] = None,
) -> Optional[str]:
    """
    Convenience function to generate response audio.

    Args:
        text: Text to convert to speech.
        message_id: Message identifier.
        voice_id: Optional voice override.

    Returns:
        URL path to audio or None.
    """
    service = get_interactive_tts_service()
    return await service.generate_response_audio(text, message_id, voice_id)
