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

# Emotion-voice mapping
from config.emotion_voice_mapping import (
    EMOTION_VOICE_PARAMS,
    EMOTION_STYLE_MODIFIERS,
    PAUSE_STYLE_DURATIONS,
    SUPPORTED_EMOTIONS,
    get_emotion_voice_params,
    get_emotion_style_modifiers,
    get_pause_durations,
    is_valid_emotion,
)

# Emotion-visual mapping
from config.emotion_visual_mapping import (
    EMOTION_VISUAL_STYLE,
    EMOTION_VISUAL_TRANSITIONS,
    SUPPORTED_VISUAL_EMOTIONS,
    get_emotion_visual_style,
    build_emotion_prompt_suffix,
    get_emotion_color_hint,
    get_emotion_mood_hint,
    get_transition_hint,
)

# Speaker configuration
from config.speaker_config import (
    AVAILABLE_VOICES,
    DEFAULT_VOICE,
    SPEAKER_FORMATS,
    ROLE_VOICE_RECOMMENDATIONS,
    VOICE_CONTRAST_RULES,
    get_voice_id,
    get_format_speakers,
    get_default_voice_for_role,
    get_recommended_voices,
    list_available_formats,
    list_available_voices,
)

# Mode configuration
from config.modes import (
    MODE_CONFIGS,
    NORMAL_BGM_SEGMENTS,
    get_mode_config,
    get_tts_config,
    get_bgm_config,
    get_image_config,
    get_script_config,
    get_assembly_config,
    VOICE_STYLE_PRESETS,
    MUSIC_GENRE_PRESETS,
    IMAGE_STYLE_PRESETS,
)

# User configuration
from config.user_config import (
    UserConfig,
    DEFAULT_CONFIG_PATH,
    get_default_config,
    save_default_config,
    run_config_wizard,
)

# Era profiles for series generation
from config.era_profiles import (
    ERA_PROFILES,
    ERA_KEYWORDS,
    get_era_profile,
    detect_era_from_text,
    get_all_eras,
)

# Genre templates for series generation
from config.genre_templates import (
    GENRE_TEMPLATES,
    GENRE_KEYWORDS,
    get_genre_template,
    detect_genre_from_text,
    get_arc_template,
    get_all_genres,
    get_cliffhanger_strategies,
)

# Cliffhanger prompts for series generation
from config.cliffhanger_prompts import (
    CLIFFHANGER_TYPES,
    CLIFFHANGER_STRATEGIES,
    get_cliffhanger_type,
    get_cliffhanger_prompt,
    get_audio_sting_prompt,
    get_cliffhanger_strategy,
    get_episode_cliffhanger_type,
    PREVIOUSLY_ON_STYLES,
    get_previously_on_prompt,
)

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
    # Emotion-voice mapping
    'EMOTION_VOICE_PARAMS',
    'EMOTION_STYLE_MODIFIERS',
    'PAUSE_STYLE_DURATIONS',
    'SUPPORTED_EMOTIONS',
    'get_emotion_voice_params',
    'get_emotion_style_modifiers',
    'get_pause_durations',
    'is_valid_emotion',
    # Emotion-visual mapping
    'EMOTION_VISUAL_STYLE',
    'EMOTION_VISUAL_TRANSITIONS',
    'SUPPORTED_VISUAL_EMOTIONS',
    'get_emotion_visual_style',
    'build_emotion_prompt_suffix',
    'get_emotion_color_hint',
    'get_emotion_mood_hint',
    'get_transition_hint',
    # Speaker configuration
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
    # Mode configuration
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
    # User configuration
    'UserConfig',
    'DEFAULT_CONFIG_PATH',
    'get_default_config',
    'save_default_config',
    'run_config_wizard',
    # Era profiles
    'ERA_PROFILES',
    'ERA_KEYWORDS',
    'get_era_profile',
    'detect_era_from_text',
    'get_all_eras',
    # Genre templates
    'GENRE_TEMPLATES',
    'GENRE_KEYWORDS',
    'get_genre_template',
    'detect_genre_from_text',
    'get_arc_template',
    'get_all_genres',
    'get_cliffhanger_strategies',
    # Cliffhanger prompts
    'CLIFFHANGER_TYPES',
    'CLIFFHANGER_STRATEGIES',
    'get_cliffhanger_type',
    'get_cliffhanger_prompt',
    'get_audio_sting_prompt',
    'get_cliffhanger_strategy',
    'get_episode_cliffhanger_type',
    'PREVIOUSLY_ON_STYLES',
    'get_previously_on_prompt',
]
