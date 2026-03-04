"""
Configuration routes.

Handles:
- GET /modes: Get available pipeline modes
- GET /formats: Get supported file formats
- GET /voices: Get available voice presets
- GET /suggest-topic: Get an AI-suggested podcast topic
"""

import logging

from fastapi import APIRouter, HTTPException
from anthropic import AsyncAnthropic

from ..models.responses import ConfigResponse, ModeConfig
from ..config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/modes",
    response_model=ConfigResponse,
    summary="Get configuration",
    description="Get available pipeline modes and supported formats.",
)
async def get_modes() -> ConfigResponse:
    """
    Get available pipeline modes and configuration.

    Returns:
        ConfigResponse with modes, supported formats, and limits.
    """
    settings = get_settings()

    modes = {
        "normal": ModeConfig(
            name="Normal",
            description="Fast generation for quick previews",
            features=[
                "90-120 second output",
                "Chunk-level TTS (15 calls)",
                "3-segment parallel BGM",
                "4 key moment images",
                "Single adaptive voice",
            ],
            estimated_duration="~2 minutes",
        ),
        "pro": ModeConfig(
            name="Pro",
            description="High-quality generation with full features",
            features=[
                "5-8 minute output",
                "Sentence-level TTS (80-100 calls)",
                "9-segment daisy-chain BGM",
                "16 narrative images",
                "Director review loop",
                "5 voice personas",
                "Emotion-voice sync",
                "Emotion-aligned images",
                "Multi-speaker support",
            ],
            estimated_duration="~6 minutes",
        ),
    }

    supported_formats = [
        ".txt", ".md",  # Text
        ".pdf",  # PDF
        ".docx", ".doc",  # Word
        ".mp3", ".wav", ".m4a",  # Audio
        ".mp4", ".mov", ".avi", ".mkv",  # Video
    ]

    return ConfigResponse(
        modes=modes,
        supported_formats=supported_formats,
        max_file_size_mb=settings.max_upload_size_mb,
    )


@router.get(
    "/voices",
    summary="Get available voices",
    description="Get available voice presets for TTS.",
)
async def get_voices() -> dict:
    """
    Get available voice presets.

    Returns:
        Dictionary of available voice presets with descriptions.
    """
    return {
        "voices": {
            "female_friendly": {
                "id": "Friendly_Female_English",
                "description": "Warm, engaging female voice",
            },
            "female_professional": {
                "id": "Professional_Female_English",
                "description": "Clear, authoritative female voice",
            },
            "female_energetic": {
                "id": "Energetic_Female_English",
                "description": "Upbeat, dynamic female voice",
            },
            "male_friendly": {
                "id": "Friendly_Male_English",
                "description": "Warm, approachable male voice",
            },
            "male_professional": {
                "id": "Professional_Male_English",
                "description": "Clear, authoritative male voice",
            },
            "male_energetic": {
                "id": "Energetic_Male_English",
                "description": "Upbeat, dynamic male voice",
            },
        },
        "default": "female_friendly",
    }


@router.get(
    "/emotions",
    summary="Get supported emotions",
    description="Get supported emotions for Pro mode.",
)
async def get_emotions() -> dict:
    """
    Get supported emotions for emotion-sync features.

    Returns:
        Dictionary of emotions with voice and visual parameters.
    """
    return {
        "emotions": {
            "wonder": {"speed": 0.95, "emphasis": "soft", "visual": "ethereal blues"},
            "curiosity": {"speed": 1.00, "emphasis": "moderate", "visual": "warm amber"},
            "tension": {"speed": 1.02, "emphasis": "moderate", "visual": "stark contrasts"},
            "triumph": {"speed": 1.05, "emphasis": "strong", "visual": "warm golds"},
            "melancholy": {"speed": 0.90, "emphasis": "soft", "visual": "muted blues"},
            "intrigue": {"speed": 0.98, "emphasis": "moderate", "visual": "mysterious purples"},
            "excitement": {"speed": 1.10, "emphasis": "strong", "visual": "vibrant"},
            "reflection": {"speed": 0.92, "emphasis": "soft", "visual": "sepia"},
            "restlessness": {"speed": 1.05, "emphasis": "moderate", "visual": "edgy contrasts"},
            "explosive_energy": {"speed": 1.15, "emphasis": "strong", "visual": "intense reds"},
            "rebellion": {"speed": 1.12, "emphasis": "strong", "visual": "punk aesthetics"},
            "liberation": {"speed": 1.08, "emphasis": "strong", "visual": "open skies"},
            "experimentation": {"speed": 1.00, "emphasis": "moderate", "visual": "creative"},
            "mastery": {"speed": 0.95, "emphasis": "moderate", "visual": "sophisticated"},
            "intensity": {"speed": 1.08, "emphasis": "strong", "visual": "focused"},
        },
        "default": "curiosity",
    }


@router.get(
    "/speaker-formats",
    summary="Get speaker formats",
    description="Get available multi-speaker formats for Pro mode.",
)
async def get_speaker_formats() -> dict:
    """
    Get available multi-speaker formats.

    Returns:
        Dictionary of speaker formats with descriptions.
    """
    return {
        "formats": {
            "auto": {
                "description": "Automatically detect from content",
                "speakers": [],
            },
            "single": {
                "description": "Single narrator for documentary/storytelling",
                "speakers": ["narrator"],
            },
            "interview": {
                "description": "Host and guest for expert interviews",
                "speakers": ["host", "guest"],
            },
            "co_hosts": {
                "description": "Two co-hosts for conversational podcasts",
                "speakers": ["host_1", "host_2"],
            },
            "narrator_characters": {
                "description": "Narrator with character voices for narrative",
                "speakers": ["narrator", "character"],
            },
        },
        "default": "auto",
    }


@router.get(
    "/suggest-topic",
    summary="Suggest a podcast topic",
    description="Use Claude to suggest a creative, trending podcast topic.",
)
async def suggest_topic() -> dict:
    """
    Generate a creative podcast topic suggestion using Claude.

    Returns:
        Dictionary with a single 'topic' key containing the suggestion.

    Raises:
        HTTPException 503: If Anthropic API key is not configured.
        HTTPException 500: If Claude API call fails.
    """
    settings = get_settings()

    if not settings.anthropic_api_key:
        raise HTTPException(
            status_code=503,
            detail="Anthropic API key is not configured.",
        )

    try:
        client = AsyncAnthropic(api_key=settings.anthropic_api_key, timeout=30.0)

        response = await client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=200,
            messages=[
                {
                    "role": "user",
                    "content": (
                        "Suggest ONE creative, specific, and trending podcast topic. "
                        "It should be interesting, timely, and appeal to a broad audience. "
                        "Reply with ONLY the topic as a short phrase (under 15 words), "
                        "nothing else. No quotes, no explanation."
                    ),
                }
            ],
        )

        topic = response.content[0].text.strip()
        return {"topic": topic}

    except Exception as e:
        logger.error("Failed to suggest topic: %s", e)
        raise HTTPException(
            status_code=500,
            detail="Failed to generate topic suggestion.",
        )
