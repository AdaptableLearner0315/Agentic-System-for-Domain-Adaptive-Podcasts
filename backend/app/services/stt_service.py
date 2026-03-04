"""
Speech-to-text service using Fal AI Whisper.

Provides async transcription of audio data for interactive
voice conversations.
"""

import os
import asyncio
import tempfile
from pathlib import Path
from typing import Dict, Optional

from ..logging_config import get_logger

logger = get_logger("stt_service")


class STTService:
    """
    Speech-to-text service using Fal AI Whisper.

    Handles audio transcription for voice input in interactive
    conversations.

    Attributes:
        _model: Whisper model identifier
    """

    def __init__(self, model: str = "fal-ai/whisper"):
        """
        Initialize the STT service.

        Args:
            model: Fal AI Whisper model identifier.
        """
        self._model = model

    async def transcribe(
        self,
        audio_data: bytes,
        language: Optional[str] = None,
    ) -> Dict:
        """
        Transcribe audio data to text.

        Args:
            audio_data: Raw audio bytes (webm, wav, mp3).
            language: Optional language code (auto-detected if not provided).

        Returns:
            Dictionary with:
                - text: Transcribed text
                - confidence: Confidence score (0-1)
                - duration: Audio duration in seconds (if available)

        Raises:
            RuntimeError: If transcription fails.
        """
        try:
            import fal_client
        except ImportError:
            raise RuntimeError("fal_client not installed. Run: pip install fal-client")

        # Check for API key
        if not os.environ.get("FAL_KEY"):
            raise RuntimeError("FAL_KEY environment variable is not set")

        # Save audio to temp file
        with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as f:
            f.write(audio_data)
            temp_path = f.name

        try:
            # Upload to Fal storage
            logger.debug("Uploading audio to Fal AI...")
            audio_url = await asyncio.to_thread(fal_client.upload_file, temp_path)

            # Build arguments
            arguments = {
                "audio_url": audio_url,
                "task": "transcribe",
                "version": "3",  # Whisper large-v3
            }

            if language:
                arguments["language"] = language

            # Run transcription
            logger.debug("Transcribing audio...")
            result = await asyncio.to_thread(
                fal_client.subscribe,
                self._model,
                arguments=arguments,
            )

            # Extract results
            text = result.get("text", "")
            chunks = result.get("chunks", [])

            # Calculate confidence from chunks if available
            confidence = 0.9  # Default confidence
            if chunks:
                chunk_confidences = [
                    c.get("confidence", 0.9)
                    for c in chunks
                    if "confidence" in c
                ]
                if chunk_confidences:
                    confidence = sum(chunk_confidences) / len(chunk_confidences)

            # Get duration if available
            duration = None
            if chunks and len(chunks) > 0:
                last_chunk = chunks[-1]
                if "timestamp" in last_chunk and len(last_chunk["timestamp"]) > 1:
                    duration = last_chunk["timestamp"][1]

            logger.info("Transcription complete: %d chars", len(text))

            return {
                "text": text.strip(),
                "confidence": confidence,
                "duration": duration,
            }

        finally:
            # Cleanup temp file
            try:
                Path(temp_path).unlink()
            except Exception:
                pass

    async def transcribe_url(
        self,
        audio_url: str,
        language: Optional[str] = None,
    ) -> Dict:
        """
        Transcribe audio from a URL.

        Args:
            audio_url: URL to audio file.
            language: Optional language code.

        Returns:
            Dictionary with text, confidence, and duration.
        """
        try:
            import fal_client
        except ImportError:
            raise RuntimeError("fal_client not installed")

        if not os.environ.get("FAL_KEY"):
            raise RuntimeError("FAL_KEY environment variable is not set")

        arguments = {
            "audio_url": audio_url,
            "task": "transcribe",
            "version": "3",
        }

        if language:
            arguments["language"] = language

        result = await asyncio.to_thread(
            fal_client.subscribe,
            self._model,
            arguments=arguments,
        )

        text = result.get("text", "")
        chunks = result.get("chunks", [])

        confidence = 0.9
        if chunks:
            chunk_confidences = [
                c.get("confidence", 0.9)
                for c in chunks
                if "confidence" in c
            ]
            if chunk_confidences:
                confidence = sum(chunk_confidences) / len(chunk_confidences)

        duration = None
        if chunks and len(chunks) > 0:
            last_chunk = chunks[-1]
            if "timestamp" in last_chunk and len(last_chunk["timestamp"]) > 1:
                duration = last_chunk["timestamp"][1]

        return {
            "text": text.strip(),
            "confidence": confidence,
            "duration": duration,
        }


# Global STT service singleton
_stt_service: Optional[STTService] = None


def get_stt_service() -> STTService:
    """Get or create the STT service singleton."""
    global _stt_service
    if _stt_service is None:
        _stt_service = STTService()
    return _stt_service
