"""
Mode Configuration
Author: Sarath

Defines Normal and Pro mode configurations for the podcast enhancement system.
Normal mode prioritizes speed (90-120 seconds), Pro mode prioritizes quality (5-8 minutes).
"""

from typing import Dict, Any


# Mode configurations
MODE_CONFIGS: Dict[str, Dict[str, Any]] = {
    "normal": {
        "name": "Normal Mode",
        "description": "Fast generation targeting 90-120 seconds",
        "target_time_seconds": 120,

        # Script enhancement settings
        "script": {
            "director_review": False,  # Skip review loop for speed
            "max_review_rounds": 0,
            "model": "sonnet",  # Faster model
        },

        # TTS settings
        "tts": {
            "granularity": "chunk",  # Generate per-chunk, not per-sentence
            "parallel_workers": 10,  # Max concurrent API calls
            "apply_voice_styles": False,  # Skip voice styling for speed
            "use_asset_library": True,  # Use pre-generated assets when possible
        },

        # BGM settings
        "bgm": {
            "segments": 3,  # Just intro, main, outro
            "daisy_chain": False,  # No daisy-chain conditioning
            "parallel": True,  # Generate all segments in parallel
            "use_stems": True,  # Use pre-generated stem library
        },

        # Image settings
        "images": {
            "count": 4,  # Just 4 key images
            "use_library": True,  # Smart-select from library
            "parallel_workers": 4,
            "generate_custom": 1,  # Generate only 1 custom image
        },

        # Assembly settings
        "assembly": {
            "fast_mix": True,
            "vad_ducking": False,  # Simple ducking instead
            "crossfade_ms": 500,
            "video_ken_burns": False,
            "video_fps": 24,
            "video_quality": "fast",
        },
    },

    "pro": {
        "name": "Pro Mode",
        "description": "High-quality generation with full customization (5-8 minutes)",
        "target_time_seconds": 420,

        # Script enhancement settings
        "script": {
            "director_review": True,
            "max_review_rounds": 3,
            "model": "opus",  # Best model for quality
        },

        # TTS settings
        "tts": {
            "granularity": "sentence",  # Generate per-sentence for precision
            "parallel_workers": 10,
            "apply_voice_styles": True,  # Full 5-persona voice styling
            "use_asset_library": False,
        },

        # BGM settings
        "bgm": {
            "segments": 9,  # Full 9-segment daisy-chain
            "daisy_chain": True,
            "parallel": False,  # Sequential for conditioning
            "use_stems": False,
        },

        # Image settings
        "images": {
            "count": 16,  # Full 16 narrative images
            "use_library": False,
            "parallel_workers": 8,
            "generate_custom": 16,  # All custom
        },

        # Assembly settings
        "assembly": {
            "fast_mix": False,
            "vad_ducking": True,  # Full VAD-based ducking
            "crossfade_ms": 2000,
            "video_ken_burns": True,
            "video_fps": 24,
            "video_quality": "quality",
        },
    },
}


# Simplified BGM segment configuration for Normal mode (3 segments)
NORMAL_BGM_SEGMENTS = {
    1: {
        "name": "Intro",
        "prompt": "Cinematic ambient soundscape, atmospheric and engaging, sense of mystery and wonder, building anticipation, high fidelity, 90 BPM",
        "duration": 30,
        "phase": "Opening",
    },
    2: {
        "name": "Main",
        "prompt": "Steady background music, subtle emotional progression, professional podcast quality, dynamic but not distracting, 100 BPM",
        "duration": 45,
        "phase": "Content",
    },
    3: {
        "name": "Outro",
        "prompt": "Reflective ambient music, sense of completion and satisfaction, gentle fade, warm and conclusive, 85 BPM",
        "duration": 30,
        "phase": "Closing",
    },
}


def get_mode_config(mode: str) -> Dict[str, Any]:
    """
    Get configuration for a specific mode.

    Args:
        mode: Mode name ('normal' or 'pro')

    Returns:
        Mode configuration dictionary

    Raises:
        ValueError: If mode is not recognized
    """
    mode_lower = mode.lower()
    if mode_lower not in MODE_CONFIGS:
        available = ', '.join(MODE_CONFIGS.keys())
        raise ValueError(f"Unknown mode: {mode}. Available modes: {available}")
    return MODE_CONFIGS[mode_lower]


def get_tts_config(mode: str) -> Dict[str, Any]:
    """Get TTS configuration for a mode."""
    return get_mode_config(mode)["tts"]


def get_bgm_config(mode: str) -> Dict[str, Any]:
    """Get BGM configuration for a mode."""
    return get_mode_config(mode)["bgm"]


def get_image_config(mode: str) -> Dict[str, Any]:
    """Get image configuration for a mode."""
    return get_mode_config(mode)["images"]


def get_script_config(mode: str) -> Dict[str, Any]:
    """Get script enhancement configuration for a mode."""
    return get_mode_config(mode)["script"]


def get_assembly_config(mode: str) -> Dict[str, Any]:
    """Get assembly configuration for a mode."""
    return get_mode_config(mode)["assembly"]


# Voice style configurations (for Pro mode)
VOICE_STYLE_PRESETS = {
    "default": {
        "speed_multiplier": 1.0,
        "volume_boost_db": 0,
        "eq": "balanced",
    },
    "energetic": {
        "speed_multiplier": 1.08,
        "volume_boost_db": 3,
        "eq": "bright",
    },
    "calm": {
        "speed_multiplier": 0.92,
        "volume_boost_db": 1,
        "eq": "warm",
    },
    "dramatic": {
        "speed_multiplier": 0.95,
        "volume_boost_db": 2,
        "eq": "full",
    },
}


# Music genre presets (for Pro mode customization)
MUSIC_GENRE_PRESETS = {
    "cinematic": {
        "style": "Orchestral cinematic",
        "tempo_range": (70, 110),
        "instruments": ["strings", "piano", "brass"],
    },
    "ambient": {
        "style": "Atmospheric ambient",
        "tempo_range": (60, 90),
        "instruments": ["pads", "textures", "minimal percussion"],
    },
    "electronic": {
        "style": "Modern electronic",
        "tempo_range": (100, 128),
        "instruments": ["synths", "beats", "bass"],
    },
    "acoustic": {
        "style": "Warm acoustic",
        "tempo_range": (80, 110),
        "instruments": ["guitar", "piano", "soft drums"],
    },
    "documentary": {
        "style": "Documentary score",
        "tempo_range": (70, 100),
        "instruments": ["piano", "strings", "subtle percussion"],
    },
}


# Image style presets (for Pro mode customization)
IMAGE_STYLE_PRESETS = {
    "cinematic": "cinematic photography, documentary style, photorealistic, film grain, 35mm film aesthetic, professional lighting",
    "artistic": "artistic photography, creative composition, dramatic lighting, fine art style, gallery quality",
    "minimal": "minimalist photography, clean lines, simple composition, modern aesthetic, high contrast",
    "vintage": "vintage photography, retro film look, warm tones, nostalgic aesthetic, classic composition",
    "dramatic": "dramatic photography, strong shadows, bold contrast, moody lighting, powerful composition",
}


__all__ = [
    'MODE_CONFIGS',
    'NORMAL_BGM_SEGMENTS',
    'get_mode_config',
    'get_tts_config',
    'get_bgm_config',
    'get_image_config',
    'get_script_config',
    'get_assembly_config',
    'VOICE_STYLE_PRESETS',
    'MUSIC_GENRE_PRESETS',
    'IMAGE_STYLE_PRESETS',
]
