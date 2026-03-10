"""
Music Intelligence Configuration
Author: Sarath

Configuration for the emotionally intelligent music system.
Contains emotion-to-music mappings, transition settings, and mode-specific parameters.
"""

# Emotion to music characteristics mapping
# Used by MusicSelector and StemComposer to match emotions with appropriate music
EMOTION_MUSIC_PROFILE = {
    "wonder": {
        "energy_range": (3, 6),
        "tempo_range": (70, 100),
        "texture": "open",
        "mode": "major",
        "primary_layers": ["atmosphere", "melody"],
        "instruments": ["piano", "pads", "strings"],
        "description": "Expansive, awe-inspiring soundscape"
    },
    "curiosity": {
        "energy_range": (3, 5),
        "tempo_range": (80, 105),
        "texture": "playful",
        "mode": "major",
        "primary_layers": ["atmosphere", "rhythm"],
        "instruments": ["piano", "plucks", "soft_percussion"],
        "description": "Inquisitive, forward-moving exploration"
    },
    "tension": {
        "energy_range": (5, 8),
        "tempo_range": (90, 120),
        "texture": "dense",
        "mode": "minor",
        "primary_layers": ["atmosphere", "rhythm"],
        "instruments": ["strings", "low_synth", "percussion"],
        "description": "Building suspense and anticipation"
    },
    "triumph": {
        "energy_range": (7, 10),
        "tempo_range": (100, 130),
        "texture": "full",
        "mode": "major",
        "primary_layers": ["atmosphere", "rhythm", "melody"],
        "instruments": ["brass", "strings", "drums", "piano"],
        "description": "Victorious, celebratory climax"
    },
    "melancholy": {
        "energy_range": (2, 4),
        "tempo_range": (60, 85),
        "texture": "sparse",
        "mode": "minor",
        "primary_layers": ["atmosphere", "melody"],
        "instruments": ["piano", "strings", "pads"],
        "description": "Reflective sadness with beauty"
    },
    "intrigue": {
        "energy_range": (3, 5),
        "tempo_range": (75, 95),
        "texture": "mysterious",
        "mode": "minor",
        "primary_layers": ["atmosphere"],
        "instruments": ["pads", "piano", "textures"],
        "description": "Mysterious curiosity and anticipation"
    },
    "excitement": {
        "energy_range": (7, 9),
        "tempo_range": (110, 140),
        "texture": "bright",
        "mode": "major",
        "primary_layers": ["rhythm", "melody"],
        "instruments": ["synths", "drums", "bass"],
        "description": "High-energy enthusiasm"
    },
    "reflection": {
        "energy_range": (2, 4),
        "tempo_range": (60, 80),
        "texture": "contemplative",
        "mode": "major",
        "primary_layers": ["atmosphere", "melody"],
        "instruments": ["piano", "pads", "soft_strings"],
        "description": "Thoughtful introspection"
    },
    "restlessness": {
        "energy_range": (5, 7),
        "tempo_range": (95, 115),
        "texture": "edgy",
        "mode": "minor",
        "primary_layers": ["rhythm", "atmosphere"],
        "instruments": ["synths", "percussion", "bass"],
        "description": "Unsettled, anticipatory energy"
    },
    "explosive_energy": {
        "energy_range": (9, 10),
        "tempo_range": (120, 150),
        "texture": "powerful",
        "mode": "major",
        "primary_layers": ["rhythm", "melody", "atmosphere"],
        "instruments": ["drums", "guitars", "synths", "bass"],
        "description": "Maximum intensity release"
    },
    "rebellion": {
        "energy_range": (8, 10),
        "tempo_range": (115, 140),
        "texture": "raw",
        "mode": "minor",
        "primary_layers": ["rhythm", "melody"],
        "instruments": ["guitars", "drums", "bass"],
        "description": "Defiant, powerful resistance"
    },
    "liberation": {
        "energy_range": (7, 9),
        "tempo_range": (100, 125),
        "texture": "soaring",
        "mode": "major",
        "primary_layers": ["melody", "atmosphere", "rhythm"],
        "instruments": ["strings", "synths", "piano"],
        "description": "Freeing, euphoric release"
    },
    "experimentation": {
        "energy_range": (4, 6),
        "tempo_range": (85, 110),
        "texture": "creative",
        "mode": "both",
        "primary_layers": ["atmosphere", "melody"],
        "instruments": ["synths", "textures", "piano"],
        "description": "Innovative, exploratory sound design"
    },
    "mastery": {
        "energy_range": (5, 7),
        "tempo_range": (90, 110),
        "texture": "refined",
        "mode": "major",
        "primary_layers": ["melody", "atmosphere"],
        "instruments": ["piano", "strings", "synths"],
        "description": "Confident, accomplished expertise"
    },
    "intensity": {
        "energy_range": (7, 9),
        "tempo_range": (100, 130),
        "texture": "focused",
        "mode": "minor",
        "primary_layers": ["rhythm", "atmosphere"],
        "instruments": ["strings", "percussion", "synths"],
        "description": "Concentrated, powerful focus"
    },
    "neutral": {
        "energy_range": (3, 5),
        "tempo_range": (80, 100),
        "texture": "balanced",
        "mode": "major",
        "primary_layers": ["atmosphere"],
        "instruments": ["piano", "pads"],
        "description": "Neutral, supportive background"
    }
}

# Transition configuration
TRANSITION_CONFIG = {
    # Default crossfade duration in milliseconds
    "crossfade_default_ms": 3000,

    # How early transitions start before segment boundary (anticipatory)
    "anticipatory_lead_ms": 2500,

    # Duration of riser accent before peaks
    "peak_riser_duration_ms": 3000,

    # Minimum segment duration to apply transitions
    "min_segment_duration_ms": 5000,

    # Maximum number of transitions per minute
    "max_transitions_per_minute": 4,

    # Energy change threshold to trigger transition (1-10 scale)
    "energy_change_threshold": 2,

    # Fade-in at start of BGM
    "fade_in_ms": 2000,

    # Fade-out at end of BGM
    "fade_out_ms": 3000,
}

# Transition types and their characteristics
TRANSITION_TYPES = {
    "crossfade": {
        "description": "Standard equal-power crossfade between tracks",
        "duration_range_ms": (2000, 5000),
        "use_cases": ["between_tracks", "emotion_shift_same_energy"]
    },
    "build": {
        "description": "Rising intensity transition with riser accent",
        "duration_range_ms": (3000, 5000),
        "use_cases": ["before_peak", "tension_increase"]
    },
    "release": {
        "description": "Gentle fade with layer removal",
        "duration_range_ms": (2000, 3000),
        "use_cases": ["after_peak", "tension_decrease"]
    },
    "shift": {
        "description": "Quick texture morph at same energy level",
        "duration_range_ms": (1000, 2000),
        "use_cases": ["emotion_change_same_energy"]
    }
}

# Normal mode settings (fast generation)
NORMAL_MODE = {
    # Maximum number of tracks to select
    "max_tracks": 3,

    # Target latency for music selection/assembly
    "target_latency_ms": 500,

    # Transition style
    "transition_style": "crossfade",

    # Crossfade duration
    "crossfade_ms": 3000,

    # Accent density
    "accent_density": "low",

    # Number of accent points to place
    "max_accent_points": 2,

    # Use pre-composed tracks only
    "use_stems": False,

    # Emotion granularity (module-level)
    "granularity": "module",
}

# Pro mode settings (high quality)
PRO_MODE = {
    # Stem layers to use
    "stem_layers": ["atmosphere", "rhythm", "melody"],

    # Target latency for composition
    "target_latency_ms": 2000,

    # Transition style
    "transition_style": "anticipatory",

    # Crossfade duration
    "crossfade_ms": 4000,

    # Accent density
    "accent_density": "high",

    # Maximum accent points
    "max_accent_points": 8,

    # Use dynamic stem composition
    "use_stems": True,

    # Emotion granularity (chunk-level)
    "granularity": "chunk",

    # Energy envelope smoothing (ms)
    "energy_smoothing_ms": 1000,
}

# Energy level to layer mapping
# Maps tension_level (1-5) to which stem layers should be active
ENERGY_TO_LAYERS = {
    1: ["atmosphere"],  # Very low - sparse atmosphere only
    2: ["atmosphere"],  # Low - atmosphere, subtle texture
    3: ["atmosphere", "rhythm"],  # Medium - add light rhythm
    4: ["atmosphere", "rhythm", "melody"],  # High - all layers, moderate intensity
    5: ["atmosphere", "rhythm", "melody"],  # Climax - all layers full intensity
}

# Layer volume curves by energy level
LAYER_VOLUME_CURVES = {
    "atmosphere": {
        1: -6,   # dB adjustment at energy 1
        2: -3,
        3: 0,
        4: 0,
        5: 2,
    },
    "rhythm": {
        1: -20,  # Silent at energy 1
        2: -15,
        3: -6,
        4: -3,
        5: 0,
    },
    "melody": {
        1: -20,  # Silent at energy 1
        2: -20,
        3: -12,
        4: -6,
        5: 0,
    }
}

# Accent types and their properties
ACCENT_TYPES = {
    "riser": {
        "description": "Building sweep before tension peak",
        "duration_range_ms": (2000, 4000),
        "placement": "before_peak",
        "offset_ms": -3000,  # Starts 3s before peak
    },
    "impact": {
        "description": "Percussive hit at peak moment",
        "duration_range_ms": (300, 800),
        "placement": "at_peak",
        "offset_ms": 0,
    },
    "swell": {
        "description": "Emotional crescendo for revelations",
        "duration_range_ms": (1000, 2000),
        "placement": "at_emotion",
        "emotions": ["wonder", "triumph", "liberation"],
    },
    "drop": {
        "description": "Sudden reduction/silence after climax",
        "duration_range_ms": (500, 1500),
        "placement": "after_peak",
        "offset_ms": 500,  # Starts 0.5s after peak
    }
}

# Harmonic compatibility matrix
# True if tracks in these keys can transition smoothly
HARMONIC_COMPATIBILITY = {
    "C_major": ["G_major", "F_major", "A_minor", "E_minor", "D_minor"],
    "G_major": ["C_major", "D_major", "E_minor", "B_minor", "A_minor"],
    "D_major": ["G_major", "A_major", "B_minor", "F#_minor", "E_minor"],
    "A_major": ["D_major", "E_major", "F#_minor", "C#_minor", "B_minor"],
    "E_major": ["A_major", "B_major", "C#_minor", "G#_minor", "F#_minor"],
    "F_major": ["C_major", "Bb_major", "D_minor", "A_minor", "G_minor"],
    "A_minor": ["C_major", "E_minor", "D_minor", "G_major", "F_major"],
    "E_minor": ["G_major", "A_minor", "B_minor", "C_major", "D_major"],
    "D_minor": ["F_major", "A_minor", "G_minor", "C_major", "Bb_major"],
    "B_minor": ["D_major", "E_minor", "F#_minor", "G_major", "A_major"],
}


def get_mode_config(mode: str) -> dict:
    """
    Get configuration for specified mode.

    Args:
        mode: "normal" or "pro"

    Returns:
        Mode configuration dictionary
    """
    return PRO_MODE if mode == "pro" else NORMAL_MODE


def get_emotion_profile(emotion: str) -> dict:
    """
    Get music profile for an emotion.

    Args:
        emotion: Emotion name (case-insensitive)

    Returns:
        Emotion music profile dictionary
    """
    return EMOTION_MUSIC_PROFILE.get(
        emotion.lower(),
        EMOTION_MUSIC_PROFILE["neutral"]
    )


def get_layers_for_energy(energy_level: int) -> list:
    """
    Get active layers for a given energy/tension level.

    Args:
        energy_level: Tension level 1-5

    Returns:
        List of layer names that should be active
    """
    level = max(1, min(5, energy_level))  # Clamp to 1-5
    return ENERGY_TO_LAYERS[level]


def is_harmonic_compatible(key1: str, key2: str) -> bool:
    """
    Check if two musical keys are harmonically compatible.

    Args:
        key1: First key (e.g., "C_major")
        key2: Second key

    Returns:
        True if keys can transition smoothly
    """
    if key1 == key2:
        return True
    compatible = HARMONIC_COMPATIBILITY.get(key1, [])
    return key2 in compatible


__all__ = [
    'EMOTION_MUSIC_PROFILE',
    'TRANSITION_CONFIG',
    'TRANSITION_TYPES',
    'NORMAL_MODE',
    'PRO_MODE',
    'ENERGY_TO_LAYERS',
    'LAYER_VOLUME_CURVES',
    'ACCENT_TYPES',
    'HARMONIC_COMPATIBILITY',
    'get_mode_config',
    'get_emotion_profile',
    'get_layers_for_energy',
    'is_harmonic_compatible',
]
