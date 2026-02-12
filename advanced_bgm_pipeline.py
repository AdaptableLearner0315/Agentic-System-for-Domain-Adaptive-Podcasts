"""
Advanced BGM Pipeline - One-Shot Audio Generation

This script generates seamless, narratively consistent background music using:
- Audio-to-audio conditioning (each track feeds into the next)
- Fixed seed for timbral consistency
- VAD-based ducking for vocal clarity
- Inflection point overlays for dramatic peaks

Usage:
    python advanced_bgm_pipeline.py --generate-base    # Generate base BGM tracks
    python advanced_bgm_pipeline.py --generate-swells  # Generate inflection swells
    python advanced_bgm_pipeline.py --stitch           # Stitch tracks with crossfades
    python advanced_bgm_pipeline.py --mix-final        # Apply ducking and overlays
    python advanced_bgm_pipeline.py --update-video     # Update video with new audio
    python advanced_bgm_pipeline.py --all              # Full pipeline
"""

import argparse
import base64
import io
import os
import subprocess
from pathlib import Path
from typing import Optional

import fal_client
import numpy as np
import requests
from dotenv import load_dotenv
from pydub import AudioSegment

load_dotenv()

# =============================================================================
# DIRECTORY CONFIGURATION
# =============================================================================

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "Output" / "audio"
BGM_ADV_DIR = OUTPUT_DIR / "bgm_advanced"
VOICE_ONLY_DIR = OUTPUT_DIR / "previews_voice_only"
FINAL_DIR = OUTPUT_DIR / "final_advanced"
VISUALS_DIR = BASE_DIR / "Output" / "Visuals Included"

# =============================================================================
# GLOBAL AUDIO STANDARDS
# =============================================================================

NARRATOR_LEVEL_DB = 0       # Normalized voice level
BASE_BGM_LEVEL_DB = -18     # Standard bed level
INFLECTION_LEVEL_DB = -6    # High intensity moments
CROSSFADE_MS = 5000         # 5 seconds between modules
SEED = 42                   # Fixed for consistency
STEPS = 100                 # Maximum quality
MAX_DURATION = 47           # Fal AI max duration per generation

# =============================================================================
# MODULE SPECIFICATIONS
# =============================================================================

MODULE_SPECS = {
    "hook": {
        "name": "The Hook",
        "role": "Cold Open",
        "duration": 55,  # 45s + 10s buffer
        "content_duration": 45,
        "prompt": "Icelandic ambient soundscape, glacial wind textures, distant geothermal rumbling, minimal glass chimes, sense of mystery and anticipation, cold but magical, high fidelity, 70 BPM, no percussion, reverb-heavy flute in distance.",
        "input_audio": None,
        "input_strength": None,
        "output": "audio_hook_out.wav"
    },
    "module_1": {
        "name": "The Origins",
        "role": "Bohemian Childhood",
        "duration": 138,  # 128s + 10s buffer
        "content_duration": 128,
        "prompt": "Warm acoustic folk fusion, flute and gentle acoustic guitar strumming, experimental textures blending with organic sounds, curious and whimsical, sense of wonder, soft rhythmic pulse starting to form, creative and bohemian, 85 BPM, major key.",
        "input_audio": "audio_hook_out.wav",
        "input_strength": 0.35,
        "output": "audio_mod1_out.wav"
    },
    "module_2": {
        "name": "The Breakthrough",
        "role": "Prodigy's Rise",
        "duration": 91,  # 81s + 10s buffer
        "content_duration": 81,
        "prompt": "Building orchestral pop, piano arpeggios, confident rhythm, hopeful and bright, feeling of growing up, movement towards success, crisp production, 100 BPM, strings section swelling.",
        "input_audio": "audio_mod1_out.wav",
        "input_strength": 0.30,
        "output": "audio_mod2_out.wav"
    },
    "module_3": {
        "name": "The Punk Revolution",
        "role": "Rebellion",
        "duration": 116,  # 106s + 10s buffer
        "content_duration": 106,
        "prompt": "Post-punk instrumental, distorted bass guitar, driving tribal drums, raw and gritty, experimental rock, moody and rebellious, high energy, feral texture, 1980s underground club vibe, 120 BPM, heavy percussion.",
        "input_audio": "audio_mod2_out.wav",
        "input_strength": 0.20,
        "output": "audio_mod3_out.wav"
    },
    "module_4": {
        "name": "Global Mastery",
        "role": "Evolution",
        "duration": 158,  # 148s + 10s fade out
        "content_duration": 148,
        "prompt": "Avant-garde pop, electronic house beat, 90s dance music influence, sophisticated synthesizer, celebratory and majestic, complex rhythm, artistic freedom, Debut album style, confident and polished, 128 BPM, wide stereo field.",
        "input_audio": "audio_mod3_out.wav",
        "input_strength": 0.25,
        "output": "audio_mod4_out.wav"
    }
}

# =============================================================================
# INFLECTION POINT SPECIFICATIONS
# =============================================================================

INFLECTION_SPECS = {
    "record_deal": {
        "name": "The Record Deal",
        "target_time_ms": 195000,  # 3:15
        "duration": 15,
        "mix_level_db": -6,
        "fade_in_ms": 2000,
        "prompt": "Triumphant cinematic crescendo, swelling strings, bright synthesizer pads, major key, euphoric release, victory moment, intense and uplifting.",
        "output": "swell_record_deal.wav"
    },
    "feral_intensity": {
        "name": "Feral Intensity",
        "target_time_ms": 285000,  # 4:45
        "duration": 20,
        "mix_level_db": -8,
        "fade_in_ms": 0,
        "prompt": "Chaotic punk breakdown, heavy drum fills, distorted guitar feedback, aggressive texture, high intensity, raw power, fast tempo.",
        "output": "swell_feral_intensity.wav"
    },
    "global_explosion": {
        "name": "Global Explosion",
        "target_time_ms": 360000,  # 6:00
        "duration": 25,
        "mix_level_db": -6,
        "fade_in_ms": 0,
        "prompt": "Massive stadium anthem, celebratory brass section, thumping kick drum, wide stereo field, global success, top of the world feeling, triumphant finale.",
        "output": "swell_global_explosion.wav"
    }
}


def extract_last_n_seconds(audio_path: Path, n_seconds: int = 10) -> AudioSegment:
    """Extract the last N seconds of an audio file for conditioning."""
    audio = AudioSegment.from_file(str(audio_path))
    return audio[-n_seconds * 1000:]


def audio_to_base64(audio: AudioSegment) -> str:
    """Convert AudioSegment to base64 string for Fal AI."""
    buffer = io.BytesIO()
    audio.export(buffer, format="wav")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def generate_bgm_segment(
    prompt: str,
    duration: int,
    conditioning_audio: Optional[AudioSegment] = None,
    conditioning_strength: float = 0.3
) -> Optional[AudioSegment]:
    """Generate a single BGM segment using Fal AI stable-audio."""

    # Clamp duration to max
    actual_duration = min(duration, MAX_DURATION)

    arguments = {
        "prompt": prompt,
        "seconds_total": actual_duration,
        "steps": STEPS
    }

    # Add conditioning if provided
    if conditioning_audio is not None:
        audio_b64 = audio_to_base64(conditioning_audio)
        arguments["audio_input"] = f"data:audio/wav;base64,{audio_b64}"
        arguments["input_strength"] = conditioning_strength

    try:
        print(f"    Generating {actual_duration}s segment...")
        result = fal_client.subscribe(
            "fal-ai/stable-audio",
            arguments=arguments,
            with_logs=False
        )

        audio_url = result.get("audio_file", {}).get("url")
        if audio_url:
            response = requests.get(audio_url)
            return AudioSegment.from_file(io.BytesIO(response.content), format="wav")
        else:
            print("    ERROR: No audio URL in response")
            return None

    except Exception as e:
        print(f"    ERROR: {e}")
        return None


def generate_long_bgm(
    prompt: str,
    total_duration: int,
    initial_conditioning: Optional[AudioSegment] = None,
    conditioning_strength: float = 0.3
) -> Optional[AudioSegment]:
    """Generate BGM longer than 47s by chaining segments."""

    segments = []
    remaining = total_duration
    current_conditioning = initial_conditioning

    segment_num = 1
    while remaining > 0:
        segment_duration = min(remaining, MAX_DURATION)
        print(f"    Segment {segment_num}: {segment_duration}s (remaining: {remaining}s)")

        segment = generate_bgm_segment(
            prompt=prompt,
            duration=segment_duration,
            conditioning_audio=current_conditioning,
            conditioning_strength=conditioning_strength
        )

        if segment is None:
            print(f"    Failed to generate segment {segment_num}")
            return None

        segments.append(segment)

        # Use last 10s of this segment as conditioning for next
        current_conditioning = segment[-10000:] if len(segment) > 10000 else segment
        remaining -= segment_duration
        segment_num += 1

    # Concatenate all segments with short crossfade
    if len(segments) == 1:
        return segments[0]

    print(f"    Concatenating {len(segments)} segments...")
    result = segments[0]
    for seg in segments[1:]:
        # 2s crossfade between segments
        result = result.append(seg, crossfade=2000)

    return result


def generate_base_tracks():
    """Generate all base BGM tracks with audio-to-audio conditioning."""
    print("\n" + "=" * 70)
    print("GENERATING BASE BGM TRACKS (Audio-to-Audio Conditioning)")
    print("=" * 70)

    BGM_ADV_DIR.mkdir(parents=True, exist_ok=True)

    generated = []
    prev_audio = None

    for key, spec in MODULE_SPECS.items():
        print(f"\n{'─' * 60}")
        print(f"Generating: {spec['name']} ({spec['role']})")
        print(f"Duration: {spec['duration']}s")
        if spec['input_audio']:
            print(f"Conditioning: {spec['input_audio']} (strength: {spec['input_strength']})")
        print(f"{'─' * 60}")

        # Get conditioning audio
        conditioning = None
        if spec['input_audio'] and prev_audio is not None:
            conditioning = extract_last_n_seconds(
                BGM_ADV_DIR / prev_audio,
                n_seconds=10
            )
            print(f"  Using last 10s of {prev_audio} for conditioning")

        # Generate the track
        audio = generate_long_bgm(
            prompt=spec['prompt'],
            total_duration=spec['duration'],
            initial_conditioning=conditioning,
            conditioning_strength=spec.get('input_strength', 0.3)
        )

        if audio:
            output_path = BGM_ADV_DIR / spec['output']
            audio.export(str(output_path), format="wav")
            print(f"  Saved: {output_path}")
            print(f"  Duration: {len(audio)/1000:.2f}s")
            generated.append(key)
            prev_audio = spec['output']
        else:
            print(f"  FAILED to generate {key}")

    print(f"\n{'=' * 70}")
    print(f"Generated {len(generated)}/{len(MODULE_SPECS)} base tracks")
    print("=" * 70)

    return generated


def generate_inflection_swells():
    """Generate inflection point swell audio files."""
    print("\n" + "=" * 70)
    print("GENERATING INFLECTION SWELLS")
    print("=" * 70)

    BGM_ADV_DIR.mkdir(parents=True, exist_ok=True)
    generated = []

    for key, spec in INFLECTION_SPECS.items():
        print(f"\n{'─' * 60}")
        print(f"Generating: {spec['name']}")
        print(f"Duration: {spec['duration']}s")
        print(f"Target: {spec['target_time_ms']//1000//60}:{spec['target_time_ms']//1000%60:02d}")
        print(f"{'─' * 60}")

        audio = generate_bgm_segment(
            prompt=spec['prompt'],
            duration=spec['duration']
        )

        if audio:
            output_path = BGM_ADV_DIR / spec['output']
            audio.export(str(output_path), format="wav")
            print(f"  Saved: {output_path}")
            generated.append(key)
        else:
            print(f"  FAILED to generate {key}")

    print(f"\n{'=' * 70}")
    print(f"Generated {len(generated)}/{len(INFLECTION_SPECS)} swells")
    print("=" * 70)

    return generated


def stitch_base_tracks():
    """Stitch all base tracks together with 5s crossfades."""
    print("\n" + "=" * 70)
    print("STITCHING BASE TRACKS WITH CROSSFADES")
    print("=" * 70)

    FINAL_DIR.mkdir(parents=True, exist_ok=True)

    # Load all tracks
    tracks = []
    track_order = ["hook", "module_1", "module_2", "module_3", "module_4"]

    for key in track_order:
        spec = MODULE_SPECS[key]
        path = BGM_ADV_DIR / spec['output']

        if not path.exists():
            print(f"  ERROR: Missing {path}")
            return None

        audio = AudioSegment.from_file(str(path))
        # Trim to content duration (remove buffer)
        content_ms = spec['content_duration'] * 1000
        audio = audio[:content_ms]
        tracks.append((key, audio))
        print(f"  Loaded {key}: {len(audio)/1000:.2f}s")

    # Stitch with crossfades
    print(f"\nStitching with {CROSSFADE_MS}ms crossfades...")
    result = tracks[0][1]

    for i in range(1, len(tracks)):
        key, track = tracks[i]
        result = result.append(track, crossfade=CROSSFADE_MS)
        print(f"  + {key} → total: {len(result)/1000:.2f}s")

    # Save stitched track
    output_path = FINAL_DIR / "bgm_stitched.wav"
    result.export(str(output_path), format="wav")

    print(f"\nSaved: {output_path}")
    print(f"Total duration: {len(result)/1000:.2f}s ({len(result)/1000/60:.1f} min)")

    return str(output_path)


def detect_voice_activity(voice_audio: AudioSegment, frame_ms: int = 100) -> list:
    """
    Simple energy-based voice activity detection.
    Returns list of (start_ms, is_voice_active) tuples.
    """
    samples = np.array(voice_audio.get_array_of_samples())
    frame_samples = int(voice_audio.frame_rate * frame_ms / 1000)

    # Calculate RMS energy per frame
    frames = []
    for i in range(0, len(samples), frame_samples):
        frame = samples[i:i + frame_samples]
        if len(frame) > 0:
            rms = np.sqrt(np.mean(frame.astype(float) ** 2))
            frames.append(rms)

    # Threshold at 20% of max RMS
    if not frames:
        return []

    threshold = max(frames) * 0.15

    vad_result = []
    for i, rms in enumerate(frames):
        start_ms = i * frame_ms
        is_active = rms > threshold
        vad_result.append((start_ms, is_active))

    return vad_result


def apply_ducking(bgm: AudioSegment, vad_result: list, frame_ms: int = 100) -> AudioSegment:
    """
    Apply ducking to BGM based on voice activity.
    - Voice active: -18 dB
    - Voice silent: -12 dB
    """
    print("  Applying VAD-based ducking...")

    # Start at base level
    ducked = AudioSegment.silent(duration=0)

    for i, (start_ms, is_active) in enumerate(vad_result):
        end_ms = start_ms + frame_ms
        if end_ms > len(bgm):
            end_ms = len(bgm)

        frame = bgm[start_ms:end_ms]

        if is_active:
            # Voice active: lower BGM
            frame = frame + BASE_BGM_LEVEL_DB
        else:
            # Voice silent: raise BGM slightly
            frame = frame - 12  # -12 dB during silence

        ducked = ducked + frame

    return ducked


def overlay_inflection_swells(audio: AudioSegment) -> AudioSegment:
    """Overlay inflection swells at specified times."""
    print("  Overlaying inflection swells...")

    result = audio

    for key, spec in INFLECTION_SPECS.items():
        swell_path = BGM_ADV_DIR / spec['output']

        if not swell_path.exists():
            print(f"    WARNING: Missing swell {swell_path}")
            continue

        swell = AudioSegment.from_file(str(swell_path))

        # Apply level adjustment
        swell = swell + spec['mix_level_db']

        # Apply fade-in if specified
        if spec['fade_in_ms'] > 0:
            swell = swell.fade_in(spec['fade_in_ms'])

        # Overlay at target time
        target_ms = spec['target_time_ms']
        print(f"    {spec['name']} at {target_ms//1000//60}:{target_ms//1000%60:02d} ({spec['mix_level_db']}dB)")

        result = result.overlay(swell, position=target_ms)

    return result


def mix_final_audio():
    """Mix final audio with ducking and inflection overlays."""
    print("\n" + "=" * 70)
    print("MIXING FINAL AUDIO")
    print("=" * 70)

    FINAL_DIR.mkdir(parents=True, exist_ok=True)

    # Load stitched BGM
    bgm_path = FINAL_DIR / "bgm_stitched.wav"
    if not bgm_path.exists():
        print("ERROR: Stitched BGM not found. Run --stitch first.")
        return None

    bgm = AudioSegment.from_file(str(bgm_path))
    print(f"  Loaded BGM: {len(bgm)/1000:.2f}s")

    # Load voice-only audio (concatenate all modules)
    print("\n  Loading voice-only audio...")
    voice_files = [
        VOICE_ONLY_DIR / "hook_preview_voice_only.mp3",
        VOICE_ONLY_DIR / "module_1_preview_voice_only.mp3",
        VOICE_ONLY_DIR / "module_2_preview_voice_only.mp3",
        VOICE_ONLY_DIR / "module_3_preview_voice_only.mp3",
        VOICE_ONLY_DIR / "module_4_preview_voice_only.mp3",
    ]

    voice = AudioSegment.empty()
    for vf in voice_files:
        if vf.exists():
            v = AudioSegment.from_file(str(vf))
            voice = voice + v
            print(f"    + {vf.name}: {len(v)/1000:.2f}s")
        else:
            print(f"    WARNING: Missing {vf}")

    print(f"  Total voice: {len(voice)/1000:.2f}s")

    # Ensure BGM matches voice length
    if len(bgm) < len(voice):
        # Loop BGM
        loops = (len(voice) // len(bgm)) + 1
        bgm = bgm * loops
    bgm = bgm[:len(voice)]

    # VAD detection
    print("\n  Running voice activity detection...")
    vad_result = detect_voice_activity(voice)
    print(f"    Detected {len(vad_result)} frames")

    # Apply ducking
    bgm_ducked = apply_ducking(bgm, vad_result)

    # Add inflection overlays (BEFORE mixing with voice)
    bgm_with_swells = overlay_inflection_swells(bgm_ducked)

    # Mix voice + BGM
    print("\n  Mixing voice + BGM...")

    # Normalize voice
    voice = voice.normalize()

    # Mix
    final_mix = voice.overlay(bgm_with_swells)

    # Final normalization
    final_mix = final_mix.normalize()

    # Export
    output_path = FINAL_DIR / "final_podcast_advanced.mp3"
    final_mix.export(str(output_path), format="mp3", bitrate="192k")

    print(f"\n  Saved: {output_path}")
    print(f"  Duration: {len(final_mix)/1000:.2f}s ({len(final_mix)/1000/60:.1f} min)")

    return str(output_path)


def get_audio_duration(audio_path: str) -> float:
    """Get duration of audio file in seconds."""
    result = subprocess.run([
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        audio_path
    ], capture_output=True, text=True)
    return float(result.stdout.strip())


def update_video():
    """Update video with new advanced audio."""
    print("\n" + "=" * 70)
    print("UPDATING VIDEO WITH ADVANCED AUDIO")
    print("=" * 70)

    # Create output directory
    video_output_dir = VISUALS_DIR / "advanced"
    video_output_dir.mkdir(parents=True, exist_ok=True)

    # Find source video
    voice_only_video = VISUALS_DIR / "voice_only" / "final_podcast_video_voice_only.mp4"
    if not voice_only_video.exists():
        # Fall back to original
        voice_only_video = VISUALS_DIR / "final_podcast_video.mp4"

    if not voice_only_video.exists():
        print(f"ERROR: No source video found")
        return None

    # Find new audio
    new_audio = FINAL_DIR / "final_podcast_advanced.mp3"
    if not new_audio.exists():
        print(f"ERROR: Advanced audio not found. Run --mix-final first.")
        return None

    output_path = video_output_dir / "final_podcast_video_advanced.mp4"

    print(f"  Source video: {voice_only_video}")
    print(f"  New audio: {new_audio}")
    print(f"  Output: {output_path}")

    # Replace audio
    cmd = [
        "ffmpeg", "-y",
        "-i", str(voice_only_video),
        "-i", str(new_audio),
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "192k",
        "-map", "0:v:0",
        "-map", "1:a:0",
        str(output_path)
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0 and output_path.exists():
        duration = get_audio_duration(str(output_path))
        print(f"\n  Success!")
        print(f"  Duration: {duration:.2f}s ({duration/60:.1f} min)")
        return str(output_path)
    else:
        print(f"  ERROR: {result.stderr}")
        return None


def main():
    parser = argparse.ArgumentParser(description="Advanced BGM Pipeline")
    parser.add_argument("--generate-base", action="store_true", help="Generate base BGM tracks")
    parser.add_argument("--generate-swells", action="store_true", help="Generate inflection swells")
    parser.add_argument("--stitch", action="store_true", help="Stitch tracks with crossfades")
    parser.add_argument("--mix-final", action="store_true", help="Mix final audio with ducking")
    parser.add_argument("--update-video", action="store_true", help="Update video with new audio")
    parser.add_argument("--all", action="store_true", help="Run full pipeline")

    args = parser.parse_args()

    if args.all:
        print("\n" + "=" * 70)
        print("ADVANCED BGM PIPELINE - FULL RUN")
        print("=" * 70)

        # Step 1: Generate base tracks
        generate_base_tracks()

        # Step 2: Generate swells
        generate_inflection_swells()

        # Step 3: Stitch
        stitch_base_tracks()

        # Step 4: Mix final
        mix_final_audio()

        # Step 5: Update video
        update_video()

        print("\n" + "=" * 70)
        print("PIPELINE COMPLETE")
        print("=" * 70)
        print(f"\nFinal video: {VISUALS_DIR / 'advanced' / 'final_podcast_video_advanced.mp4'}")

    elif args.generate_base:
        generate_base_tracks()
    elif args.generate_swells:
        generate_inflection_swells()
    elif args.stitch:
        stitch_base_tracks()
    elif args.mix_final:
        mix_final_audio()
    elif args.update_video:
        update_video()
    else:
        print("No action specified. Use --help for options.")
        print("\nQuick start:")
        print("  python advanced_bgm_pipeline.py --all  # Full pipeline")


if __name__ == "__main__":
    main()
