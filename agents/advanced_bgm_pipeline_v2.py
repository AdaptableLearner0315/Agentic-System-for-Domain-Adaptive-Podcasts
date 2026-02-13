"""
Advanced BGM Pipeline V2 - 9-Segment Daisy-Chain

This script implements the improved BGM generation with:
- 9 linked segments (each feeds into the next)
- Smoother transitions with pre-build and aftermath sections
- Softer punk (driving/rhythmic instead of distorted/feral)
- 5-second buffer on each segment for crossfade stitching

Usage:
    python advanced_bgm_pipeline_v2.py --generate    # Generate all 9 segments
    python advanced_bgm_pipeline_v2.py --stitch      # Stitch with crossfades
    python advanced_bgm_pipeline_v2.py --mix         # Mix with voice + finalize
    python advanced_bgm_pipeline_v2.py --all         # Full pipeline
"""

import argparse
import base64
import io
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
BGM_V2_DIR = OUTPUT_DIR / "bgm_v2_daisy"
VOICE_ONLY_DIR = OUTPUT_DIR / "previews_voice_only"
FINAL_DIR = OUTPUT_DIR / "final_v2"
VISUALS_DIR = BASE_DIR / "Output" / "Visuals Included"

# =============================================================================
# GLOBAL SETTINGS
# =============================================================================

MAX_DURATION = 47  # Fal AI max per generation
CROSSFADE_MS = 5000  # 5 second crossfade (using the buffer)
STEPS = 100

# =============================================================================
# 9-SEGMENT DAISY-CHAIN SPECIFICATION
# =============================================================================

SEGMENTS = [
    # Phase 1: Origins (Atmosphere & Wonder)
    {
        "id": 1,
        "name": "The Hook",
        "phase": "Origins",
        "time": "0:00 - 0:45",
        "goal": "Establish the cold, mysterious Icelandic landscape",
        "duration": 50,
        "content_duration": 45,
        "input_audio": None,
        "input_strength": None,
        "prompt": "Cinematic ambient soundscape, Iceland atmosphere, glacial wind textures, distant geothermal rumbling, minimal glass chimes, sense of mystery, cold but magical, high fidelity, 70 BPM, reverb-heavy flute in distance."
    },
    {
        "id": 2,
        "name": "The Bohemian Commune",
        "phase": "Origins",
        "time": "0:45 - 2:53",
        "goal": "Warmth, creativity, folk influences",
        "duration": 133,
        "content_duration": 128,
        "input_audio": 1,  # Last 10s of segment 1
        "input_strength": 0.35,
        "prompt": "Warm acoustic folk fusion, gentle flute and acoustic guitar strumming, experimental textures blending with organic sounds, curious and whimsical, soft rhythmic pulse, creative and bohemian, 85 BPM, major key, sense of childhood wonder."
    },

    # Phase 2: The Breakthrough (Smooth Swell)
    {
        "id": 3,
        "name": "The Pre-Build",
        "phase": "Breakthrough",
        "time": "2:53 - 3:15",
        "goal": "Transition from folk to orchestral",
        "duration": 27,
        "content_duration": 22,
        "input_audio": 2,
        "input_strength": 0.35,
        "prompt": "Building orchestral pop, piano arpeggios starting gently, confident rhythm emerging, hopeful and bright, feeling of anticipation, crisp production, 95 BPM."
    },
    {
        "id": 4,
        "name": "Inflection 1: The Triumph",
        "phase": "Breakthrough",
        "time": "3:15 - 3:45",
        "goal": "THE SWELL - Record deal triumph",
        "duration": 35,
        "content_duration": 30,
        "input_audio": 3,
        "input_strength": 0.4,  # Higher strength for energy shift
        "prompt": "Triumphant orchestral swell, sweeping strings section, bright synthesizer pads, major key, euphoric release, victory moment, rich and full sound, uplifting and cinematic, 100 BPM."
    },
    {
        "id": 5,
        "name": "The Aftermath",
        "phase": "Breakthrough",
        "time": "3:45 - 4:14",
        "goal": "Ease down from triumph, prep for genre shift",
        "duration": 34,
        "content_duration": 29,
        "input_audio": 4,
        "input_strength": 0.35,
        "prompt": "Orchestral pop settling down, steady rhythmic pulse, remaining hopeful but less intense, transition to a slightly edgier texture, 100 BPM."
    },

    # Phase 3: The Punk Revolution (Softened & Energetic)
    {
        "id": 6,
        "name": "Punk Intro",
        "phase": "Punk Revolution",
        "time": "4:14 - 4:40",
        "goal": "Introduce energy change without jarring",
        "duration": 31,
        "content_duration": 26,
        "input_audio": 5,
        "input_strength": 0.3,
        "prompt": "Driving rhythmic bassline, fast-paced drums, new-wave energy, clean electric guitar strumming (no distortion), high energy pulse, 120 BPM, mysterious and cool."
    },
    {
        "id": 7,
        "name": "Inflection 2: The Energy Peak",
        "phase": "Punk Revolution",
        "time": "4:40 - 5:15",
        "goal": "High energy club/dance style (NOT noise)",
        "duration": 40,
        "content_duration": 35,
        "input_audio": 6,
        "input_strength": 0.3,
        "prompt": "High energy alternative rock, driving drum beat, catchy bass groove, upbeat and rebellious but polished, The Sugarcubes style, dynamic and fast, 125 BPM, no harsh noise, smooth but powerful."
    },
    {
        "id": 8,
        "name": "Punk Fade Out",
        "phase": "Punk Revolution",
        "time": "5:15 - 6:00",
        "goal": "Maintain rhythm, lower complexity, transition",
        "duration": 50,
        "content_duration": 45,
        "input_audio": 7,
        "input_strength": 0.35,
        "prompt": "Rhythmic drum groove continues, bassline becomes simpler, atmospheric synthesizers entering, cooling down the energy, transition towards electronic pop, 120 BPM."
    },

    # Phase 4: Global Mastery (The Anthem)
    {
        "id": 9,
        "name": "Inflection 3: The Global Anthem",
        "phase": "Global Mastery",
        "time": "6:00 - 8:28",
        "goal": "Final evolution - starts big, sustains, euphoric finale",
        "duration": 153,
        "content_duration": 148,
        "input_audio": 8,
        "input_strength": 0.3,
        "prompt": "Anthemic electronic pop, 90s house beat, sophisticated synthesizer, celebratory and majestic, wide stadium sound, confident and polished, artistic freedom, 128 BPM, euphoric finale."
    }
]


def audio_to_base64(audio: AudioSegment) -> str:
    """Convert AudioSegment to base64 for Fal AI."""
    buffer = io.BytesIO()
    audio.export(buffer, format="wav")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def generate_segment(
    prompt: str,
    duration: int,
    conditioning_audio: Optional[AudioSegment] = None,
    conditioning_strength: float = 0.35
) -> Optional[AudioSegment]:
    """Generate a single segment using Fal AI."""

    actual_duration = min(duration, MAX_DURATION)

    arguments = {
        "prompt": prompt,
        "seconds_total": actual_duration,
        "steps": STEPS
    }

    if conditioning_audio is not None:
        audio_b64 = audio_to_base64(conditioning_audio)
        arguments["audio_input"] = f"data:audio/wav;base64,{audio_b64}"
        arguments["input_strength"] = conditioning_strength

    try:
        print(f"      Generating {actual_duration}s...")
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
            print("      ERROR: No audio URL")
            return None
    except Exception as e:
        print(f"      ERROR: {e}")
        return None


def generate_long_segment(
    prompt: str,
    total_duration: int,
    initial_conditioning: Optional[AudioSegment] = None,
    conditioning_strength: float = 0.35
) -> Optional[AudioSegment]:
    """Generate segment longer than 47s by chaining."""

    segments = []
    remaining = total_duration
    current_conditioning = initial_conditioning
    part = 1

    while remaining > 0:
        seg_duration = min(remaining, MAX_DURATION)
        print(f"      Part {part}: {seg_duration}s (remaining: {remaining}s)")

        seg = generate_segment(
            prompt=prompt,
            duration=seg_duration,
            conditioning_audio=current_conditioning,
            conditioning_strength=conditioning_strength
        )

        if seg is None:
            return None

        segments.append(seg)
        current_conditioning = seg[-10000:] if len(seg) > 10000 else seg
        remaining -= seg_duration
        part += 1

    if len(segments) == 1:
        return segments[0]

    print(f"      Concatenating {len(segments)} parts...")
    result = segments[0]
    for s in segments[1:]:
        result = result.append(s, crossfade=2000)

    return result


def generate_all_segments():
    """Generate all 9 segments with daisy-chain conditioning."""
    print("\n" + "=" * 70)
    print("GENERATING 9-SEGMENT DAISY-CHAIN BGM")
    print("=" * 70)

    BGM_V2_DIR.mkdir(parents=True, exist_ok=True)

    generated_segments = {}

    for seg in SEGMENTS:
        print(f"\n{'─' * 60}")
        print(f"SEGMENT {seg['id']}: {seg['name']}")
        print(f"Phase: {seg['phase']} | Time: {seg['time']}")
        print(f"Goal: {seg['goal']}")
        print(f"Duration: {seg['duration']}s (content: {seg['content_duration']}s)")
        if seg['input_audio']:
            print(f"Conditioning: Segment {seg['input_audio']} (strength: {seg['input_strength']})")
        print(f"{'─' * 60}")

        # Get conditioning audio from previous segment
        conditioning = None
        if seg['input_audio'] and seg['input_audio'] in generated_segments:
            prev_audio = generated_segments[seg['input_audio']]
            conditioning = prev_audio[-10000:]  # Last 10 seconds
            print(f"    Using last 10s of segment {seg['input_audio']}")

        # Generate
        audio = generate_long_segment(
            prompt=seg['prompt'],
            total_duration=seg['duration'],
            initial_conditioning=conditioning,
            conditioning_strength=seg.get('input_strength', 0.35)
        )

        if audio:
            output_path = BGM_V2_DIR / f"segment_{seg['id']:02d}_{seg['name'].lower().replace(' ', '_').replace(':', '')}.wav"
            audio.export(str(output_path), format="wav")
            generated_segments[seg['id']] = audio
            print(f"    ✓ Saved: {output_path.name}")
            print(f"    Duration: {len(audio)/1000:.2f}s")
        else:
            print(f"    ✗ FAILED to generate segment {seg['id']}")

    print(f"\n{'=' * 70}")
    print(f"Generated {len(generated_segments)}/9 segments")
    print("=" * 70)

    return generated_segments


def stitch_segments():
    """Stitch all segments with 5s crossfades."""
    print("\n" + "=" * 70)
    print("STITCHING SEGMENTS WITH 5s CROSSFADES")
    print("=" * 70)

    FINAL_DIR.mkdir(parents=True, exist_ok=True)

    # Load all segments
    tracks = []
    for seg in SEGMENTS:
        pattern = f"segment_{seg['id']:02d}_*.wav"
        matches = list(BGM_V2_DIR.glob(pattern))

        if not matches:
            print(f"  ERROR: Missing segment {seg['id']}")
            return None

        audio = AudioSegment.from_file(str(matches[0]))
        # Trim to content duration (remove the 5s buffer, keep it for crossfade)
        content_ms = seg['content_duration'] * 1000
        # Keep a bit extra for crossfade
        audio = audio[:content_ms + CROSSFADE_MS]
        tracks.append((seg['id'], seg['name'], audio))
        print(f"  Loaded segment {seg['id']}: {seg['name']} ({len(audio)/1000:.2f}s)")

    # Stitch with crossfades
    print(f"\n  Stitching with {CROSSFADE_MS}ms crossfades...")
    result = tracks[0][2]

    for i in range(1, len(tracks)):
        seg_id, name, track = tracks[i]
        result = result.append(track, crossfade=CROSSFADE_MS)
        print(f"    + Segment {seg_id} ({name}) → total: {len(result)/1000:.2f}s")

    # Final fade out
    result = result.fade_out(3000)

    # Save
    output_path = FINAL_DIR / "bgm_stitched_v2.wav"
    result.export(str(output_path), format="wav")

    print(f"\n  ✓ Saved: {output_path}")
    print(f"  Total duration: {len(result)/1000:.2f}s ({len(result)/1000/60:.1f} min)")

    return str(output_path)


def detect_voice_activity(voice_audio: AudioSegment, frame_ms: int = 100) -> list:
    """Energy-based VAD."""
    samples = np.array(voice_audio.get_array_of_samples())
    frame_samples = int(voice_audio.frame_rate * frame_ms / 1000)

    frames = []
    for i in range(0, len(samples), frame_samples):
        frame = samples[i:i + frame_samples]
        if len(frame) > 0:
            rms = np.sqrt(np.mean(frame.astype(float) ** 2))
            frames.append(rms)

    if not frames:
        return []

    threshold = max(frames) * 0.15

    return [(i * frame_ms, rms > threshold) for i, rms in enumerate(frames)]


def apply_ducking(bgm: AudioSegment, vad_result: list, frame_ms: int = 100) -> AudioSegment:
    """Apply ducking: -18dB during voice, -12dB during silence."""
    ducked = AudioSegment.silent(duration=0)

    for start_ms, is_active in vad_result:
        end_ms = min(start_ms + frame_ms, len(bgm))
        frame = bgm[start_ms:end_ms]

        if is_active:
            frame = frame - 18  # Voice active: lower BGM
        else:
            frame = frame - 12  # Voice silent: slightly higher

        ducked = ducked + frame

    return ducked


def mix_final():
    """Mix BGM with voice and create final output."""
    print("\n" + "=" * 70)
    print("MIXING FINAL AUDIO")
    print("=" * 70)

    FINAL_DIR.mkdir(parents=True, exist_ok=True)

    # Load stitched BGM
    bgm_path = FINAL_DIR / "bgm_stitched_v2.wav"
    if not bgm_path.exists():
        print("ERROR: Stitched BGM not found. Run --stitch first.")
        return None

    bgm = AudioSegment.from_file(str(bgm_path))
    print(f"  Loaded BGM: {len(bgm)/1000:.2f}s")

    # Load voice-only audio
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

    print(f"  Total voice: {len(voice)/1000:.2f}s")

    # Match lengths
    if len(bgm) < len(voice):
        loops = (len(voice) // len(bgm)) + 1
        bgm = bgm * loops
    bgm = bgm[:len(voice)]

    # VAD
    print("\n  Running voice activity detection...")
    vad_result = detect_voice_activity(voice)
    print(f"    Detected {len(vad_result)} frames")

    # Apply ducking
    print("  Applying ducking...")
    bgm_ducked = apply_ducking(bgm, vad_result)

    # Mix
    print("  Mixing voice + BGM...")
    voice = voice.normalize()
    final_mix = voice.overlay(bgm_ducked)
    final_mix = final_mix.normalize()

    # Export
    output_path = FINAL_DIR / "final_podcast_v2.mp3"
    final_mix.export(str(output_path), format="mp3", bitrate="192k")

    print(f"\n  ✓ Saved: {output_path}")
    print(f"  Duration: {len(final_mix)/1000:.2f}s ({len(final_mix)/1000/60:.1f} min)")

    return str(output_path)


def update_video():
    """Update video with new audio."""
    print("\n" + "=" * 70)
    print("UPDATING VIDEO")
    print("=" * 70)

    video_output_dir = VISUALS_DIR / "v2_daisy"
    video_output_dir.mkdir(parents=True, exist_ok=True)

    # Find source video
    source_video = VISUALS_DIR / "voice_only" / "final_podcast_video_voice_only.mp4"
    if not source_video.exists():
        source_video = VISUALS_DIR / "final_podcast_video.mp4"

    if not source_video.exists():
        print("ERROR: No source video found")
        return None

    # Find new audio
    new_audio = FINAL_DIR / "final_podcast_v2.mp3"
    if not new_audio.exists():
        print("ERROR: Final audio not found. Run --mix first.")
        return None

    output_path = video_output_dir / "final_podcast_video_v2.mp4"

    print(f"  Source: {source_video}")
    print(f"  Audio: {new_audio}")
    print(f"  Output: {output_path}")

    cmd = [
        "ffmpeg", "-y",
        "-i", str(source_video),
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
        # Get duration
        probe = subprocess.run([
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(output_path)
        ], capture_output=True, text=True)
        duration = float(probe.stdout.strip())

        print(f"\n  ✓ Success!")
        print(f"  Duration: {duration:.2f}s ({duration/60:.1f} min)")
        return str(output_path)
    else:
        print(f"  ERROR: {result.stderr}")
        return None


def main():
    parser = argparse.ArgumentParser(description="Advanced BGM Pipeline V2 - 9-Segment Daisy-Chain")
    parser.add_argument("--generate", action="store_true", help="Generate all 9 segments")
    parser.add_argument("--stitch", action="store_true", help="Stitch segments with crossfades")
    parser.add_argument("--mix", action="store_true", help="Mix with voice and finalize")
    parser.add_argument("--video", action="store_true", help="Update video with new audio")
    parser.add_argument("--all", action="store_true", help="Run full pipeline")

    args = parser.parse_args()

    if args.all:
        print("\n" + "=" * 70)
        print("9-SEGMENT DAISY-CHAIN PIPELINE - FULL RUN")
        print("=" * 70)

        generate_all_segments()
        stitch_segments()
        mix_final()
        update_video()

        print("\n" + "=" * 70)
        print("PIPELINE COMPLETE")
        print("=" * 70)
        print(f"\nFinal video: {VISUALS_DIR / 'v2_daisy' / 'final_podcast_video_v2.mp4'}")

    elif args.generate:
        generate_all_segments()
    elif args.stitch:
        stitch_segments()
    elif args.mix:
        mix_final()
    elif args.video:
        update_video()
    else:
        print("No action specified. Use --help for options.")
        print("\nQuick start:")
        print("  python advanced_bgm_pipeline_v2.py --all")


if __name__ == "__main__":
    main()
