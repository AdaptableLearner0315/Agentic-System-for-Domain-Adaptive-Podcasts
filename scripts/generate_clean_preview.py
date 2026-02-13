"""
Generate clean audio previews for step-by-step review.

This script generates module previews with:
- 350ms pause between sentences ONLY
- Voice style applied per module
- BGM (trimmed 500ms, fade-in/fade-out)
- NO audio surgery effects (those will be added after flow is confirmed)

Usage:
    python generate_clean_preview.py --hook          # Generate hook preview
    python generate_clean_preview.py --module 1     # Generate module 1 preview
    python generate_clean_preview.py --module 2     # Generate module 2 preview
    python generate_clean_preview.py --module 3     # Generate module 3 preview
    python generate_clean_preview.py --module 4     # Generate module 4 preview
    python generate_clean_preview.py --all          # Generate all previews
"""

import argparse
import json
from pathlib import Path
from pydub import AudioSegment

import sys
sys.path.insert(0, str(Path(__file__).parent))
from utils.voice_styles import apply_voice_style, VOICE_STYLES

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "Output" / "audio"
TTS_DIR = OUTPUT_DIR / "tts"
BGM_DIR = OUTPUT_DIR / "bgm"
PREVIEW_DIR = OUTPUT_DIR / "previews"

# =============================================================================
# EMOTIONALLY CONNECTIVE PACING CONFIGURATION
# =============================================================================
# Each sentence has an emotional ROLE that determines its pause duration:
# - Scene Setting: Establishes context, allows visualization (800ms)
# - Anticipation: Short sentence before reveal, creates tension (1200ms)
# - Peak Reveal: High-impact content, maintain momentum (600ms)
# - Info Delivery: Dense facts, moderate processing time (800ms)
# - Pivot Point: "But..." narrative shift, maximum tension (1500ms)
# - Grand Finale: Epic scope, bridge to next section (2000ms)
# =============================================================================

HOOK_PAUSE_CONFIG = {
    1: {"role": "scene_setting", "pause_ms": 800, "description": "Picture this... visualization time"},
    2: {"role": "anticipation", "pause_ms": 1200, "description": "She sits... build tension before reveal"},
    3: {"role": "peak_reveal", "pause_ms": 600, "description": "Voice cuts through... maintain momentum"},
    4: {"role": "info_delivery", "pause_ms": 800, "description": "Performance recorded... processing time"},
    5: {"role": "pivot", "pause_ms": 1500, "description": "But this is just the beginning... TENSION PEAK"},
    6: {"role": "grand_finale", "pause_ms": 2000, "description": "From volcanic... epic scope, bridge to Module 1"},
}

# Default fallback for sentences without specific config
DEFAULT_SENTENCE_PAUSE_MS = 600

# =============================================================================
# MODULE 1: THE BIOGRAPHER - Warm, Nostalgic, Measured Pace
# =============================================================================
# Module 1 tells the origin story. "The Biographer" style is warm and deliberate.
# Overall pacing is SLOWER than hook - more time for listener to absorb details.
# Longer pauses after imagery-rich sentences, shorter for factual sequences.

MODULE_1_PAUSE_CONFIG = {
    # Chunk 1: wonder (tension_level 2) - Setting the scene
    "chunk_1": {
        1: {"role": "scene_setting", "pause_ms": 1000, "description": "Volcanic landscape imagery - let it paint"},
        2: {"role": "birth_info", "pause_ms": 800, "description": "Birth facts - moderate pause"},
        3: {"role": "family_detail", "pause_ms": 600, "description": "Parents info - quick transition"},
        4: {"role": "early_pivot", "pause_ms": 1200, "description": "Parents separated - emotional beat"},
    },
    # Chunk 2: curiosity (tension_level 3) - The commune environment
    "chunk_2": {
        1: {"role": "setting_establish", "pause_ms": 900, "description": "Artistic laboratory - evocative"},
        2: {"role": "descriptive", "pause_ms": 700, "description": "Creative energy - flowing"},
        3: {"role": "character_intro", "pause_ms": 700, "description": "Stepfather intro - brief"},
        4: {"role": "list_culmination", "pause_ms": 1100, "description": "Musical diversity - let it land"},
    },
    # Chunk 3: wonder (tension_level 3) - Musical training contrast
    "chunk_3": {
        1: {"role": "contrast_setup", "pause_ms": 900, "description": "Most children vs Björk contrast"},
        2: {"role": "key_reveal", "pause_ms": 1300, "description": "Teachers discovered wildness - KEY MOMENT"},
        3: {"role": "contrast_continue", "pause_ms": 1000, "description": "Hendrix vs Mozart - rich imagery"},
    },
    # Chunk 4: intrigue (tension_level 4) - Building to something unprecedented
    "chunk_4": {
        1: {"role": "powerful_imagery", "pause_ms": 1100, "description": "Northern lights - painterly moment"},
        2: {"role": "building", "pause_ms": 900, "description": "Folklore mixed with activism"},
        3: {"role": "module_finale", "pause_ms": 1800, "description": "Unprecedented - BRIDGE to Module 2"},
    },
}

# Pause between chunks within Module 1 (paragraph breaks)
MODULE_1_CHUNK_PAUSE_MS = 900

# =============================================================================
# MODULE 2: THE ANNOUNCER - Punchy, Triumphant, Medium-Fast
# =============================================================================
# Module 2 tells breakthrough achievements. "The Announcer" style is energetic.
# Overall pacing is FASTER - punchy delivery, quick transitions.
# Shorter pauses maintain momentum, emphasis on achievements.

MODULE_2_PAUSE_CONFIG = {
    # Chunk 1: tension → triumph (tension_level 4) - The decisive moment
    "chunk_1": {
        1: {"role": "tension_build", "pause_ms": 600, "description": "Decisive moment arrived - building"},
        2: {"role": "action_sequence", "pause_ms": 500, "description": "Recording sent - quick momentum"},
        3: {"role": "impact_landing", "pause_ms": 800, "description": "Captivated nation - let achievement land"},
    },
    # Chunk 2: triumph (tension_level 5) - Record deal PEAK
    "chunk_2": {
        1: {"role": "big_reveal", "pause_ms": 700, "description": "Record contract at 11 - BIG NEWS"},
        2: {"role": "detail_rapid", "pause_ms": 500, "description": "Album details - quick"},
        3: {"role": "character_moment", "pause_ms": 600, "description": "Artistic independence shown"},
        4: {"role": "triumph_peak", "pause_ms": 900, "description": "Beatles cover - stubborn independence"},
    },
    # Chunk 3: excitement (tension_level 4) - Rising star
    "chunk_3": {
        1: {"role": "achievement_stat", "pause_ms": 600, "description": "Sales numbers - factual punch"},
        2: {"role": "transition_hint", "pause_ms": 700, "description": "Restless adolescent - foreshadowing"},
        3: {"role": "module_bridge", "pause_ms": 1200, "description": "True voice beginning - BRIDGE to punk era"},
    },
}
MODULE_2_CHUNK_PAUSE_MS = 700

# =============================================================================
# MODULE 3: THE PUNK CHRONICLER - Raw, Urgent, Fast
# =============================================================================
# Module 3 covers punk rebellion. "The Punk Chronicler" style is electric.
# Overall pacing is FASTEST - urgent, rapid-fire energy.
# Minimal pauses with occasional dramatic beats for impact.

MODULE_3_PAUSE_CONFIG = {
    # Chunk 1: rebellion (tension_level 4) - Volcanic awakening
    "chunk_1": {
        1: {"role": "explosive_opening", "pause_ms": 500, "description": "Volcano metaphor - punchy"},
        2: {"role": "scene_rapid", "pause_ms": 400, "description": "Reykjavik pressure cooker - fast"},
        3: {"role": "context_quick", "pause_ms": 400, "description": "Punk necessity - flowing"},
        4: {"role": "howl_moment", "pause_ms": 700, "description": "Collective howl - let it echo"},
    },
    # Chunk 2: intensity (tension_level 5) - PEAK punk energy
    "chunk_2": {
        1: {"role": "quicksilver", "pause_ms": 400, "description": "Band succession - rapid"},
        2: {"role": "documentary_moment", "pause_ms": 500, "description": "Rock í Reykjavík - visual"},
        3: {"role": "feral_peak", "pause_ms": 800, "description": "Feral intensity - PEAK MOMENT pause"},
    },
    # Chunk 3: liberation (tension_level 4) - KUKL sorcery
    "chunk_3": {
        1: {"role": "sorcery_intro", "pause_ms": 500, "description": "KUKL sorcery - mystical"},
        2: {"role": "lightning_image", "pause_ms": 700, "description": "Lightning through storm - vivid"},
    },
    # Chunk 4: triumph (tension_level 3) - Personal revolution
    "chunk_4": {
        1: {"role": "life_change", "pause_ms": 600, "description": "Marriage and son - personal"},
        2: {"role": "band_birth", "pause_ms": 500, "description": "Sugarcubes emerge"},
        3: {"role": "barrier_break", "pause_ms": 1000, "description": "Invisible barrier - BRIDGE to global"},
    },
}
MODULE_3_CHUNK_PAUSE_MS = 600

# =============================================================================
# MODULE 4: THE SAGE - Reflective, Reverential, Slow
# =============================================================================
# Module 4 covers global success and legacy. "The Sage" style is wise.
# Overall pacing is SLOWEST - deliberate, reflective, conclusive.
# Longer pauses for gravitas, maximum pause at finale.

MODULE_4_PAUSE_CONFIG = {
    # Chunk 1: triumph (tension_level 5) - Global breakthrough PEAK
    "chunk_1": {
        1: {"role": "impossible_achieved", "pause_ms": 900, "description": "Million copies - let magnitude land"},
        2: {"role": "cultural_moment", "pause_ms": 800, "description": "John Peel, Top of Pops - iconic"},
        3: {"role": "arrival_statement", "pause_ms": 1000, "description": "SNL appearance - they've arrived"},
    },
    # Chunk 2: tension (tension_level 4) - Complications
    "chunk_2": {
        1: {"role": "shadow_intro", "pause_ms": 800, "description": "Success brought complications - shift"},
        2: {"role": "strain_detail", "pause_ms": 700, "description": "Communal spirit strained"},
        3: {"role": "friction_build", "pause_ms": 700, "description": "Creative differences grew"},
        4: {"role": "breaking_point", "pause_ms": 900, "description": "Friction unbearable - tension peak"},
        5: {"role": "looking_elsewhere", "pause_ms": 1100, "description": "Already looking elsewhere - pivot"},
    },
    # Chunk 3: liberation (tension_level 3) - Solo emergence
    "chunk_3": {
        1: {"role": "crossroads", "pause_ms": 900, "description": "Creative crossroads - reflective"},
        2: {"role": "emergence", "pause_ms": 800, "description": "Singular voice emerged"},
        3: {"role": "debut_declaration", "pause_ms": 900, "description": "Declaration of independence"},
        4: {"role": "shattered_expectations", "pause_ms": 1100, "description": "Shattered expectations - powerful"},
    },
    # Chunk 4: mastery (tension_level 4) - LEGACY FINALE
    "chunk_4": {
        1: {"role": "three_decades", "pause_ms": 1000, "description": "Three decades of work - scope"},
        2: {"role": "hallmarks", "pause_ms": 900, "description": "Reinvention, collaboration, courage"},
        3: {"role": "authenticity", "pause_ms": 1100, "description": "Swan dresses to authenticity"},
        4: {"role": "grand_finale", "pause_ms": 2500, "description": "True musical revolutionary - PODCAST FINALE"},
    },
}
MODULE_4_CHUNK_PAUSE_MS = 1000


def generate_hook_preview():
    """Generate hook preview with emotionally connective variable pacing."""
    print("=" * 60)
    print("GENERATING HOOK PREVIEW WITH EMOTIONALLY CONNECTIVE PACING")
    print("=" * 60)

    # Ensure preview directory exists
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)

    # Step 1: Load and concatenate hook sentences with VARIABLE pauses
    print("\nStep 1: Loading hook sentences with variable pacing...")
    print("  Pacing strategy: Variable pauses based on emotional role")
    hook_files = sorted(TTS_DIR.glob("hook_sent_*.wav"))

    if not hook_files:
        print("ERROR: No hook sentence files found!")
        return None

    print(f"  Found {len(hook_files)} sentence files\n")

    hook_voice = AudioSegment.empty()
    total_pause_time = 0

    for i, f in enumerate(hook_files):
        sent_num = i + 1
        sent = AudioSegment.from_file(str(f))
        hook_voice = hook_voice + sent

        # Get pause configuration for this sentence
        pause_config = HOOK_PAUSE_CONFIG.get(sent_num, {"role": "default", "pause_ms": DEFAULT_SENTENCE_PAUSE_MS})
        pause_ms = pause_config["pause_ms"]
        role = pause_config["role"]
        description = pause_config.get("description", "")

        # Add pause after each sentence EXCEPT the last one
        if i < len(hook_files) - 1:
            hook_voice = hook_voice + AudioSegment.silent(duration=pause_ms)
            total_pause_time += pause_ms

        # Print detailed info about each sentence
        print(f"    [{sent_num}/{len(hook_files)}] {f.name}")
        print(f"           Duration: {len(sent)/1000:.2f}s | Pause: {pause_ms}ms ({role})")
        if description:
            print(f"           Reason: {description}")

    print(f"\n  Raw hook duration: {len(hook_voice)/1000:.2f}s")
    print(f"  Total pause time: {total_pause_time/1000:.2f}s across {len(hook_files)-1} pauses")
    print(f"  Average pause: {total_pause_time/(len(hook_files)-1):.0f}ms (vs. fixed 350ms before)")

    # Step 2: Apply voice style (The Intriguer)
    print("\nStep 2: Applying voice style 'The Intriguer'...")
    style = VOICE_STYLES["hook"]
    print(f"  Style: {style['name']}")
    print(f"  Speed: {style['speed']}x")
    print(f"  EQ: {style['eq']}")
    print(f"  Volume boost: +{style['volume_boost_db']}dB")

    hook_styled = apply_voice_style(hook_voice, "hook")
    print(f"  Styled duration: {len(hook_styled)/1000:.2f}s")

    # Step 3: Add BGM
    print("\nStep 3: Adding BGM...")
    bgm_path = BGM_DIR / "module_1_bgm.wav"  # Hook uses module 1 BGM

    if bgm_path.exists():
        bgm = AudioSegment.from_file(str(bgm_path))

        # Trim 500ms from start to remove noise
        bgm = bgm[500:]
        print(f"  Trimmed 500ms noise from BGM start")

        # Lower volume (reduced 30% for voice prominence)
        bgm = bgm - 24
        print(f"  BGM volume: -24dB")

        # Loop BGM if needed
        if len(bgm) < len(hook_styled):
            loops_needed = (len(hook_styled) // len(bgm)) + 1
            bgm = bgm * loops_needed
            print(f"  Looped BGM {loops_needed}x to cover voice")

        # Trim to match voice length and add fades
        bgm = bgm[:len(hook_styled)]
        bgm = bgm.fade_in(2000).fade_out(2000)
        print(f"  Added 2s fade-in and 2s fade-out")

        # Mix voice with BGM
        hook_mixed = hook_styled.overlay(bgm)
        print(f"  Mixed voice with BGM")
    else:
        print(f"  WARNING: BGM not found at {bgm_path}, using voice only")
        hook_mixed = hook_styled

    # Step 4: Export
    print("\nStep 4: Exporting...")
    hook_mixed = hook_mixed.normalize()

    output_path = PREVIEW_DIR / "hook_preview_paced.mp3"
    hook_mixed.export(str(output_path), format="mp3", bitrate="192k")

    print(f"\n" + "=" * 60)
    print(f"SAVED: {output_path}")
    print(f"Duration: {len(hook_mixed)/1000:.2f}s")
    print("=" * 60)

    # Print pacing summary
    print("\nPacing Summary:")
    print("  Variable pauses create emotional rhythm:")
    for sent_num, config in HOOK_PAUSE_CONFIG.items():
        if sent_num <= len(hook_files):
            print(f"    Sentence {sent_num}: {config['pause_ms']}ms ({config['role']})")

    return output_path


def get_module_pause_config(module_id: int):
    """Get pause configuration for a specific module."""
    configs = {
        1: (MODULE_1_PAUSE_CONFIG, MODULE_1_CHUNK_PAUSE_MS),
        2: (MODULE_2_PAUSE_CONFIG, MODULE_2_CHUNK_PAUSE_MS),
        3: (MODULE_3_PAUSE_CONFIG, MODULE_3_CHUNK_PAUSE_MS),
        4: (MODULE_4_PAUSE_CONFIG, MODULE_4_CHUNK_PAUSE_MS),
    }
    return configs.get(module_id, (None, 800))


def generate_module_preview(module_id: int):
    """Generate module preview with emotionally connective pacing."""
    print("=" * 60)
    print(f"GENERATING MODULE {module_id} PREVIEW WITH EMOTIONALLY CONNECTIVE PACING")
    print("=" * 60)

    # Ensure preview directory exists
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)

    # Load script for chunk info
    with open(BASE_DIR / "Output" / "enhanced_script.json") as f:
        script = json.load(f)

    # Find the module
    module = None
    for m in script["modules"]:
        if m["id"] == module_id:
            module = m
            break

    if not module:
        print(f"ERROR: Module {module_id} not found in script!")
        return None

    style_key = f"module_{module_id}"
    style = VOICE_STYLES[style_key]

    print(f"\nModule: {module['title']}")
    print(f"Style: {style['name']} - {style['description']}")

    # Get pause configuration for this module
    pause_config, chunk_pause_ms = get_module_pause_config(module_id)
    has_custom_config = pause_config is not None

    if has_custom_config:
        print(f"Pacing: Custom emotionally connective configuration")
    else:
        print(f"Pacing: Default ({DEFAULT_SENTENCE_PAUSE_MS}ms between sentences)")

    # Step 1: Load and concatenate sentences with VARIABLE pauses
    print("\nStep 1: Loading sentences with variable pacing...")

    module_voice = AudioSegment.empty()
    chunk_count = len(module["chunks"])
    total_pause_time = 0
    total_sentences = 0

    for chunk_idx in range(chunk_count):
        chunk_key = f"chunk_{chunk_idx + 1}"
        chunk_config = pause_config.get(chunk_key, {}) if has_custom_config else {}
        chunk_emotion = module["chunks"][chunk_idx].get("emotion", "neutral")
        chunk_tension = module["chunks"][chunk_idx].get("tension_level", 2)

        sent_files = sorted(TTS_DIR.glob(f"module_{module_id}_chunk_{chunk_idx+1}_sent_*.wav"))

        if not sent_files:
            print(f"  WARNING: No sentence files for chunk {chunk_idx + 1}")
            continue

        print(f"\n  Chunk {chunk_idx + 1}/{chunk_count}: {len(sent_files)} sentences")
        print(f"  Emotion: {chunk_emotion} | Tension: {chunk_tension}")

        for i, f in enumerate(sent_files):
            sent_num = i + 1
            total_sentences += 1
            sent = AudioSegment.from_file(str(f))
            module_voice = module_voice + sent

            # Get pause for this sentence
            sent_config = chunk_config.get(sent_num, {"role": "default", "pause_ms": DEFAULT_SENTENCE_PAUSE_MS})
            pause_ms = sent_config["pause_ms"]
            role = sent_config["role"]
            description = sent_config.get("description", "")

            # Add pause after each sentence EXCEPT the last one in the LAST chunk
            is_last_sentence_of_chunk = (i == len(sent_files) - 1)
            is_last_chunk = (chunk_idx == chunk_count - 1)

            if is_last_sentence_of_chunk and not is_last_chunk:
                # End of chunk but not end of module - use chunk pause
                module_voice = module_voice + AudioSegment.silent(duration=chunk_pause_ms)
                total_pause_time += chunk_pause_ms
                print(f"    [{sent_num}/{len(sent_files)}] {f.name}")
                print(f"           Duration: {len(sent)/1000:.2f}s | Pause: {chunk_pause_ms}ms (CHUNK BREAK)")
            elif is_last_sentence_of_chunk and is_last_chunk:
                # Last sentence of module - no pause after
                print(f"    [{sent_num}/{len(sent_files)}] {f.name}")
                print(f"           Duration: {len(sent)/1000:.2f}s | Pause: [END OF MODULE]")
            else:
                # Normal sentence pause
                module_voice = module_voice + AudioSegment.silent(duration=pause_ms)
                total_pause_time += pause_ms
                print(f"    [{sent_num}/{len(sent_files)}] {f.name}")
                print(f"           Duration: {len(sent)/1000:.2f}s | Pause: {pause_ms}ms ({role})")
                if description:
                    print(f"           Reason: {description}")

    print(f"\n  Raw module duration: {len(module_voice)/1000:.2f}s")
    print(f"  Total pause time: {total_pause_time/1000:.2f}s")
    if total_sentences > 1:
        print(f"  Average pause: {total_pause_time/(total_sentences-1):.0f}ms")

    # Step 2: Apply voice style
    print(f"\nStep 2: Applying voice style '{style['name']}'...")
    print(f"  Speed: {style['speed']}x")
    print(f"  EQ: {style['eq']}")
    print(f"  Volume boost: +{style['volume_boost_db']}dB")
    print(f"  Compression: {style['compression']}")
    print(f"  Reverb: {'Yes' if style['reverb'] else 'No'}")

    module_styled = apply_voice_style(module_voice, style_key)
    print(f"  Styled duration: {len(module_styled)/1000:.2f}s")

    # Step 3: Add BGM
    print("\nStep 3: Adding BGM...")
    bgm_path = BGM_DIR / f"module_{module_id}_bgm.wav"

    if bgm_path.exists():
        bgm = AudioSegment.from_file(str(bgm_path))

        # Trim 500ms from start to remove noise
        bgm = bgm[500:]
        print(f"  Trimmed 500ms noise from BGM start")

        # Lower volume (reduced 30% for voice prominence)
        bgm = bgm - 22
        print(f"  BGM volume: -22dB")

        # Loop BGM if needed
        if len(bgm) < len(module_styled):
            loops_needed = (len(module_styled) // len(bgm)) + 1
            bgm = bgm * loops_needed
            print(f"  Looped BGM {loops_needed}x to cover voice")

        # Trim to match voice length and add fades
        bgm = bgm[:len(module_styled)]
        bgm = bgm.fade_in(1500).fade_out(2000)
        print(f"  Added 1.5s fade-in and 2s fade-out")

        # Mix voice with BGM
        module_mixed = module_styled.overlay(bgm)
        print(f"  Mixed voice with BGM")
    else:
        print(f"  WARNING: BGM not found at {bgm_path}, using voice only")
        module_mixed = module_styled

    # Step 4: Export
    print("\nStep 4: Exporting...")
    module_mixed = module_mixed.normalize()

    output_path = PREVIEW_DIR / f"module_{module_id}_preview_paced.mp3"
    module_mixed.export(str(output_path), format="mp3", bitrate="192k")

    print(f"\n" + "=" * 60)
    print(f"SAVED: {output_path}")
    print(f"Duration: {len(module_mixed)/1000:.2f}s")
    print("=" * 60)

    # Print pacing summary if custom config exists
    if has_custom_config:
        print("\nPacing Summary:")
        for chunk_key, chunk_cfg in pause_config.items():
            print(f"  {chunk_key}:")
            for sent_num, sent_cfg in chunk_cfg.items():
                print(f"    Sentence {sent_num}: {sent_cfg['pause_ms']}ms ({sent_cfg['role']})")

    return output_path


def main():
    parser = argparse.ArgumentParser(description="Generate clean audio previews")
    parser.add_argument("--hook", action="store_true", help="Generate hook preview")
    parser.add_argument("--module", type=int, choices=[1, 2, 3, 4], help="Generate specific module preview")
    parser.add_argument("--all", action="store_true", help="Generate all previews")

    args = parser.parse_args()

    if args.hook:
        generate_hook_preview()
    elif args.module:
        generate_module_preview(args.module)
    elif args.all:
        print("\n" + "=" * 70)
        print("GENERATING ALL CLEAN PREVIEWS")
        print("=" * 70)

        generate_hook_preview()
        print("\n")

        for mid in [1, 2, 3, 4]:
            generate_module_preview(mid)
            print("\n")

        print("\n" + "=" * 70)
        print("ALL PREVIEWS GENERATED")
        print(f"Location: {PREVIEW_DIR}")
        print("=" * 70)
    else:
        # Default to hook if no args
        print("No arguments provided. Generating hook preview...")
        generate_hook_preview()


if __name__ == "__main__":
    main()
