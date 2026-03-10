"""
Emotion-Voice Mapping Configuration
Author: Sarath

Maps emotions to voice parameters for TTS generation and post-processing.
Used by TTSNarrator and VoiceStyleEngine to create emotionally-responsive voice delivery.

Supported Emotions (15 total):
- wonder, curiosity, tension, triumph, melancholy
- intrigue, excitement, reflection, restlessness
- explosive_energy, rebellion, liberation, experimentation
- mastery, intensity
"""

# Emotion to TTS voice parameters
# These parameters are passed to the TTS generation
EMOTION_VOICE_PARAMS = {
    "wonder": {
        "speed": 0.95,
        "emphasis": "soft",
        "pause_style": "contemplative",
        "description": "Slow, awe-filled delivery with space for reflection"
    },
    "curiosity": {
        "speed": 1.00,
        "emphasis": "moderate",
        "pause_style": "questioning",
        "description": "Engaged, inquisitive tone with natural pacing"
    },
    "tension": {
        "speed": 1.02,
        "emphasis": "moderate",
        "pause_style": "dramatic",
        "description": "Slightly faster, building suspense with strategic pauses"
    },
    "triumph": {
        "speed": 1.05,
        "emphasis": "strong",
        "pause_style": "confident",
        "description": "Uplifting, celebratory delivery with energy"
    },
    "melancholy": {
        "speed": 0.90,
        "emphasis": "soft",
        "pause_style": "slow",
        "description": "Slow, reflective, emotionally weighted delivery"
    },
    "intrigue": {
        "speed": 0.98,
        "emphasis": "moderate",
        "pause_style": "mysterious",
        "description": "Slightly measured, creating curiosity and anticipation"
    },
    "excitement": {
        "speed": 1.10,
        "emphasis": "strong",
        "pause_style": "quick",
        "description": "Fast, energetic delivery with enthusiasm"
    },
    "reflection": {
        "speed": 0.92,
        "emphasis": "soft",
        "pause_style": "thoughtful",
        "description": "Measured, contemplative tone with deliberate pacing"
    },
    "restlessness": {
        "speed": 1.05,
        "emphasis": "moderate",
        "pause_style": "edgy",
        "description": "Slightly urgent, conveying inner tension"
    },
    "explosive_energy": {
        "speed": 1.15,
        "emphasis": "strong",
        "pause_style": "quick",
        "description": "High-energy, powerful delivery with momentum"
    },
    "rebellion": {
        "speed": 1.12,
        "emphasis": "strong",
        "pause_style": "defiant",
        "description": "Raw, urgent delivery with conviction"
    },
    "liberation": {
        "speed": 1.08,
        "emphasis": "strong",
        "pause_style": "triumphant",
        "description": "Freeing, uplifting delivery with release"
    },
    "experimentation": {
        "speed": 1.00,
        "emphasis": "moderate",
        "pause_style": "creative",
        "description": "Curious, explorative tone with variation"
    },
    "mastery": {
        "speed": 0.95,
        "emphasis": "moderate",
        "pause_style": "confident",
        "description": "Assured, authoritative delivery"
    },
    "intensity": {
        "speed": 1.08,
        "emphasis": "strong",
        "pause_style": "dramatic",
        "description": "Focused, powerful delivery with weight"
    },
    # Fallback/default
    "neutral": {
        "speed": 1.0,
        "emphasis": "moderate",
        "pause_style": "normal",
        "description": "Standard narration pace"
    }
}

# Emotion to post-processing style adjustments
# These are applied by VoiceStyleEngine on top of module styles
EMOTION_STYLE_MODIFIERS = {
    "wonder": {
        "eq_boost": "warm",
        "reverb": 0.15,
        "compression": None,
        "volume_adjust_db": 0,
        "description": "Warm, spacious sound"
    },
    "curiosity": {
        "eq_boost": "presence",
        "reverb": 0.05,
        "compression": None,
        "volume_adjust_db": 1,
        "description": "Clear, forward presence"
    },
    "tension": {
        "eq_boost": "presence",
        "reverb": 0.0,
        "compression": "light",
        "volume_adjust_db": 1,
        "description": "Tight, focused sound"
    },
    "triumph": {
        "eq_boost": "bright",
        "reverb": 0.1,
        "compression": "medium",
        "volume_adjust_db": 2,
        "description": "Bright, powerful sound"
    },
    "melancholy": {
        "eq_boost": "warm",
        "reverb": 0.2,
        "compression": None,
        "volume_adjust_db": -1,
        "description": "Warm, intimate sound"
    },
    "intrigue": {
        "eq_boost": "presence",
        "reverb": 0.1,
        "compression": None,
        "volume_adjust_db": 0,
        "description": "Clear with subtle depth"
    },
    "excitement": {
        "eq_boost": "bright",
        "reverb": 0.0,
        "compression": "medium",
        "volume_adjust_db": 2,
        "description": "Bright, energetic sound"
    },
    "reflection": {
        "eq_boost": "warm",
        "reverb": 0.15,
        "compression": None,
        "volume_adjust_db": 0,
        "description": "Warm, contemplative sound"
    },
    "restlessness": {
        "eq_boost": "edge",
        "reverb": 0.0,
        "compression": "light",
        "volume_adjust_db": 1,
        "description": "Edgy, tense sound"
    },
    "explosive_energy": {
        "eq_boost": "bright",
        "reverb": 0.0,
        "compression": "heavy",
        "volume_adjust_db": 3,
        "description": "Bright, powerful, compressed"
    },
    "rebellion": {
        "eq_boost": "edge",
        "reverb": 0.0,
        "compression": "medium",
        "volume_adjust_db": 3,
        "description": "Raw, edgy sound"
    },
    "liberation": {
        "eq_boost": "bright",
        "reverb": 0.1,
        "compression": "light",
        "volume_adjust_db": 2,
        "description": "Open, freeing sound"
    },
    "experimentation": {
        "eq_boost": "presence",
        "reverb": 0.1,
        "compression": None,
        "volume_adjust_db": 0,
        "description": "Clear, balanced sound"
    },
    "mastery": {
        "eq_boost": "full",
        "reverb": 0.1,
        "compression": "light",
        "volume_adjust_db": 1,
        "description": "Full, authoritative sound"
    },
    "intensity": {
        "eq_boost": "presence",
        "reverb": 0.0,
        "compression": "medium",
        "volume_adjust_db": 2,
        "description": "Focused, powerful sound"
    },
    "neutral": {
        "eq_boost": None,
        "reverb": 0.0,
        "compression": None,
        "volume_adjust_db": 0,
        "description": "No adjustments"
    }
}

# Pause durations by pause style (in milliseconds)
PAUSE_STYLE_DURATIONS = {
    "contemplative": {"between_sentences": 450, "after_chunk": 1000},
    "questioning": {"between_sentences": 350, "after_chunk": 800},
    "dramatic": {"between_sentences": 400, "after_chunk": 1200},
    "confident": {"between_sentences": 300, "after_chunk": 700},
    "slow": {"between_sentences": 500, "after_chunk": 1100},
    "mysterious": {"between_sentences": 400, "after_chunk": 900},
    "quick": {"between_sentences": 250, "after_chunk": 600},
    "thoughtful": {"between_sentences": 450, "after_chunk": 1000},
    "edgy": {"between_sentences": 300, "after_chunk": 700},
    "defiant": {"between_sentences": 300, "after_chunk": 800},
    "triumphant": {"between_sentences": 350, "after_chunk": 800},
    "creative": {"between_sentences": 350, "after_chunk": 800},
    "normal": {"between_sentences": 350, "after_chunk": 800}
}


def get_emotion_voice_params(emotion: str) -> dict:
    """
    Get voice parameters for a specific emotion.

    Args:
        emotion: Emotion name (case-insensitive)

    Returns:
        Voice parameters dictionary
    """
    return EMOTION_VOICE_PARAMS.get(emotion.lower(), EMOTION_VOICE_PARAMS["neutral"])


def get_emotion_style_modifiers(emotion: str) -> dict:
    """
    Get post-processing style modifiers for a specific emotion.

    Args:
        emotion: Emotion name (case-insensitive)

    Returns:
        Style modifiers dictionary
    """
    return EMOTION_STYLE_MODIFIERS.get(emotion.lower(), EMOTION_STYLE_MODIFIERS["neutral"])


def get_pause_durations(pause_style: str) -> dict:
    """
    Get pause durations for a specific pause style.

    Args:
        pause_style: Pause style name

    Returns:
        Dictionary with between_sentences and after_chunk durations
    """
    return PAUSE_STYLE_DURATIONS.get(pause_style, PAUSE_STYLE_DURATIONS["normal"])


# List of all supported emotions
SUPPORTED_EMOTIONS = list(EMOTION_VOICE_PARAMS.keys())


def is_valid_emotion(emotion: str) -> bool:
    """Check if an emotion is supported."""
    return emotion.lower() in SUPPORTED_EMOTIONS


__all__ = [
    'EMOTION_VOICE_PARAMS',
    'EMOTION_STYLE_MODIFIERS',
    'PAUSE_STYLE_DURATIONS',
    'SUPPORTED_EMOTIONS',
    'get_emotion_voice_params',
    'get_emotion_style_modifiers',
    'get_pause_durations',
    'is_valid_emotion',
]
