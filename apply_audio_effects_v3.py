"""
Apply audio effects to existing final_enhanced_v2.mp3
NO script changes, NO TTS regeneration - just audio post-processing.

Timestamps based on user specifications:
- 0:00 - Breath before first word
- 0:15 - 1.5s silence after "heard before"
- 0:30 - Volcanic sub-bass boom + geothermal hiss
- 0:45 - Ice crack on "glaciers"
- 1:20 - Vinyl crackle + guitar feedback for punk section
- 1:45 - Slowdown + pitch shift for emotional section
- 2:10 - 2.0s silence after rhetorical moment
- 2:30 - Electric zap + crystalline chime
- 3:00 - Music swell/bloom effect
- Era EQ: 1970s (AM radio), 1990s (Hi-Fi)
- Ending: Reverb tail + hard cut
"""

from pathlib import Path
from pydub import AudioSegment
from pydub.generators import Sine, WhiteNoise
from pydub.effects import low_pass_filter, high_pass_filter

BASE_DIR = Path(__file__).parent
INPUT_FILE = BASE_DIR / "Output" / "audio" / "final_enhanced_v2.mp3"
OUTPUT_FILE = BASE_DIR / "Output" / "audio" / "final_enhanced_v3.mp3"


# =============================================================================
# SOUND EFFECT GENERATORS
# =============================================================================

def generate_breath(duration_ms=300):
    """Sharp intake of breath."""
    noise = WhiteNoise().to_audio_segment(duration=duration_ms)
    breath = noise.fade_in(50).fade_out(100)
    breath = low_pass_filter(breath, 2000)
    breath = high_pass_filter(breath, 200)
    return breath - 12


def generate_sub_bass_boom(duration_ms=1500, freq=50):
    """Sub-bass boom (40-60Hz)."""
    boom = Sine(freq).to_audio_segment(duration=duration_ms)
    boom2 = Sine(freq * 2).to_audio_segment(duration=duration_ms) - 10
    boom = boom.overlay(boom2)
    boom = boom.fade_in(300).fade_out(500)
    return boom - 3


def generate_geothermal_hiss(duration_ms=3000):
    """Geothermal vent hissing steam."""
    noise = WhiteNoise().to_audio_segment(duration=duration_ms)
    hiss = high_pass_filter(noise, 1000)
    hiss = low_pass_filter(hiss, 8000)
    hiss = hiss.fade_in(500).fade_out(1000)
    return hiss - 18


def generate_ice_crack(duration_ms=200):
    """Ice cracking sound."""
    crack = WhiteNoise().to_audio_segment(duration=duration_ms)
    crack = high_pass_filter(crack, 2000)
    crack = crack.fade_in(5).fade_out(50)
    snap = Sine(4000).to_audio_segment(duration=50).fade_in(5).fade_out(20)
    crack = crack.overlay(snap)
    return crack - 8


def generate_vinyl_crackle(duration_ms=15000):
    """Vinyl crackle/tape hiss."""
    import numpy as np
    noise = WhiteNoise().to_audio_segment(duration=duration_ms)
    crackle = low_pass_filter(noise, 3000)
    crackle = high_pass_filter(crackle, 500)
    crackle = crackle - 25
    # Add pops
    for i in range(int(duration_ms / 500)):
        pop_time = int(np.random.uniform(0, duration_ms - 100))
        pop = Sine(1000 + np.random.uniform(-200, 200)).to_audio_segment(duration=30)
        pop = pop.fade_in(5).fade_out(10) - 20
        crackle = crackle.overlay(pop, position=pop_time)
    return crackle


def generate_feedback_squeal(duration_ms=5000):
    """Guitar amp feedback."""
    feedback = Sine(2500).to_audio_segment(duration=duration_ms)
    feedback2 = Sine(3750).to_audio_segment(duration=duration_ms) - 6
    feedback = feedback.overlay(feedback2)
    feedback = feedback.fade_in(1500).fade_out(1000)
    return feedback - 28


def generate_electric_zap(duration_ms=300):
    """Static electricity zap."""
    import numpy as np
    zap = AudioSegment.silent(duration=duration_ms)
    for i in range(5):
        freq = 3000 + np.random.uniform(-500, 500)
        burst = Sine(freq).to_audio_segment(duration=50)
        burst = burst.fade_in(5).fade_out(20) - 10
        pos = int(i * duration_ms / 5)
        zap = zap.overlay(burst, position=pos)
    noise = WhiteNoise().to_audio_segment(duration=duration_ms)
    noise = high_pass_filter(noise, 4000) - 15
    zap = zap.overlay(noise)
    return zap.fade_in(20).fade_out(50)


def generate_crystalline_chime(duration_ms=1500):
    """Crystalline chime."""
    chime = AudioSegment.silent(duration=duration_ms)
    for i, freq in enumerate([1200, 1800, 2400, 3000, 3600]):
        tone = Sine(freq).to_audio_segment(duration=duration_ms)
        tone = tone.fade_in(10).fade_out(800) - (10 + i * 2)
        chime = chime.overlay(tone)
    return chime - 5


def generate_cello_drone(duration_ms=5000):
    """Cello/violin drone."""
    base_freq = 130
    drone = Sine(base_freq).to_audio_segment(duration=duration_ms)
    for h in [2, 3, 4, 5]:
        harm = Sine(base_freq * h).to_audio_segment(duration=duration_ms) - (6 * h)
        drone = drone.overlay(harm)
    drone = drone.fade_in(1500).fade_out(1500)
    drone = low_pass_filter(drone, 2000)
    return drone - 12


def apply_reverb_tail(audio, tail_duration_ms=4000):
    """Apply reverb tail."""
    result = audio
    delays = [100, 200, 350, 500, 700, 1000, 1500, 2000, 2500, 3000]
    for i, delay in enumerate(delays):
        if delay < tail_duration_ms:
            decay = -6 * (i + 1)
            echo = AudioSegment.silent(duration=delay) + audio
            echo = echo + decay
            echo = echo[:len(audio) + delay]
            if len(echo) > len(result):
                result = result + AudioSegment.silent(duration=len(echo) - len(result))
            result = result.overlay(echo)
    result = result + AudioSegment.silent(duration=tail_duration_ms - 3000)
    return result


def pan_audio(audio, pan_percent):
    """Pan audio (-100 left, +100 right)."""
    return audio.pan(pan_percent / 100)


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 70)
    print("APPLYING AUDIO EFFECTS TO final_enhanced_v2.mp3 -> v3")
    print("=" * 70)

    # Load audio
    print(f"\nLoading: {INPUT_FILE}")
    audio = AudioSegment.from_file(str(INPUT_FILE))
    original_duration = len(audio)
    print(f"Duration: {original_duration / 1000:.1f}s ({original_duration / 60000:.1f} min)")

    # Track offset as we insert silences
    offset = 0

    # =========================================================================
    # PHASE 1: VOCAL SURGERY
    # =========================================================================
    print("\n" + "-" * 50)
    print("PHASE 1: VOCAL SURGERY")
    print("-" * 50)

    # 0:00 - Breath before first word
    print("\n[0:00] Adding breath before 'Picture'...")
    breath = generate_breath(300)
    audio = breath + audio
    offset += 300
    print("  Added 0.3s breath")

    # 0:15 - 1.5s silence after "heard before"
    print("\n[0:15] Adding 1.5s silence after 'heard before'...")
    pos = 15000 + offset
    audio = audio[:pos] + AudioSegment.silent(duration=1500) + audio[pos:]
    offset += 1500
    print("  Added 1.5s silence")

    # 2:10 - 2.0s silence (rhetorical pause)
    print("\n[2:10] Adding 2.0s rhetorical pause...")
    pos = 130000 + offset
    audio = audio[:pos] + AudioSegment.silent(duration=2000) + audio[pos:]
    offset += 2000
    print("  Added 2.0s silence")

    # 1:45 - Slowdown section (stretch 10-15%)
    print("\n[1:45] Applying slowdown to emotional section...")
    slow_start = 105000 + offset
    slow_end = 115000 + offset
    before = audio[:slow_start]
    slow_section = audio[slow_start:slow_end]
    after = audio[slow_end:]

    # Slow down by changing frame rate
    new_rate = int(slow_section.frame_rate * 0.88)  # 12% slower
    slowed = slow_section._spawn(slow_section.raw_data, overrides={"frame_rate": new_rate})
    slowed = slowed.set_frame_rate(slow_section.frame_rate)

    audio = before + slowed + after
    offset += len(slowed) - len(slow_section)
    print(f"  Applied 12% slowdown to 1:45-1:55 section")

    # =========================================================================
    # PHASE 2: SOUNDSCAPE LAYER
    # =========================================================================
    print("\n" + "-" * 50)
    print("PHASE 2: SOUNDSCAPE LAYER")
    print("-" * 50)

    # 0:30 - Volcanic sub-bass boom
    print("\n[0:30] Adding volcanic sub-bass boom...")
    pos = 30000 + offset
    boom = generate_sub_bass_boom(1500, freq=50)
    audio = audio.overlay(boom, position=pos)
    print("  Added sub-bass boom")

    # 0:30 - Geothermal hiss
    print("\n[0:30] Adding geothermal hiss...")
    hiss = generate_geothermal_hiss(3000)
    audio = audio.overlay(hiss, position=pos + 500)
    print("  Added 3s geothermal hiss")

    # 0:45 - Ice crack on "glaciers"
    print("\n[0:45] Adding ice crack...")
    pos = 45000 + offset
    crack = generate_ice_crack(200)
    audio = audio.overlay(crack, position=pos)
    print("  Added ice crack")

    # 1:20 - Vinyl crackle for punk section (15 seconds)
    print("\n[1:20] Adding vinyl crackle for punk section...")
    pos = 80000 + offset
    crackle = generate_vinyl_crackle(15000)
    audio = audio.overlay(crackle, position=pos)
    print("  Added 15s vinyl crackle")

    # 1:20 - Guitar feedback (panned 30% left)
    print("\n[1:20] Adding guitar feedback (panned 30% left)...")
    feedback = generate_feedback_squeal(5000)
    feedback = pan_audio(feedback, -30)
    audio = audio.overlay(feedback, position=pos + 5000)
    print("  Added feedback squeal")

    # 2:30 - Electric zap
    print("\n[2:30] Adding electric zap...")
    pos = 150000 + offset
    zap = generate_electric_zap(300)
    audio = audio.overlay(zap, position=pos)
    print("  Added electric zap")

    # 2:30 - Crystalline chime
    print("\n[2:30] Adding crystalline chime...")
    chime = generate_crystalline_chime(1500)
    audio = audio.overlay(chime, position=pos + 500)
    print("  Added crystalline chime")

    # 1:50 - Cello drone for emotional moment
    print("\n[1:50] Adding cello drone...")
    pos = 110000 + offset
    drone = generate_cello_drone(5000)
    audio = audio.overlay(drone, position=pos)
    print("  Added cello drone")

    # =========================================================================
    # PHASE 3: ERA-SPECIFIC EQ
    # =========================================================================
    print("\n" + "-" * 50)
    print("PHASE 3: ERA-SPECIFIC EQ")
    print("-" * 50)

    # 1970s section (0:45-1:30) - AM radio effect
    print("\n[0:45-1:30] Applying AM radio EQ to 1970s section...")
    start_70s = 45000 + offset
    end_70s = 90000 + offset

    before = audio[:start_70s]
    section_70s = audio[start_70s:end_70s]
    after = audio[end_70s:]

    section_70s = high_pass_filter(section_70s, 200)
    section_70s = low_pass_filter(section_70s, 4000)

    audio = before + section_70s + after
    print("  Applied high-pass 200Hz + low-pass 4kHz")

    # 1990s section (6:00-7:30) - Hi-Fi bass boost
    print("\n[6:00-7:30] Applying Hi-Fi EQ to 1990s section...")
    start_90s = 360000 + offset
    end_90s = min(450000 + offset, len(audio))

    if start_90s < len(audio):
        before = audio[:start_90s]
        section_90s = audio[start_90s:end_90s]
        after = audio[end_90s:]

        # Bass boost
        bass = low_pass_filter(section_90s, 100) + 2
        section_90s = section_90s.overlay(bass)

        audio = before + section_90s + after
        print("  Applied bass boost +2dB at 60Hz")

    # =========================================================================
    # PHASE 4: MIC DROP ENDING
    # =========================================================================
    print("\n" + "-" * 50)
    print("PHASE 4: MIC DROP ENDING")
    print("-" * 50)

    print("\n[END] Applying reverb tail to final word...")
    # Get last 3 seconds
    final_start = len(audio) - 3000
    before = audio[:final_start]
    final_section = audio[final_start:]

    # Apply reverb
    final_with_reverb = apply_reverb_tail(final_section, 4000)

    audio = before + final_with_reverb

    # Add 4 seconds silence
    audio = audio + AudioSegment.silent(duration=4000)
    print("  Added reverb tail + 4s silence")

    # =========================================================================
    # EXPORT
    # =========================================================================
    print("\n" + "-" * 50)
    print("EXPORT")
    print("-" * 50)

    audio = audio.normalize()
    audio.export(str(OUTPUT_FILE), format="mp3", bitrate="192k")

    print(f"\nOriginal duration: {original_duration / 1000:.1f}s")
    print(f"Final duration: {len(audio) / 1000:.1f}s")
    print(f"\nSaved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
