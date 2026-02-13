"""
Voice Style Engine
Author: Sarath

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
from typing import Optional

from config.voice_styles import VOICE_STYLES


class VoiceStyleEngine:
    """
    Engine for applying module-specific voice styles to audio.

    Uses post-processing effects (EQ, compression, reverb, speed) to
    create distinct narrator personas while maintaining voice consistency.
    """

    def __init__(self):
        """Initialize the Voice Style Engine."""
        self.styles = VOICE_STYLES
        print(f"[VoiceStyleEngine] Loaded {len(self.styles)} voice styles")

    def get_style(self, style_key: str) -> Optional[dict]:
        """
        Get style configuration by key.

        Args:
            style_key: Style key (e.g., 'hook', 'module_1')

        Returns:
            Style configuration dictionary or None
        """
        return self.styles.get(style_key)

    def get_style_for_module(self, module_id: int) -> str:
        """
        Get the style key for a given module ID.

        Args:
            module_id: Module number (1-4)

        Returns:
            Style key string
        """
        return f"module_{module_id}"

    def apply_eq(self, audio: AudioSegment, eq_type: str) -> AudioSegment:
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
            audio = low_pass_filter(audio, 8000)
            return audio.overlay(bass)

        elif eq_type == "bright":
            # Boost treble for energy and clarity
            highs = high_pass_filter(audio, 4000)
            highs = highs + 2  # +2dB treble boost
            return audio.overlay(highs)

        elif eq_type == "presence":
            # Boost 2-4kHz for vocal clarity and forward sound
            mids = high_pass_filter(audio, 2000)
            mids = low_pass_filter(mids, 5000)
            mids = mids + 3  # +3dB presence boost
            return audio.overlay(mids)

        elif eq_type == "edge":
            # Aggressive mid boost for raw, punk feel
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
            bass = low_pass_filter(audio, 150)
            bass = bass + 1  # Subtle bass warmth
            return audio.overlay(bass)

        else:
            return audio

    def apply_compression(self, audio: AudioSegment, level: str) -> AudioSegment:
        """
        Apply dynamic range compression.

        Args:
            audio: Input audio segment
            level: 'light', 'medium', or 'heavy'

        Returns:
            Compressed audio
        """
        if level == "light":
            return compress_dynamic_range(
                audio, threshold=-20.0, ratio=2.0, attack=10.0, release=100.0
            )
        elif level == "medium":
            return compress_dynamic_range(
                audio, threshold=-18.0, ratio=3.0, attack=5.0, release=80.0
            )
        elif level == "heavy":
            return compress_dynamic_range(
                audio, threshold=-15.0, ratio=4.0, attack=3.0, release=50.0
            )
        else:
            return audio

    def apply_reverb(self, audio: AudioSegment, decay_ms: int = 800) -> AudioSegment:
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

    def apply_speed_change(self, audio: AudioSegment, speed: float) -> AudioSegment:
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

    def apply_style(self, audio: AudioSegment, style_key: str) -> AudioSegment:
        """
        Apply a complete voice style to audio.

        Args:
            audio: Input audio segment
            style_key: One of 'hook', 'module_1', 'module_2', 'module_3', 'module_4'

        Returns:
            Styled audio segment
        """
        if style_key not in self.styles:
            print(f"  Warning: Unknown style '{style_key}', returning unmodified audio")
            return audio

        style = self.styles[style_key]
        print(f"  Applying style: {style['name']} ({style['description']})")

        result = audio

        # 1. Apply speed change
        if style["speed"] != 1.0:
            result = self.apply_speed_change(result, style["speed"])
            print(f"    Speed: {style['speed']}x")

        # 2. Apply EQ
        if style["eq"]:
            result = self.apply_eq(result, style["eq"])
            print(f"    EQ: {style['eq']}")

        # 3. Apply compression
        if style["compression"]:
            result = self.apply_compression(result, style["compression"])
            print(f"    Compression: {style['compression']}")

        # 4. Apply reverb
        if style["reverb"]:
            result = self.apply_reverb(result)
            print(f"    Reverb: applied")

        # 5. Apply volume boost
        if style["volume_boost_db"] != 0:
            result = result + style["volume_boost_db"]
            print(f"    Volume: +{style['volume_boost_db']}dB")

        return result

    def print_style_summary(self):
        """Print a summary of all voice styles."""
        print("\n" + "=" * 60)
        print("VOICE STYLES SUMMARY")
        print("=" * 60)

        for key, style in self.styles.items():
            print(f"\n{key.upper()}: {style['name']}")
            print(f"  {style['description']}")
            print(f"  Speed: {style['speed']}x | Volume: +{style['volume_boost_db']}dB")
            print(f"  EQ: {style['eq']} | Compression: {style['compression']}")
            print(f"  Reverb: {'Yes' if style['reverb'] else 'No'}")


if __name__ == "__main__":
    engine = VoiceStyleEngine()
    engine.print_style_summary()
