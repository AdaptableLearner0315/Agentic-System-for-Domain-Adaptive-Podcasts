"""
BGM Reconstruction Script - Simple Ambient Audio Layer

This script replaces ONLY the background music with simple ambient/minimal BGM.
- Keeps TTS, pacing, voice styles exactly the same
- Generates subtle ambient BGM that stays unobtrusive
- Voice narration remains the star
- Re-mixes audio with new BGM
- Updates videos with new audio

Usage:
    python reconstruct_bgm.py --generate-bgm    # Generate new BGM files only
    python reconstruct_bgm.py --remix           # Remix audio with new BGM
    python reconstruct_bgm.py --update-video    # Update videos with new audio
    python reconstruct_bgm.py --all             # Run full pipeline
"""

import argparse
import os
import subprocess
from pathlib import Path
from dotenv import load_dotenv

import fal_client
import requests
from pydub import AudioSegment

import sys
sys.path.insert(0, str(Path(__file__).parent))
from utils.voice_styles import apply_voice_style, VOICE_STYLES

load_dotenv()

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "Output" / "audio"
TTS_DIR = OUTPUT_DIR / "tts"
BGM_V2_DIR = OUTPUT_DIR / "bgm_v2"
PREVIEW_V2_DIR = OUTPUT_DIR / "previews_v2"
PREVIEW_VOICE_ONLY_DIR = OUTPUT_DIR / "previews_voice_only"
VISUALS_DIR = BASE_DIR / "Output" / "Visuals Included"

# =============================================================================
# SIMPLE AMBIENT BGM PROMPTS
# =============================================================================
# Subtle ambient music that stays unobtrusive - voice remains the star

BGM_PROMPTS = {
    "hook": {
        "name": "Ambient Opening",
        "prompt": """Soft ambient pad, gentle atmospheric texture, minimal and unobtrusive,
warm subtle background, very quiet and supportive, documentary underscore,
simple sustained tones, no melody, just gentle atmosphere""",
        "duration": 47,
        "style": "Simple Ambient"
    },
    "module_1": {
        "name": "Ambient Module 1",
        "prompt": """Gentle ambient drone, soft warm pad, minimal texture,
quiet atmospheric background, unobtrusive and supportive,
simple sustained tones, peaceful and subtle""",
        "duration": 47,
        "style": "Simple Ambient"
    },
    "module_2": {
        "name": "Ambient Module 2",
        "prompt": """Soft ambient texture, gentle warm atmosphere, minimal background,
quiet supportive pad, unobtrusive documentary underscore,
simple and subtle, no distracting elements""",
        "duration": 47,
        "style": "Simple Ambient"
    },
    "module_3": {
        "name": "Ambient Module 3",
        "prompt": """Gentle atmospheric pad, soft ambient texture, minimal and warm,
quiet background support, unobtrusive presence,
simple sustained atmosphere, subtle and supportive""",
        "duration": 47,
        "style": "Simple Ambient"
    },
    "module_4": {
        "name": "Ambient Module 4",
        "prompt": """Soft warm ambient drone, gentle atmospheric texture, minimal background,
quiet and unobtrusive, supportive documentary underscore,
simple sustained tones, peaceful resolution feeling""",
        "duration": 47,
        "style": "Simple Ambient"
    }
}

# =============================================================================
# SIMPLIFIED PACING CONFIGURATION
# =============================================================================
# Uniform pauses for comfortable listening pace:
# - 600ms between sentences (breathing room)
# - 1200ms between major sections (hook → module transitions)

SENTENCE_PAUSE_MS = 600      # Pause after each sentence
MODULE_TRANSITION_MS = 1200  # Pause between hook/modules


def generate_bgm_files():
    """Generate all emotion-coherent BGM files using Fal AI."""
    print("\n" + "=" * 70)
    print("GENERATING EMOTION-COHERENT BGM FILES")
    print("=" * 70)

    BGM_V2_DIR.mkdir(parents=True, exist_ok=True)

    generated_files = []

    for key, config in BGM_PROMPTS.items():
        print(f"\n{'─' * 60}")
        print(f"Generating: {config['name']} ({key})")
        print(f"Style: {config['style']}")
        print(f"Duration: {config['duration']}s")
        print(f"{'─' * 60}")

        output_path = BGM_V2_DIR / f"{key}_bgm.wav"

        # Clean up the prompt (remove newlines, extra spaces)
        prompt = " ".join(config["prompt"].split())
        print(f"Prompt: {prompt[:100]}...")

        try:
            print("  Calling Fal AI stable-audio...")
            result = fal_client.subscribe(
                "fal-ai/stable-audio",
                arguments={
                    "prompt": prompt,
                    "seconds_total": config["duration"],
                    "steps": 100
                },
                with_logs=False
            )

            # Download the generated audio
            audio_url = result.get("audio_file", {}).get("url")
            if audio_url:
                print(f"  Downloading from: {audio_url[:60]}...")
                response = requests.get(audio_url)
                with open(output_path, "wb") as f:
                    f.write(response.content)
                print(f"  Saved: {output_path}")
                generated_files.append({
                    "key": key,
                    "name": config["name"],
                    "path": str(output_path)
                })
            else:
                print(f"  ERROR: No audio URL in response")

        except Exception as e:
            print(f"  ERROR: {e}")

    print("\n" + "=" * 70)
    print(f"GENERATED {len(generated_files)} BGM FILES")
    print("=" * 70)

    for f in generated_files:
        print(f"  {f['key']}: {f['name']}")

    return generated_files




def remix_hook_with_new_bgm(voice_only: bool = False):
    """Remix hook with new emotion-coherent BGM or voice-only."""
    print("\n" + "=" * 60)
    if voice_only:
        print("GENERATING HOOK - VOICE ONLY (NO BGM)")
    else:
        print("REMIXING HOOK WITH NEW BGM")
    print("=" * 60)

    output_dir = PREVIEW_VOICE_ONLY_DIR if voice_only else PREVIEW_V2_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load hook TTS sentences
    hook_files = sorted(TTS_DIR.glob("hook_sent_*.wav"))
    if not hook_files:
        print("ERROR: No hook sentence files found!")
        return None

    print(f"Found {len(hook_files)} sentence files")
    print(f"Using {SENTENCE_PAUSE_MS}ms pause between sentences")

    # Concatenate with uniform 600ms pauses between sentences
    hook_voice = AudioSegment.empty()
    total_pause_time = 0

    for i, f in enumerate(hook_files):
        sent_num = i + 1
        sent = AudioSegment.from_file(str(f))
        hook_voice = hook_voice + sent

        # Add 600ms pause after each sentence except the last
        if i < len(hook_files) - 1:
            hook_voice = hook_voice + AudioSegment.silent(duration=SENTENCE_PAUSE_MS)
            total_pause_time += SENTENCE_PAUSE_MS

        print(f"  [{sent_num}] {f.name} | Pause: {SENTENCE_PAUSE_MS}ms")

    print(f"\nRaw voice duration: {len(hook_voice)/1000:.2f}s")
    print(f"Total pause time: {total_pause_time/1000:.2f}s")

    # Apply voice style
    print("\nApplying voice style 'The Intriguer'...")
    hook_styled = apply_voice_style(hook_voice, "hook")
    print(f"Styled duration: {len(hook_styled)/1000:.2f}s")

    # Add BGM (skip if voice_only mode)
    if voice_only:
        print("\nVOICE ONLY MODE - Skipping BGM")
        hook_mixed = hook_styled
    else:
        bgm_path = BGM_V2_DIR / "hook_bgm.wav"
        if not bgm_path.exists():
            print(f"WARNING: New BGM not found at {bgm_path}")
            print("Using old BGM as fallback...")
            bgm_path = OUTPUT_DIR / "bgm" / "module_1_bgm.wav"

        if bgm_path.exists():
            bgm = AudioSegment.from_file(str(bgm_path))

            # Trim 500ms from start to remove noise
            bgm = bgm[500:]
            print(f"Trimmed 500ms noise from BGM start")

            # Lower volume (raised ~3dB for more presence while keeping voice primary)
            bgm = bgm - 17
            print(f"BGM volume: -17dB")

            # Loop if needed
            if len(bgm) < len(hook_styled):
                loops_needed = (len(hook_styled) // len(bgm)) + 1
                bgm = bgm * loops_needed

            # Trim and fade
            bgm = bgm[:len(hook_styled)]
            bgm = bgm.fade_in(2000).fade_out(2000)

            # Mix
            hook_mixed = hook_styled.overlay(bgm)
            print("Mixed voice with new BGM")
        else:
            print("WARNING: No BGM available, using voice only")
            hook_mixed = hook_styled

    # Add 1200ms transition pause at end (for transition to Module 1)
    hook_mixed = hook_mixed + AudioSegment.silent(duration=MODULE_TRANSITION_MS)
    print(f"Added {MODULE_TRANSITION_MS}ms transition pause at end")

    # Export
    hook_mixed = hook_mixed.normalize()
    filename = "hook_preview_voice_only.mp3" if voice_only else "hook_preview_v2.mp3"
    output_path = output_dir / filename
    hook_mixed.export(str(output_path), format="mp3", bitrate="192k")

    print(f"\nSaved: {output_path}")
    print(f"Duration: {len(hook_mixed)/1000:.2f}s")

    return str(output_path)


def remix_module_with_new_bgm(module_id: int, voice_only: bool = False):
    """Remix a module with new emotion-coherent BGM or voice-only."""
    print(f"\n{'=' * 60}")
    if voice_only:
        print(f"GENERATING MODULE {module_id} - VOICE ONLY (NO BGM)")
    else:
        print(f"REMIXING MODULE {module_id} WITH NEW BGM")
    print("=" * 60)

    output_dir = PREVIEW_VOICE_ONLY_DIR if voice_only else PREVIEW_V2_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load script to get chunk info
    import json
    with open(BASE_DIR / "Output" / "enhanced_script.json") as f:
        script = json.load(f)

    # Find module
    module = None
    for m in script["modules"]:
        if m["id"] == module_id:
            module = m
            break

    if not module:
        print(f"ERROR: Module {module_id} not found!")
        return None

    style_key = f"module_{module_id}"
    style = VOICE_STYLES[style_key]

    print(f"Module: {module['title']}")
    print(f"Style: {style['name']} - {style['description']}")
    print(f"Using {SENTENCE_PAUSE_MS}ms pause between sentences")

    # Load and concatenate sentences with uniform 600ms pauses
    module_voice = AudioSegment.empty()
    chunk_count = len(module["chunks"])
    total_pause_time = 0
    total_sentences = 0

    for chunk_idx in range(chunk_count):
        sent_files = sorted(TTS_DIR.glob(f"module_{module_id}_chunk_{chunk_idx+1}_sent_*.wav"))

        if not sent_files:
            print(f"WARNING: No sentence files for chunk {chunk_idx + 1}")
            continue

        print(f"\n  Chunk {chunk_idx + 1}/{chunk_count}: {len(sent_files)} sentences")

        for i, f in enumerate(sent_files):
            total_sentences += 1
            sent = AudioSegment.from_file(str(f))
            module_voice = module_voice + sent

            is_last_sentence_of_module = (chunk_idx == chunk_count - 1) and (i == len(sent_files) - 1)

            # Add 600ms pause after each sentence except the very last one in the module
            if not is_last_sentence_of_module:
                module_voice = module_voice + AudioSegment.silent(duration=SENTENCE_PAUSE_MS)
                total_pause_time += SENTENCE_PAUSE_MS

            print(f"    [{i+1}] {f.name}")

    print(f"\nRaw voice duration: {len(module_voice)/1000:.2f}s")
    print(f"Total sentences: {total_sentences}")
    print(f"Total pause time: {total_pause_time/1000:.2f}s")

    # Apply voice style
    print(f"\nApplying voice style '{style['name']}'...")
    module_styled = apply_voice_style(module_voice, style_key)
    print(f"Styled duration: {len(module_styled)/1000:.2f}s")

    # Add BGM (skip if voice_only mode)
    if voice_only:
        print("\nVOICE ONLY MODE - Skipping BGM")
        module_mixed = module_styled
    else:
        bgm_path = BGM_V2_DIR / f"module_{module_id}_bgm.wav"
        if not bgm_path.exists():
            print(f"WARNING: New BGM not found at {bgm_path}")
            print("Using old BGM as fallback...")
            bgm_path = OUTPUT_DIR / "bgm" / f"module_{module_id}_bgm.wav"

        if bgm_path.exists():
            bgm = AudioSegment.from_file(str(bgm_path))

            # Trim 500ms from start
            bgm = bgm[500:]

            # Lower volume (raised ~3dB for more presence while keeping voice primary)
            bgm = bgm - 15
            print(f"BGM volume: -15dB")

            # Loop if needed
            if len(bgm) < len(module_styled):
                loops_needed = (len(module_styled) // len(bgm)) + 1
                bgm = bgm * loops_needed

            # Trim and fade
            bgm = bgm[:len(module_styled)]
            bgm = bgm.fade_in(1500).fade_out(2000)

            # Mix
            module_mixed = module_styled.overlay(bgm)
            print("Mixed voice with new BGM")
        else:
            print("WARNING: No BGM available")
            module_mixed = module_styled

    # Add 1200ms transition pause at end (except for Module 4 which is last)
    if module_id < 4:
        module_mixed = module_mixed + AudioSegment.silent(duration=MODULE_TRANSITION_MS)
        print(f"Added {MODULE_TRANSITION_MS}ms transition pause at end")

    # Export
    module_mixed = module_mixed.normalize()
    filename = f"module_{module_id}_preview_voice_only.mp3" if voice_only else f"module_{module_id}_preview_v2.mp3"
    output_path = output_dir / filename
    module_mixed.export(str(output_path), format="mp3", bitrate="192k")

    print(f"\nSaved: {output_path}")
    print(f"Duration: {len(module_mixed)/1000:.2f}s")

    return str(output_path)


def remix_all_audio(voice_only: bool = False):
    """Remix all audio sections with new BGM or voice-only."""
    print("\n" + "=" * 70)
    if voice_only:
        print("GENERATING ALL AUDIO - VOICE ONLY (NO BGM)")
    else:
        print("REMIXING ALL AUDIO WITH NEW BGM")
    print("=" * 70)

    results = {}

    # Remix hook
    results["hook"] = remix_hook_with_new_bgm(voice_only=voice_only)

    # Remix all modules
    for module_id in [1, 2, 3, 4]:
        results[f"module_{module_id}"] = remix_module_with_new_bgm(module_id, voice_only=voice_only)

    print("\n" + "=" * 70)
    if voice_only:
        print("VOICE ONLY GENERATION COMPLETE")
    else:
        print("REMIX COMPLETE")
    print("=" * 70)

    for key, path in results.items():
        if path:
            audio = AudioSegment.from_file(path)
            print(f"  {key}: {len(audio)/1000:.2f}s")

    return results


def get_audio_duration(audio_path: str) -> float:
    """Get duration of audio file in seconds."""
    result = subprocess.run([
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        audio_path
    ], capture_output=True, text=True)
    return float(result.stdout.strip())


def replace_audio_in_video(video_path: str, audio_path: str, output_path: str):
    """Replace audio track in a video file."""
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-i", audio_path,
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "192k",
        "-map", "0:v:0",
        "-map", "1:a:0",
        output_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  FFmpeg error: {result.stderr}")
    return output_path


def update_videos_with_new_audio(voice_only: bool = False):
    """Update all videos with new audio (BGM or voice-only)."""
    print("\n" + "=" * 70)
    if voice_only:
        print("UPDATING VIDEOS WITH VOICE-ONLY AUDIO")
    else:
        print("UPDATING VIDEOS WITH NEW AUDIO")
    print("=" * 70)

    # Create output directory
    if voice_only:
        video_output_dir = VISUALS_DIR / "voice_only"
    else:
        video_output_dir = VISUALS_DIR / "v2"
    video_output_dir.mkdir(parents=True, exist_ok=True)

    # Select audio source directory
    audio_source_dir = PREVIEW_VOICE_ONLY_DIR if voice_only else PREVIEW_V2_DIR
    audio_suffix = "_voice_only.mp3" if voice_only else "_v2.mp3"

    sections = ["hook", "module_1", "module_2", "module_3", "module_4"]
    updated_videos = []

    for section in sections:
        print(f"\n{'─' * 50}")
        print(f"Updating: {section}")
        print("─" * 50)

        # Find original video
        if section == "hook":
            video_path = VISUALS_DIR / "hook_video.mp4"
        else:
            video_path = VISUALS_DIR / f"{section}_video.mp4"

        # Find audio
        audio_filename = f"{section}_preview{audio_suffix}"
        audio_path = audio_source_dir / audio_filename

        if not video_path.exists():
            print(f"  WARNING: Video not found: {video_path}")
            continue

        if not audio_path.exists():
            print(f"  WARNING: Audio not found: {audio_path}")
            continue

        # Output path
        video_suffix = "_voice_only.mp4" if voice_only else "_v2.mp4"
        output_path = video_output_dir / f"{section}_video{video_suffix}"

        print(f"  Video: {video_path.name}")
        print(f"  Audio: {audio_path.name}")
        print(f"  Output: {output_path.name}")

        # Replace audio
        replace_audio_in_video(str(video_path), str(audio_path), str(output_path))

        if output_path.exists():
            duration = get_audio_duration(str(output_path))
            print(f"  Duration: {duration:.2f}s")
            updated_videos.append(str(output_path))
        else:
            print(f"  ERROR: Failed to create video")

    # Concatenate all videos into final
    if len(updated_videos) == 5:
        print(f"\n{'─' * 50}")
        print("Creating final combined video...")
        print("─" * 50)

        final_name = "final_podcast_video_voice_only.mp4" if voice_only else "final_podcast_video_v2.mp4"
        concat_videos(updated_videos, str(video_output_dir / final_name))

    print("\n" + "=" * 70)
    print("VIDEO UPDATE COMPLETE")
    print("=" * 70)

    return updated_videos


def concat_videos(video_paths: list, output_path: str):
    """Concatenate multiple videos into one."""
    # Create concat file
    concat_file = Path(output_path).parent / "concat_list.txt"
    with open(concat_file, "w") as f:
        for path in video_paths:
            f.write(f"file '{path}'\n")

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_file),
        "-c", "copy",
        output_path
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    # Clean up
    concat_file.unlink()

    if result.returncode == 0 and Path(output_path).exists():
        duration = get_audio_duration(output_path)
        print(f"  Final video: {output_path}")
        print(f"  Total duration: {duration:.2f}s ({duration/60:.1f} min)")
    else:
        print(f"  ERROR: {result.stderr}")

    return output_path


def main():
    parser = argparse.ArgumentParser(description="BGM Reconstruction - Emotion-Coherent Audio Layer")
    parser.add_argument("--generate-bgm", action="store_true", help="Generate new BGM files only")
    parser.add_argument("--remix", action="store_true", help="Remix audio with new BGM")
    parser.add_argument("--update-video", action="store_true", help="Update videos with new audio")
    parser.add_argument("--all", action="store_true", help="Run full pipeline")
    parser.add_argument("--voice-only", action="store_true", help="Generate voice-only audio without BGM")

    args = parser.parse_args()

    if args.all:
        if args.voice_only:
            print("\n" + "=" * 70)
            print("VOICE ONLY PIPELINE (NO BGM)")
            print("=" * 70)

            # Step 1: Remix audio (voice only)
            remixed = remix_all_audio(voice_only=True)

            # Step 2: Update videos
            updated = update_videos_with_new_audio(voice_only=True)

            print("\n" + "=" * 70)
            print("VOICE ONLY PIPELINE COMPLETE")
            print("=" * 70)
            print(f"  Remixed audio: {len([r for r in remixed.values() if r])}")
            print(f"  Updated videos: {len(updated)}")
        else:
            print("\n" + "=" * 70)
            print("BGM RECONSTRUCTION - FULL PIPELINE")
            print("=" * 70)

            # Step 1: Generate BGM
            generated = generate_bgm_files()

            # Step 2: Remix audio
            remixed = remix_all_audio()

            # Step 3: Update videos
            updated = update_videos_with_new_audio()

            print("\n" + "=" * 70)
            print("PIPELINE COMPLETE")
            print("=" * 70)
            print(f"  BGM files: {len(generated)}")
            print(f"  Remixed audio: {len([r for r in remixed.values() if r])}")
            print(f"  Updated videos: {len(updated)}")

    elif args.generate_bgm:
        generate_bgm_files()
    elif args.remix:
        remix_all_audio(voice_only=args.voice_only)
    elif args.update_video:
        update_videos_with_new_audio(voice_only=args.voice_only)
    else:
        print("No action specified. Use --help for options.")
        print("\nQuick start:")
        print("  python reconstruct_bgm.py --all              # Full pipeline with BGM")
        print("  python reconstruct_bgm.py --all --voice-only # Voice only (no BGM)")


if __name__ == "__main__":
    main()
