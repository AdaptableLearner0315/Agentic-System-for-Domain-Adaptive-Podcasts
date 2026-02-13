"""
Configuration Module
Author: Sarath

Centralized configuration for the podcast enhancement system.
Exports all configuration constants from submodules.
"""

# Path configuration
from config.paths import (
    BASE_DIR,
    OUTPUT_DIR,
    AUDIO_DIR,
    TTS_DIR,
    BGM_DIR,
    BGM_V2_DIR,
    BGM_V2_DAISY_DIR,
    PREVIEW_DIR,
    PREVIEW_V2_DIR,
    PREVIEW_VOICE_ONLY_DIR,
    FINAL_AUDIO_DIR,
    VISUALS_DIR,
    HOOK_VISUALS_DIR,
    VOICE_ONLY_VIDEO_DIR,
    V2_DAISY_VIDEO_DIR,
    ENHANCED_SCRIPT_PATH,
    INPUT_DIR,
    get_module_visuals_dir,
    ensure_directories,
)

# LLM configuration
from config.llm import (
    DEFAULT_MODEL,
    MODEL_OPTIONS,
    DEFAULT_MAX_TOKENS,
    DEFAULT_TEMPERATURE,
    DIRECTOR_APPROVAL_SCORE,
    DIRECTOR_CRITICAL_THRESHOLD,
    get_model_id,
)

# Music/BGM prompts
from config.prompts import (
    EMOTION_MUSIC_MAP,
    DEFAULT_MUSIC,
    BGM_SEGMENT_PROMPTS,
)

# Image prompts
from config.image_prompts import (
    CINEMATIC_STYLE,
    HOOK_PROMPTS,
    MODULE_PROMPTS,
)

# Voice styles
from config.voice_styles import VOICE_STYLES

__all__ = [
    # Paths
    'BASE_DIR',
    'OUTPUT_DIR',
    'AUDIO_DIR',
    'TTS_DIR',
    'BGM_DIR',
    'BGM_V2_DIR',
    'BGM_V2_DAISY_DIR',
    'PREVIEW_DIR',
    'PREVIEW_V2_DIR',
    'PREVIEW_VOICE_ONLY_DIR',
    'FINAL_AUDIO_DIR',
    'VISUALS_DIR',
    'HOOK_VISUALS_DIR',
    'VOICE_ONLY_VIDEO_DIR',
    'V2_DAISY_VIDEO_DIR',
    'ENHANCED_SCRIPT_PATH',
    'INPUT_DIR',
    'get_module_visuals_dir',
    'ensure_directories',
    # LLM
    'DEFAULT_MODEL',
    'MODEL_OPTIONS',
    'DEFAULT_MAX_TOKENS',
    'DEFAULT_TEMPERATURE',
    'DIRECTOR_APPROVAL_SCORE',
    'DIRECTOR_CRITICAL_THRESHOLD',
    'get_model_id',
    # Music prompts
    'EMOTION_MUSIC_MAP',
    'DEFAULT_MUSIC',
    'BGM_SEGMENT_PROMPTS',
    # Image prompts
    'CINEMATIC_STYLE',
    'HOOK_PROMPTS',
    'MODULE_PROMPTS',
    # Voice styles
    'VOICE_STYLES',
]
