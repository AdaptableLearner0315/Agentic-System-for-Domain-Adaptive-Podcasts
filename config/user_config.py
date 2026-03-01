"""
User Configuration
Author: Sarath

Persistent user preferences for podcast generation.
Supports saving/loading configs and interactive configuration wizard.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field, asdict


@dataclass
class UserConfig:
    """
    Persistent user configuration for podcast generation.

    Stores preferences for:
    - Default mode (normal/pro)
    - Voice settings
    - Music settings
    - Visual settings
    - Output preferences
    """
    # General settings
    default_mode: str = "normal"
    output_directory: Optional[str] = None

    # Voice settings
    voice_preset: str = "default"
    custom_pronunciations: Dict[str, str] = field(default_factory=dict)

    # Music settings
    music_genre: str = "cinematic"
    bgm_intensity: str = "medium"  # low, medium, high

    # Visual settings
    image_style: str = "cinematic"
    image_count_override: Optional[int] = None

    # Quality settings
    director_review: bool = True
    max_review_rounds: int = 3

    # Progress settings
    show_progress: bool = True
    verbose: bool = False

    def save(self, path: str):
        """
        Save configuration to file.

        Args:
            path: Path to save config file
        """
        config_path = Path(path)
        config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(config_path, 'w') as f:
            json.dump(asdict(self), f, indent=2)

        print(f"Configuration saved to: {config_path}")

    @classmethod
    def load(cls, path: str) -> 'UserConfig':
        """
        Load configuration from file.

        Args:
            path: Path to config file

        Returns:
            UserConfig instance
        """
        config_path = Path(path)
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")

        with open(config_path, 'r') as f:
            data = json.load(f)

        # Filter to valid fields
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}

        return cls(**filtered_data)

    @classmethod
    def load_or_default(cls, path: str) -> 'UserConfig':
        """
        Load configuration or return default if not found.

        Args:
            path: Path to config file

        Returns:
            UserConfig instance
        """
        try:
            return cls.load(path)
        except FileNotFoundError:
            return cls()

    @classmethod
    def from_interactive(cls) -> 'UserConfig':
        """
        Create configuration through interactive CLI prompts.

        Returns:
            UserConfig instance
        """
        print("\n" + "="*50)
        print("Nell Pro Configuration Wizard")
        print("="*50 + "\n")

        config = cls()

        # Default mode
        print("Select default generation mode:")
        print("  1. Normal (fast, ~2 minutes)")
        print("  2. Pro (high quality, ~6 minutes)")
        choice = input("Choice [1]: ").strip() or "1"
        config.default_mode = "pro" if choice == "2" else "normal"

        # Voice preset
        print("\nSelect voice preset:")
        print("  1. Default (balanced)")
        print("  2. Energetic (faster, brighter)")
        print("  3. Calm (slower, warmer)")
        print("  4. Dramatic (slower, fuller)")
        choice = input("Choice [1]: ").strip() or "1"
        presets = {"1": "default", "2": "energetic", "3": "calm", "4": "dramatic"}
        config.voice_preset = presets.get(choice, "default")

        # Music genre
        print("\nSelect music genre:")
        print("  1. Cinematic (orchestral, emotional)")
        print("  2. Ambient (atmospheric, subtle)")
        print("  3. Electronic (modern, dynamic)")
        print("  4. Acoustic (warm, organic)")
        print("  5. Documentary (professional, understated)")
        choice = input("Choice [1]: ").strip() or "1"
        genres = {
            "1": "cinematic", "2": "ambient", "3": "electronic",
            "4": "acoustic", "5": "documentary"
        }
        config.music_genre = genres.get(choice, "cinematic")

        # Image style
        print("\nSelect image style:")
        print("  1. Cinematic (film grain, documentary)")
        print("  2. Artistic (creative, fine art)")
        print("  3. Minimal (clean, modern)")
        print("  4. Vintage (retro, nostalgic)")
        print("  5. Dramatic (bold, high contrast)")
        choice = input("Choice [1]: ").strip() or "1"
        styles = {
            "1": "cinematic", "2": "artistic", "3": "minimal",
            "4": "vintage", "5": "dramatic"
        }
        config.image_style = styles.get(choice, "cinematic")

        # Director review (Pro mode only)
        print("\nEnable Director review? (improves script quality)")
        choice = input("Enable [Y/n]: ").strip().lower()
        config.director_review = choice != "n"

        print("\n" + "="*50)
        print("Configuration Complete!")
        print("="*50)
        print(f"  Mode: {config.default_mode}")
        print(f"  Voice: {config.voice_preset}")
        print(f"  Music: {config.music_genre}")
        print(f"  Images: {config.image_style}")
        print(f"  Director Review: {config.director_review}")

        return config

    def to_pro_config(self) -> 'ProConfig':
        """
        Convert to ProConfig for Pro pipeline.

        Returns:
            ProConfig instance
        """
        from pipelines.pro_pipeline import ProConfig

        return ProConfig(
            director_review=self.director_review,
            max_review_rounds=self.max_review_rounds,
            voice_preset=self.voice_preset,
            custom_pronunciations=self.custom_pronunciations,
            music_genre=self.music_genre,
            image_style=self.image_style,
        )


# Default config path
DEFAULT_CONFIG_PATH = Path.home() / ".nell" / "config.json"


def get_default_config() -> UserConfig:
    """Get default user configuration."""
    return UserConfig.load_or_default(str(DEFAULT_CONFIG_PATH))


def save_default_config(config: UserConfig):
    """Save as default user configuration."""
    config.save(str(DEFAULT_CONFIG_PATH))


def run_config_wizard() -> UserConfig:
    """Run interactive configuration wizard and save."""
    config = UserConfig.from_interactive()

    save = input("\nSave as default configuration? [Y/n]: ").strip().lower()
    if save != "n":
        save_default_config(config)

    return config


__all__ = [
    'UserConfig',
    'DEFAULT_CONFIG_PATH',
    'get_default_config',
    'save_default_config',
    'run_config_wizard',
]
