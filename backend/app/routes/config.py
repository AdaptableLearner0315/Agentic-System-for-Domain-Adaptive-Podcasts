"""
Configuration routes.

Handles:
- GET /modes: Get available pipeline modes
- GET /formats: Get supported file formats
- GET /voices: Get available voice presets
- GET /suggest-topic: Get an AI-suggested podcast topic
"""

import logging
import random

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
                "Chunk-level TTS (~10 calls)",
                "3-segment parallel BGM",
                "4 key moment images",
                "Single adaptive voice",
            ],
            estimated_duration="~2 minutes",
        ),
        "pro": ModeConfig(
            name="Pro",
            description="Balanced quality and speed",
            features=[
                "3-5 minute output",
                "Sentence-level TTS (~50 calls)",
                "5-segment BGM",
                "8 narrative images",
                "Basic voice styling",
                "Emotion-voice sync",
                "Emotion-aligned images",
                "Multi-speaker support",
            ],
            estimated_duration="~3 minutes",
        ),
        "ultra": ModeConfig(
            name="Ultra",
            description="Premium quality with director review",
            features=[
                "5-8 minute output",
                "Sentence-level TTS (50-100 calls)",
                "9-segment daisy-chain BGM",
                "16 narrative images",
                "3-round director review",
                "Full 5-persona voice styling",
                "VAD-based audio ducking",
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
    description="Get supported emotions for Pro and Ultra modes.",
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
    description="Get available multi-speaker formats for Pro and Ultra modes.",
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


# Diverse topic categories for "Surprise Me" feature
TOPIC_CATEGORIES = [
    "Science & Discovery (space, physics, biology, chemistry, geology, oceanography)",
    "History & Civilization (ancient empires, wars, revolutions, cultural movements)",
    "Technology & Innovation (AI, robotics, inventions, future tech, cybersecurity)",
    "Nature & Wildlife (animals, ecosystems, evolution, climate, natural wonders)",
    "Arts & Culture (music history, film, literature, art movements, theater)",
    "Business & Economics (entrepreneurs, market crashes, industries, startups)",
    "Sports & Competition (legendary athletes, historic games, Olympic stories)",
    "Food & Cuisine (culinary history, food science, regional cuisines, chefs)",
    "Travel & Geography (hidden places, cultural journeys, extreme locations)",
    "Philosophy & Ideas (thought experiments, ethical dilemmas, great thinkers)",
    "Crime & Mystery (unsolved cases, heists, forensics, true crime)",
    "Medicine & Health (medical breakthroughs, diseases, human body, surgery)",
    "Architecture & Design (iconic buildings, urban planning, interior design)",
    "Music & Musicians (genres, legendary artists, instruments, music theory)",
    "Space & Astronomy (planets, black holes, space missions, extraterrestrial)",
    "Engineering & Megaprojects (bridges, dams, tunnels, infrastructure)",
    "Psychology & Human Behavior (cognitive biases, social experiments, emotions)",
    "Environment & Sustainability (climate solutions, conservation, renewable energy)",
    "Politics & Governance (political systems, elections, diplomacy, movements)",
    "Mathematics & Logic (paradoxes, famous problems, mathematicians, applications)",
    "Mythology & Folklore (legends, gods, cultural myths, fairy tales)",
    "Fashion & Style (fashion history, designers, trends, textiles)",
    "Gaming & Entertainment (video game history, esports, board games)",
    "Aviation & Transportation (planes, trains, ships, automotive history)",
    "Military & Strategy (battles, tactics, weapons, military leaders)",
    "Language & Communication (linguistics, writing systems, endangered languages)",
    "Photography & Visual Arts (photographers, techniques, iconic images)",
    "Entrepreneurship & Startups (founder stories, business failures, pivots)",
    "Ocean & Marine Life (deep sea, marine biology, shipwrecks, exploration)",
    "Volcanoes & Geology (eruptions, earthquakes, plate tectonics, minerals)",
]


@router.get(
    "/suggest-topic",
    summary="Suggest a podcast topic",
    description="Use Claude to suggest a creative, diverse podcast topic from various categories.",
)
async def suggest_topic() -> dict:
    """
    Generate a creative podcast topic suggestion using Claude.

    Randomly selects a category to ensure diverse topics across
    science, history, arts, technology, nature, and more.

    Returns:
        Dictionary with 'topic' and 'category' keys.

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
        # Randomly select a category for diversity
        category = random.choice(TOPIC_CATEGORIES)

        client = AsyncAnthropic(api_key=settings.anthropic_api_key, timeout=30.0)

        response = await client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=200,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Generate ONE fascinating, specific podcast topic from this category: {category}\n\n"
                        "Requirements:\n"
                        "- Be SPECIFIC (not generic like 'the history of X' but 'How the invention of X changed Y')\n"
                        "- Make it intriguing with a hook or surprising angle\n"
                        "- Appeal to curious minds who want to learn something new\n"
                        "- Can be historical, scientific, cultural, or contemporary\n\n"
                        "Reply with ONLY the topic as a compelling phrase (under 15 words). "
                        "No quotes, no explanation, no category name."
                    ),
                }
            ],
        )

        topic = response.content[0].text.strip()
        # Remove any quotes that might have been added
        topic = topic.strip('"\'')

        return {"topic": topic, "category": category.split(" (")[0]}

    except Exception as e:
        logger.error("Failed to suggest topic: %s", e)
        raise HTTPException(
            status_code=500,
            detail="Failed to generate topic suggestion.",
        )
