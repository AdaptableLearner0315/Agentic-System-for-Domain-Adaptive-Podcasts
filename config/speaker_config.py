"""
Speaker Configuration
Author: Sarath

Configuration for multi-speaker podcast generation.
Defines available voices, speaker formats, and detection patterns.

Supports:
- Interview format (Host + Guest)
- Co-hosts format (Two equal hosts)
- Narrator + Characters format
- Single narrator (default)
"""

from typing import Dict, List, Optional

# Available voices from MiniMax Speech-01-HD via Fal AI
# Voice IDs confirmed from MiniMax TTS documentation
AVAILABLE_VOICES = {
    # Female voices
    "female_friendly": {
        "voice_id": "Friendly_Female_English",
        "description": "Warm, engaging female narrator",
        "tone": "friendly",
        "gender": "female"
    },
    "female_professional": {
        "voice_id": "Professional_Female_English",
        "description": "Clear, authoritative female voice",
        "tone": "professional",
        "gender": "female"
    },
    "female_energetic": {
        "voice_id": "Energetic_Female_English",
        "description": "Upbeat, dynamic female voice",
        "tone": "energetic",
        "gender": "female"
    },
    "female_calm": {
        "voice_id": "Calm_Female_English",
        "description": "Soothing, relaxed female voice",
        "tone": "calm",
        "gender": "female"
    },
    # Male voices
    "male_friendly": {
        "voice_id": "Friendly_Male_English",
        "description": "Warm, approachable male narrator",
        "tone": "friendly",
        "gender": "male"
    },
    "male_professional": {
        "voice_id": "Professional_Male_English",
        "description": "Clear, authoritative male voice",
        "tone": "professional",
        "gender": "male"
    },
    "male_energetic": {
        "voice_id": "Energetic_Male_English",
        "description": "Upbeat, dynamic male voice",
        "tone": "energetic",
        "gender": "male"
    },
    "male_calm": {
        "voice_id": "Calm_Male_English",
        "description": "Soothing, relaxed male voice",
        "tone": "calm",
        "gender": "male"
    },
}

# Default voice for single narrator mode
DEFAULT_VOICE = "female_friendly"

# Speaker format definitions
SPEAKER_FORMATS = {
    "single": {
        "id": "single",
        "name": "Single Narrator",
        "description": "Single narrator throughout the podcast",
        "speakers": {
            "narrator": {
                "role": "main",
                "default_voice": "female_friendly",
                "description": "The main narrator voice"
            }
        },
        "detection_patterns": [],  # Default format, no patterns needed
        "detection_weight": 0  # Lowest priority
    },
    "interview": {
        "id": "interview",
        "name": "Interview Format",
        "description": "Host asking questions, Guest providing answers",
        "speakers": {
            "host": {
                "role": "interviewer",
                "default_voice": "female_friendly",
                "description": "The interview host asking questions"
            },
            "guest": {
                "role": "expert",
                "default_voice": "male_professional",
                "description": "The expert guest providing answers"
            }
        },
        "detection_patterns": [
            r"Q:\s*",
            r"A:\s*",
            r"Host:\s*",
            r"Guest:\s*",
            r"\binterview\b",
            r"\bquestion\b.*\banswer\b",
            r"I asked",
            r"they (said|replied|answered|explained)",
        ],
        "detection_weight": 3
    },
    "co_hosts": {
        "id": "co_hosts",
        "name": "Co-Hosts Format",
        "description": "Two equal co-hosts having a conversation",
        "speakers": {
            "host_1": {
                "role": "primary",
                "default_voice": "female_friendly",
                "description": "First co-host"
            },
            "host_2": {
                "role": "secondary",
                "default_voice": "male_friendly",
                "description": "Second co-host"
            }
        },
        "detection_patterns": [
            r"\bwe\b.*\bthink\b",
            r"\blet's\b",
            r"\btogether\b",
            r"\bboth of us\b",
            r"Host 1:",
            r"Host 2:",
            r"\bour\b.*\bshow\b",
        ],
        "detection_weight": 2
    },
    "narrator_characters": {
        "id": "narrator_characters",
        "name": "Narrator with Characters",
        "description": "Main narrator with occasional character voices for quotes",
        "speakers": {
            "narrator": {
                "role": "main",
                "default_voice": "female_friendly",
                "description": "The main storytelling narrator"
            },
            "character": {
                "role": "quoted",
                "default_voice": "male_professional",
                "description": "Voice for character quotes and dialogue"
            }
        },
        "detection_patterns": [
            r'"[^"]{20,}"',  # Long quotes
            r'\b(said|replied|exclaimed|shouted|whispered)\b',
            r"'[^']{20,}'",  # Single-quoted speech
            r"\bhe said\b",
            r"\bshe said\b",
            r"\bthey said\b",
        ],
        "detection_weight": 1
    }
}

# Voice recommendations by speaker role
ROLE_VOICE_RECOMMENDATIONS = {
    "main": ["female_friendly", "male_friendly", "female_professional"],
    "interviewer": ["female_friendly", "male_friendly", "female_professional"],
    "expert": ["male_professional", "female_professional", "male_calm"],
    "primary": ["female_friendly", "female_energetic"],
    "secondary": ["male_friendly", "male_energetic"],
    "quoted": ["male_professional", "female_professional", "male_energetic"],
}

# Voice contrast guidelines for multi-speaker
VOICE_CONTRAST_RULES = {
    "interview": {
        "guideline": "Use contrasting tones (friendly + professional) or genders",
        "avoid": "Two voices with same tone and gender"
    },
    "co_hosts": {
        "guideline": "Use similar energy levels but different voices (gender or tone)",
        "avoid": "Identical voices that are hard to distinguish"
    },
    "narrator_characters": {
        "guideline": "Narrator should be warm/friendly, characters can vary",
        "avoid": "Character voice too similar to narrator"
    }
}


def get_voice_id(voice_key: str) -> str:
    """
    Get the actual MiniMax voice_id for a voice key.

    Args:
        voice_key: Key from AVAILABLE_VOICES (e.g., 'female_friendly')

    Returns:
        MiniMax voice_id string
    """
    voice = AVAILABLE_VOICES.get(voice_key)
    if voice:
        return voice["voice_id"]
    # Fallback to default
    return AVAILABLE_VOICES[DEFAULT_VOICE]["voice_id"]


def get_format_speakers(format_id: str) -> Dict[str, dict]:
    """
    Get speaker definitions for a format.

    Args:
        format_id: Format ID ('interview', 'co_hosts', etc.)

    Returns:
        Dictionary of speaker role -> speaker config
    """
    format_config = SPEAKER_FORMATS.get(format_id, SPEAKER_FORMATS["single"])
    return format_config.get("speakers", {})


def get_default_voice_for_role(format_id: str, role: str) -> str:
    """
    Get the default voice key for a specific role in a format.

    Args:
        format_id: Format ID
        role: Speaker role (e.g., 'host', 'guest', 'narrator')

    Returns:
        Voice key string
    """
    speakers = get_format_speakers(format_id)
    speaker = speakers.get(role, {})
    return speaker.get("default_voice", DEFAULT_VOICE)


def get_recommended_voices(role: str) -> List[str]:
    """
    Get recommended voice options for a speaker role.

    Args:
        role: Speaker role

    Returns:
        List of recommended voice keys
    """
    return ROLE_VOICE_RECOMMENDATIONS.get(role, ["female_friendly", "male_friendly"])


def list_available_formats() -> List[dict]:
    """
    Get list of all available speaker formats with descriptions.

    Returns:
        List of format info dictionaries
    """
    return [
        {
            "id": fmt_id,
            "name": fmt["name"],
            "description": fmt["description"],
            "speakers": list(fmt["speakers"].keys())
        }
        for fmt_id, fmt in SPEAKER_FORMATS.items()
    ]


def list_available_voices() -> List[dict]:
    """
    Get list of all available voices with descriptions.

    Returns:
        List of voice info dictionaries
    """
    return [
        {
            "key": key,
            "voice_id": voice["voice_id"],
            "description": voice["description"],
            "tone": voice["tone"],
            "gender": voice["gender"]
        }
        for key, voice in AVAILABLE_VOICES.items()
    ]


__all__ = [
    'AVAILABLE_VOICES',
    'DEFAULT_VOICE',
    'SPEAKER_FORMATS',
    'ROLE_VOICE_RECOMMENDATIONS',
    'VOICE_CONTRAST_RULES',
    'get_voice_id',
    'get_format_speakers',
    'get_default_voice_for_role',
    'get_recommended_voices',
    'list_available_formats',
    'list_available_voices',
]
