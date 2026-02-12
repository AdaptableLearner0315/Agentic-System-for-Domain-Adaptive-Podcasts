"""
Voice Styles for Module-Specific Audio Processing

Applies different delivery characteristics to each module while keeping
the same voice consistent throughout. Uses post-processing to simulate
different narrator styles.

Styles:
- Hook: The Intriguer - compelling, slightly fast, presence boost
- Module 1: The Biographer - warm, nostalgic, measured pace
- Module 2: The Announcer - punchy, triumphant, bright
- Module 3: The Punk Chronicler - raw, urgent, electric
- Module 4: The Sage - authoritative, reflective, reverberant
"""

from pydub import AudioSegment
from pydub.effects import low_pass_filter, high_pass_filter, compress_dynamic_range


# Style definitions
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


def apply_eq(audio: AudioSegment, eq_type: str) -> AudioSegment:
    """
    Apply EQ adjustments to audio.

    Args:
        audio: Input audio segment
        eq_type: One of 'warm', 'bright', 'presence', 'edge', 'full'

    Returns:
        EQ-adjusted audio
    """
    if eq_type == "warm":
        # Boost bass, soften highs - nostalgic feel
        bass = low_pass_filter(audio, 200)
        bass = bass + 2  # +2dB bass boost
        # Soften harsh highs
        audio = low_pass_filter(audio, 8000)
        return audio.overlay(bass)

    elif eq_type == "bright":
        # Boost treble for energy and clarity
        # Extract high frequencies and boost
        highs = high_pass_filter(audio, 4000)
        highs = highs + 2  # +2dB treble boost
        return audio.overlay(highs)

    elif eq_type == "presence":
        # Boost 2-4kHz for vocal clarity and forward sound
        # Approximate by boosting mids
        mids = high_pass_filter(audio, 2000)
        mids = low_pass_filter(mids, 5000)
        mids = mids + 3  # +3dB presence boost
        return audio.overlay(mids)

    elif eq_type == "edge":
        # Aggressive mid boost for raw, punk feel
        # Also add slight saturation effect via compression
        mids = high_pass_filter(audio, 2000)
        mids = low_pass_filter(mids, 4000)
        mids = mids + 4  # +4dB aggressive mid boost
        result = audio.overlay(mids)
        # Slight high-frequency edge
        highs = high_pass_filter(audio, 5000)
        highs = highs + 1
        return result.overlay(highs)

    elif eq_type == "full":
        # Full, balanced range - minimal processing
        # Just ensure good low-end presence
        bass = low_pass_filter(audio, 150)
        bass = bass + 1  # Subtle bass warmth
        return audio.overlay(bass)

    else:
        return audio


def apply_compression(audio: AudioSegment, level: str) -> AudioSegment:
    """
    Apply dynamic range compression.

    Args:
        audio: Input audio segment
        level: 'light', 'medium', or 'heavy'

    Returns:
        Compressed audio
    """
    if level == "light":
        return compress_dynamic_range(audio, threshold=-20.0, ratio=2.0, attack=10.0, release=100.0)
    elif level == "medium":
        return compress_dynamic_range(audio, threshold=-18.0, ratio=3.0, attack=5.0, release=80.0)
    elif level == "heavy":
        return compress_dynamic_range(audio, threshold=-15.0, ratio=4.0, attack=3.0, release=50.0)
    else:
        return audio


def apply_reverb(audio: AudioSegment, decay_ms: int = 800) -> AudioSegment:
    """
    Apply simple reverb effect for gravitas.

    Args:
        audio: Input audio segment
        decay_ms: Reverb decay time

    Returns:
        Audio with reverb
    """
    result = audio

    # Create echo layers
    delays = [50, 100, 150, 200, 300, 400]
    for i, delay in enumerate(delays):
        if delay < decay_ms:
            decay_db = -6 * (i + 1)  # -6dB per echo
            echo = AudioSegment.silent(duration=delay) + audio
            echo = echo + decay_db
            echo = echo[:len(audio) + delay]

            if len(echo) > len(result):
                result = result + AudioSegment.silent(duration=len(echo) - len(result))

            result = result.overlay(echo)

    return result


def apply_speed_change(audio: AudioSegment, speed: float) -> AudioSegment:
    """
    Change audio speed without changing pitch (approximately).

    Args:
        audio: Input audio segment
        speed: Speed multiplier (1.0 = normal, >1 = faster, <1 = slower)

    Returns:
        Speed-adjusted audio
    """
    if speed == 1.0:
        return audio

    # Change playback speed by adjusting frame rate
    new_frame_rate = int(audio.frame_rate * speed)

    # Create new audio with adjusted frame rate
    adjusted = audio._spawn(audio.raw_data, overrides={
        "frame_rate": new_frame_rate
    })

    # Resample back to original frame rate
    return adjusted.set_frame_rate(audio.frame_rate)


def apply_voice_style(audio: AudioSegment, style_key: str) -> AudioSegment:
    """
    Apply a complete voice style to audio.

    Args:
        audio: Input audio segment
        style_key: One of 'hook', 'module_1', 'module_2', 'module_3', 'module_4'

    Returns:
        Styled audio segment
    """
    if style_key not in VOICE_STYLES:
        print(f"  Warning: Unknown style '{style_key}', returning unmodified audio")
        return audio

    style = VOICE_STYLES[style_key]
    print(f"  Applying style: {style['name']} ({style['description']})")

    result = audio

    # 1. Apply speed change
    if style["speed"] != 1.0:
        result = apply_speed_change(result, style["speed"])
        print(f"    Speed: {style['speed']}x")

    # 2. Apply EQ
    if style["eq"]:
        result = apply_eq(result, style["eq"])
        print(f"    EQ: {style['eq']}")

    # 3. Apply compression
    if style["compression"]:
        result = apply_compression(result, style["compression"])
        print(f"    Compression: {style['compression']}")

    # 4. Apply reverb
    if style["reverb"]:
        result = apply_reverb(result)
        print(f"    Reverb: applied")

    # 5. Apply volume boost
    if style["volume_boost_db"] != 0:
        result = result + style["volume_boost_db"]
        print(f"    Volume: +{style['volume_boost_db']}dB")

    return result


def get_style_for_module(module_id: int) -> str:
    """
    Get the style key for a given module ID.

    Args:
        module_id: Module number (1-4)

    Returns:
        Style key string
    """
    return f"module_{module_id}"


def print_style_summary():
    """Print a summary of all voice styles."""
    print("\n" + "=" * 60)
    print("VOICE STYLES SUMMARY")
    print("=" * 60)

    for key, style in VOICE_STYLES.items():
        print(f"\n{key.upper()}: {style['name']}")
        print(f"  {style['description']}")
        print(f"  Speed: {style['speed']}x | Volume: +{style['volume_boost_db']}dB")
        print(f"  EQ: {style['eq']} | Compression: {style['compression']}")
        print(f"  Reverb: {'Yes' if style['reverb'] else 'No'}")


if __name__ == "__main__":
    print_style_summary()
