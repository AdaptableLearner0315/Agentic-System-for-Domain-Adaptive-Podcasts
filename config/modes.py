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
            "parallel_workers": 15,  # Max concurrent API calls (increased for speed)
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
            "count": 2,  # Just 2 key images (reduced for speed)
            "use_library": True,  # Smart-select from library
            "parallel_workers": 4,
            "generate_custom": 2,  # Generate 2 custom images
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
        "description": "Balanced quality and speed (2-3 minutes)",
        "target_time_seconds": 180,

        # Script enhancement settings
        "script": {
            "director_review": False,  # Skip review loop for faster generation
            "max_review_rounds": 0,
            "model": "opus",  # Best model for quality
        },

        # TTS settings
        "tts": {
            "granularity": "sentence",  # Generate per-sentence for precision
            "parallel_workers": 5,  # Reduced from 10 to avoid rate limits
            "apply_voice_styles": True,  # Basic voice styling
            "use_asset_library": False,
        },

        # BGM settings
        "bgm": {
            "segments": 5,  # Reduced from 9 for speed
            "daisy_chain": False,  # Parallel for speed
            "parallel": True,
            "use_stems": False,
        },

        # Image settings
        "images": {
            "count": 8,  # Reduced from 16 for speed
            "use_library": False,
            "parallel_workers": 4,  # Reduced from 8 to avoid rate limits
            "generate_custom": 8,
        },

        # Assembly settings
        "assembly": {
            "fast_mix": False,
            "vad_ducking": False,  # Simple ducking for speed
            "crossfade_ms": 1000,
            "video_ken_burns": True,
            "video_fps": 24,
            "video_quality": "quality",
        },
    },

    "ultra": {
        "name": "Ultra Mode",
        "description": "Premium quality with director review (5-8 minutes)",
        "target_time_seconds": 420,

        # Script enhancement settings
        "script": {
            "director_review": True,  # Full 3-round director review
            "max_review_rounds": 3,
            "model": "opus",
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


def calculate_bgm_segments(duration_minutes: int, mode: str = "normal") -> int:
    """
    Calculate the number of BGM segments based on duration and mode.

    Normal mode: 2-4 segments (simpler)
    Pro mode: 3-5 segments (balanced)
    Ultra mode: 4-9 segments (richer soundscape)

    Args:
        duration_minutes: Target podcast duration in minutes
        mode: Pipeline mode ('normal', 'pro', or 'ultra')

    Returns:
        Number of BGM segments to generate
    """
    duration_minutes = max(1, min(30, duration_minutes))
    mode_lower = mode.lower()

    if mode_lower == "normal":
        # Normal mode: simpler BGM structure
        if duration_minutes <= 3:
            return 2  # Intro + outro
        elif duration_minutes <= 7:
            return 3  # Intro + main + outro
        elif duration_minutes <= 15:
            return 4  # Intro + 2 mains + outro
        else:
            return 5  # Intro + 3 mains + outro
    elif mode_lower == "pro":
        # Pro mode: balanced BGM (reduced from ultra)
        if duration_minutes <= 3:
            return 3
        elif duration_minutes <= 7:
            return 4
        elif duration_minutes <= 15:
            return 5
        else:
            return 5  # Cap at 5 for Pro
    else:
        # Ultra mode: richer BGM with more variety
        if duration_minutes <= 3:
            return 4
        elif duration_minutes <= 7:
            return 6
        elif duration_minutes <= 12:
            return 7
        elif duration_minutes <= 18:
            return 8
        else:
            return 9  # Full daisy-chain


def calculate_image_count(duration_minutes: int, mode: str = "normal") -> int:
    """
    Calculate the number of images based on duration and mode.

    Roughly 1 image per 30-60 seconds of content.

    Normal mode: 2-4 images (faster generation)
    Pro mode: 4-8 images (balanced)
    Ultra mode: 4-16 images (richer visuals)

    Args:
        duration_minutes: Target podcast duration in minutes
        mode: Pipeline mode ('normal', 'pro', or 'ultra')

    Returns:
        Number of images to generate
    """
    duration_minutes = max(1, min(30, duration_minutes))
    mode_lower = mode.lower()

    if mode_lower == "normal":
        # Normal mode: ~0.5 images per minute, min 2, max 4
        count = max(2, min(4, duration_minutes))
        return count
    elif mode_lower == "pro":
        # Pro mode: ~1 image per minute, min 4, max 8
        count = max(4, min(8, duration_minutes))
        return count
    else:
        # Ultra mode: ~1.5 images per minute, min 4, max 16
        count = max(4, min(16, int(duration_minutes * 1.5)))
        return count


def calculate_tts_parallel_workers(duration_minutes: int, mode: str = "normal") -> int:
    """
    Calculate optimal number of parallel TTS workers based on duration.

    More workers for longer content to maintain reasonable generation time.

    Args:
        duration_minutes: Target podcast duration in minutes
        mode: Pipeline mode

    Returns:
        Number of parallel TTS workers
    """
    # Base workers on expected chunk count
    # Roughly 2-4 chunks per minute of content
    expected_chunks = duration_minutes * 3

    if mode.lower() == "normal":
        # Normal mode: aggressive parallelism
        return min(10, max(5, expected_chunks // 2))
    else:
        # Pro mode: sentence-level, more workers
        return 10  # Always max for pro mode


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
    'calculate_bgm_segments',
    'calculate_image_count',
    'calculate_tts_parallel_workers',
    'VOICE_STYLE_PRESETS',
    'MUSIC_GENRE_PRESETS',
    'IMAGE_STYLE_PRESETS',
]
