"""
Path Constants
Author: Sarath

Centralized path definitions for the podcast enhancement system.
"""

from pathlib import Path

# Base directory (project root)
BASE_DIR = Path(__file__).parent.parent

# Main output directory
OUTPUT_DIR = BASE_DIR / "Output"

# Audio directories
AUDIO_DIR = OUTPUT_DIR / "audio"
TTS_DIR = AUDIO_DIR / "tts"
BGM_DIR = AUDIO_DIR / "bgm"
BGM_V2_DIR = AUDIO_DIR / "bgm_v2"
BGM_V2_DAISY_DIR = AUDIO_DIR / "bgm_v2_daisy"
PREVIEW_DIR = AUDIO_DIR / "previews"
PREVIEW_V2_DIR = AUDIO_DIR / "previews_v2"
PREVIEW_VOICE_ONLY_DIR = AUDIO_DIR / "previews_voice_only"
FINAL_AUDIO_DIR = AUDIO_DIR / "final_v2"

# Visual directories
VISUALS_DIR = OUTPUT_DIR / "Visuals Included"
HOOK_VISUALS_DIR = VISUALS_DIR / "hook"
MODULE_1_VISUALS_DIR = VISUALS_DIR / "module_1"
MODULE_2_VISUALS_DIR = VISUALS_DIR / "module_2"
MODULE_3_VISUALS_DIR = VISUALS_DIR / "module_3"
MODULE_4_VISUALS_DIR = VISUALS_DIR / "module_4"
VOICE_ONLY_VIDEO_DIR = VISUALS_DIR / "voice_only"
V2_DAISY_VIDEO_DIR = VISUALS_DIR / "v2_daisy"

# Script files
ENHANCED_SCRIPT_PATH = OUTPUT_DIR / "enhanced_script.json"

# Input directory
INPUT_DIR = BASE_DIR / "Input"


def get_module_visuals_dir(module_id: int) -> Path:
    """
    Get the visuals directory for a specific module.

    Args:
        module_id: Module number (1-4)

    Returns:
        Path to the module's visuals directory
    """
    return VISUALS_DIR / f"module_{module_id}"


def ensure_directories():
    """Create all required directories if they don't exist."""
    directories = [
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
        MODULE_1_VISUALS_DIR,
        MODULE_2_VISUALS_DIR,
        MODULE_3_VISUALS_DIR,
        MODULE_4_VISUALS_DIR,
        VOICE_ONLY_VIDEO_DIR,
        V2_DAISY_VIDEO_DIR,
        INPUT_DIR,
    ]
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
