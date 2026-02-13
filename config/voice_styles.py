"""
Voice Styles Configuration
Author: Sarath

Contains voice style definitions for module-specific audio processing.

Styles:
- Hook: The Intriguer - compelling, slightly fast, presence boost
- Module 1: The Biographer - warm, nostalgic, measured pace
- Module 2: The Announcer - punchy, triumphant, bright
- Module 3: The Punk Chronicler - raw, urgent, electric
- Module 4: The Sage - authoritative, reflective, reverberant
"""

VOICE_STYLES = {
    "hook": {
        "name": "The Intriguer",
        "speed": 1.05,
        "volume_boost_db": 2,
        "eq": "presence",  # boost 2-4kHz for clarity
        "compression": "light",
        "reverb": False,
        "description": "Compelling, slightly fast, clear enunciation"
    },
    "module_1": {
        "name": "The Biographer",
        "speed": 0.95,
        "volume_boost_db": 0,
        "eq": "warm",  # boost bass, cut harsh highs
        "compression": None,
        "reverb": False,
        "description": "Warm, nostalgic, measured pace"
    },
    "module_2": {
        "name": "The Announcer",
        "speed": 1.08,
        "volume_boost_db": 3,
        "eq": "bright",  # boost treble for energy
        "compression": "medium",
        "reverb": False,
        "description": "Punchy, triumphant, energetic"
    },
    "module_3": {
        "name": "The Punk Chronicler",
        "speed": 1.12,
        "volume_boost_db": 4,
        "eq": "edge",  # aggressive mid boost
        "compression": "heavy",
        "reverb": False,
        "description": "Raw, urgent, electric"
    },
    "module_4": {
        "name": "The Sage",
        "speed": 0.92,
        "volume_boost_db": 1,
        "eq": "full",  # balanced, full range
        "compression": "light",
        "reverb": False,  # Removed reverb for consistency with other modules
        "description": "Authoritative, reflective, reverential"
    }
}
