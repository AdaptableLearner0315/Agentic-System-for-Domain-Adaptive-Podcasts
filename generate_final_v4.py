"""
Generate final_enhanced_v4.mp3 with module-specific voice styles.

Each module gets a distinct delivery style while maintaining the same voice:
- Hook: The Intriguer - compelling, slightly fast
- Module 1: The Biographer - warm, nostalgic, measured
- Module 2: The Announcer - punchy, triumphant
- Module 3: The Punk Chronicler - raw, urgent, electric
- Module 4: The Sage - authoritative, reflective

Also includes all audio surgery effects from v3.
"""

import json
import numpy as np
from pathlib import Path
from pydub import AudioSegment
from pydub.generators import Sine, WhiteNoise
from pydub.effects import low_pass_filter, high_pass_filter

# Import voice styles
import sys
sys.path.insert(0, str(Path(__file__).parent))
from utils.voice_styles import apply_voice_style, VOICE_STYLES, print_style_summary

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "Output" / "audio"


# =============================================================================
# SOUND EFFECT GENERATORS (from v3)
# =============================================================================

def generate_breath(duration_ms=300):
    noise = WhiteNoise().to_audio_segment(duration=duration_ms)
    breath = noise.fade_in(50).fade_out(100)
    breath = low_pass_filter(breath, 2000)
    breath = high_pass_filter(breath, 200)
    return breath - 12


def generate_sub_bass_boom(duration_ms=1500, freq=50):
    boom = Sine(freq).to_audio_segment(duration=duration_ms)
    boom2 = Sine(freq * 2).to_audio_segment(duration=duration_ms) - 10
    boom = boom.overlay(boom2).fade_in(300).fade_out(500)
    return boom - 3


def generate_geothermal_hiss(duration_ms=3000):
    noise = WhiteNoise().to_audio_segment(duration=duration_ms)
    hiss = high_pass_filter(noise, 1000)
    hiss = low_pass_filter(hiss, 8000)
    return hiss.fade_in(500).fade_out(1000) - 18


def generate_ice_crack(duration_ms=200):
    crack = WhiteNoise().to_audio_segment(duration=duration_ms)
    crack = high_pass_filter(crack, 2000).fade_in(5).fade_out(50)
    snap = Sine(4000).to_audio_segment(duration=50).fade_in(5).fade_out(20)
    return crack.overlay(snap) - 8


def generate_vinyl_crackle(duration_ms=15000):
    noise = WhiteNoise().to_audio_segment(duration=duration_ms)
    crackle = low_pass_filter(noise, 3000)
    crackle = high_pass_filter(crackle, 500) - 25
    for i in range(int(duration_ms / 500)):
        pop_time = int(np.random.uniform(0, duration_ms - 100))
        pop = Sine(1000 + np.random.uniform(-200, 200)).to_audio_segment(duration=30)
        pop = pop.fade_in(5).fade_out(10) - 20
        crackle = crackle.overlay(pop, position=pop_time)
    return crackle


def generate_feedback_squeal(duration_ms=5000):
    feedback = Sine(2500).to_audio_segment(duration=duration_ms)
    feedback2 = Sine(3750).to_audio_segment(duration=duration_ms) - 6
    feedback = feedback.overlay(feedback2).fade_in(1500).fade_out(1000)
    return feedback - 28


def generate_electric_zap(duration_ms=300):
    zap = AudioSegment.silent(duration=duration_ms)
    for i in range(5):
        freq = 3000 + np.random.uniform(-500, 500)
        burst = Sine(freq).to_audio_segment(duration=50).fade_in(5).fade_out(20) - 10
        zap = zap.overlay(burst, position=int(i * duration_ms / 5))
    noise = high_pass_filter(WhiteNoise().to_audio_segment(duration=duration_ms), 4000) - 15
    return zap.overlay(noise).fade_in(20).fade_out(50)


def generate_crystalline_chime(duration_ms=1500):
    chime = AudioSegment.silent(duration=duration_ms)
    for i, freq in enumerate([1200, 1800, 2400, 3000, 3600]):
        tone = Sine(freq).to_audio_segment(duration=duration_ms).fade_in(10).fade_out(800) - (10 + i * 2)
        chime = chime.overlay(tone)
    return chime - 5


def generate_cello_drone(duration_ms=5000):
    drone = Sine(130).to_audio_segment(duration=duration_ms)
    for h in [2, 3, 4, 5]:
        drone = drone.overlay(Sine(130 * h).to_audio_segment(duration=duration_ms) - (6 * h))
    return low_pass_filter(drone.fade_in(1500).fade_out(1500), 2000) - 12


def apply_reverb_tail(audio, tail_duration_ms=4000):
    result = audio
    for i, delay in enumerate([100, 200, 350, 500, 700, 1000, 1500, 2000, 2500, 3000]):
        if delay < tail_duration_ms:
            echo = AudioSegment.silent(duration=delay) + audio
            echo = echo + (-6 * (i + 1))
            echo = echo[:len(audio) + delay]
            if len(echo) > len(result):
                result = result + AudioSegment.silent(duration=len(echo) - len(result))
            result = result.overlay(echo)
    return result + AudioSegment.silent(duration=tail_duration_ms - 3000)


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 70)
    print("GENERATING FINAL_ENHANCED_V4.MP3")
    print("With Module-Specific Voice Styles + Audio Surgery")
    print("=" * 70)

    # Print style summary
    print_style_summary()

    # Load script for reference
    with open(BASE_DIR / "Output" / "enhanced_script.json") as f:
        script = json.load(f)

    tts_dir = OUTPUT_DIR / "tts"
    bgm_dir = OUTPUT_DIR / "bgm"

    SENTENCE_PAUSE = 350
    CHUNK_PAUSE = 800
    MODULE_PAUSE = 1500

    # ==========================================================================
    # STEP 1: BUILD HOOK WITH STYLE
    # ==========================================================================
    print("\n" + "-" * 50)
    print("STEP 1: Building Hook (The Intriguer)")
    print("-" * 50)

    hook_files = sorted(tts_dir.glob("hook_sent_*.wav"))
    hook_voice = AudioSegment.empty()
    for i, f in enumerate(hook_files):
        sent = AudioSegment.from_file(str(f))
        hook_voice = hook_voice + sent
        if i < len(hook_files) - 1:
            hook_voice = hook_voice + AudioSegment.silent(duration=SENTENCE_PAUSE)

    print(f"  Raw hook duration: {len(hook_voice)/1000:.1f}s")

    # Apply hook style
    hook_styled = apply_voice_style(hook_voice, "hook")
    print(f"  Styled hook duration: {len(hook_styled)/1000:.1f}s")

    # ==========================================================================
    # STEP 2: BUILD MODULES WITH STYLES
    # ==========================================================================
    modules_styled = {}

    for module in script["modules"]:
        mid = module["id"]
        style_key = f"module_{mid}"
        style_name = VOICE_STYLES[style_key]["name"]

        print("\n" + "-" * 50)
        print(f"STEP 2.{mid}: Building Module {mid} ({style_name})")
        print("-" * 50)

        module_audio = AudioSegment.empty()
        chunks = module["chunks"]

        for cidx in range(len(chunks)):
            sent_files = sorted(tts_dir.glob(f"module_{mid}_chunk_{cidx+1}_sent_*.wav"))

            chunk_audio = AudioSegment.empty()
            for i, f in enumerate(sent_files):
                sent = AudioSegment.from_file(str(f))
                chunk_audio = chunk_audio + sent
                if i < len(sent_files) - 1:
                    chunk_audio = chunk_audio + AudioSegment.silent(duration=SENTENCE_PAUSE)

            module_audio = module_audio + chunk_audio
            if cidx < len(chunks) - 1:
                module_audio = module_audio + AudioSegment.silent(duration=CHUNK_PAUSE)

        print(f"  Raw module duration: {len(module_audio)/1000:.1f}s")

        # Apply module-specific style
        module_styled = apply_voice_style(module_audio, style_key)
        modules_styled[mid] = module_styled
        print(f"  Styled module duration: {len(module_styled)/1000:.1f}s")

    # ==========================================================================
    # STEP 3: ADD BGM TO EACH MODULE
    # ==========================================================================
    print("\n" + "-" * 50)
    print("STEP 3: Adding BGM")
    print("-" * 50)

    # Hook BGM
    bgm1 = AudioSegment.from_file(str(bgm_dir / "module_1_bgm.wav"))
    bgm1 = bgm1[500:]  # Trim noise
    bgm1 = bgm1 - 20
    if len(bgm1) < len(hook_styled):
        bgm1 = bgm1 * ((len(hook_styled) // len(bgm1)) + 1)
    bgm1 = bgm1[:len(hook_styled)].fade_in(2000).fade_out(2000)
    hook_mixed = hook_styled.overlay(bgm1)
    print(f"  Hook mixed with BGM")

    # Module BGMs
    modules_mixed = {}
    for mid, voice in modules_styled.items():
        bgm_path = bgm_dir / f"module_{mid}_bgm.wav"
        if bgm_path.exists():
            bgm = AudioSegment.from_file(str(bgm_path))
            bgm = bgm[500:]
            bgm = bgm - 18
            if len(bgm) < len(voice):
                bgm = bgm * ((len(voice) // len(bgm)) + 1)
            bgm = bgm[:len(voice)].fade_in(1500).fade_out(2000)
            modules_mixed[mid] = voice.overlay(bgm)
        else:
            modules_mixed[mid] = voice
        print(f"  Module {mid} mixed with BGM")

    # ==========================================================================
    # STEP 4: COMBINE ALL SEGMENTS
    # ==========================================================================
    print("\n" + "-" * 50)
    print("STEP 4: Combining All Segments")
    print("-" * 50)

    final_audio = hook_mixed + AudioSegment.silent(duration=MODULE_PAUSE)

    for mid in sorted(modules_mixed.keys()):
        final_audio = final_audio + modules_mixed[mid]
        if mid < max(modules_mixed.keys()):
            final_audio = final_audio + AudioSegment.silent(duration=MODULE_PAUSE)

    print(f"  Combined duration: {len(final_audio)/1000:.1f}s")

    # ==========================================================================
    # STEP 5: APPLY AUDIO SURGERY EFFECTS
    # ==========================================================================
    print("\n" + "-" * 50)
    print("STEP 5: Applying Audio Surgery Effects")
    print("-" * 50)

    offset = 0

    # Breath at start
    breath = generate_breath(300)
    final_audio = breath + final_audio
    offset += 300
    print("  [0:00] Added breath")

    # 1.5s pause at ~15s
    pos = 15000 + offset
    final_audio = final_audio[:pos] + AudioSegment.silent(duration=1500) + final_audio[pos:]
    offset += 1500
    print("  [0:15] Added 1.5s pause")

    # 2.0s pause at ~2:10
    pos = 130000 + offset
    final_audio = final_audio[:pos] + AudioSegment.silent(duration=2000) + final_audio[pos:]
    offset += 2000
    print("  [2:10] Added 2.0s rhetorical pause")

    # Volcanic effects at ~30s
    pos = 30000 + offset
    final_audio = final_audio.overlay(generate_sub_bass_boom(), position=pos)
    final_audio = final_audio.overlay(generate_geothermal_hiss(), position=pos + 500)
    print("  [0:30] Added volcanic effects")

    # Ice crack at ~45s
    final_audio = final_audio.overlay(generate_ice_crack(), position=45000 + offset)
    print("  [0:45] Added ice crack")

    # Vinyl crackle at ~1:20 (punk section - Module 3)
    pos = 80000 + offset
    final_audio = final_audio.overlay(generate_vinyl_crackle(), position=pos)
    final_audio = final_audio.overlay(generate_feedback_squeal().pan(-0.3), position=pos + 5000)
    print("  [1:20] Added vinyl crackle + feedback")

    # Cello drone at ~1:50
    final_audio = final_audio.overlay(generate_cello_drone(), position=110000 + offset)
    print("  [1:50] Added cello drone")

    # Electric zap + chime at ~2:30
    pos = 150000 + offset
    final_audio = final_audio.overlay(generate_electric_zap(), position=pos)
    final_audio = final_audio.overlay(generate_crystalline_chime(), position=pos + 500)
    print("  [2:30] Added zap + chime")

    # Era EQ: 1970s AM radio (0:45-1:30)
    start = 45000 + offset
    end = 90000 + offset
    before = final_audio[:start]
    section = final_audio[start:end]
    after = final_audio[end:]
    section = low_pass_filter(high_pass_filter(section, 200), 4000)
    final_audio = before + section + after
    print("  [0:45-1:30] Applied AM radio EQ")

    # Era EQ: 1990s Hi-Fi (6:00-7:30)
    start = 360000 + offset
    end = min(450000 + offset, len(final_audio))
    if start < len(final_audio):
        before = final_audio[:start]
        section = final_audio[start:end]
        after = final_audio[end:]
        bass = low_pass_filter(section, 100) + 2
        section = section.overlay(bass)
        final_audio = before + section + after
        print("  [6:00-7:30] Applied Hi-Fi EQ")

    # Mic drop ending: reverb tail
    final_start = len(final_audio) - 3000
    before = final_audio[:final_start]
    final_section = final_audio[final_start:]
    final_with_reverb = apply_reverb_tail(final_section, 4000)
    final_audio = before + final_with_reverb + AudioSegment.silent(duration=4000)
    print("  [END] Added reverb tail + 4s silence")

    # ==========================================================================
    # STEP 6: EXPORT
    # ==========================================================================
    print("\n" + "-" * 50)
    print("STEP 6: Exporting")
    print("-" * 50)

    final_audio = final_audio.normalize()
    output_path = OUTPUT_DIR / "final_enhanced_v4.mp3"
    final_audio.export(str(output_path), format="mp3", bitrate="192k")

    print(f"\n" + "=" * 70)
    print(f"SAVED: {output_path}")
    print(f"Duration: {len(final_audio)/1000:.1f}s ({len(final_audio)/60000:.1f} min)")
    print("=" * 70)

    # Print style breakdown
    print("\nStyle Breakdown:")
    print(f"  Hook: {VOICE_STYLES['hook']['name']} - {VOICE_STYLES['hook']['speed']}x speed")
    for mid in sorted(modules_mixed.keys()):
        style = VOICE_STYLES[f'module_{mid}']
        print(f"  Module {mid}: {style['name']} - {style['speed']}x speed, +{style['volume_boost_db']}dB")


if __name__ == "__main__":
    main()
