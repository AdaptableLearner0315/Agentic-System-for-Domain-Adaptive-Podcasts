"""
Video Assembler - Combines images + audio into video with Ken Burns effect.

Uses FFmpeg to:
1. Apply Ken Burns effect (zoompan) to each image
2. Concatenate clips with crossfade transitions
3. Add audio track
"""

import subprocess
import os
from pathlib import Path


def get_audio_duration(audio_path: str) -> float:
    """Get duration of audio file in seconds."""
    result = subprocess.run([
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        audio_path
    ], capture_output=True, text=True)
    return float(result.stdout.strip())


def create_ken_burns_clip(image_path: str, output_path: str, duration: float,
                          effect_type: str = "zoom_in", fps: int = 30):
    """
    Create a video clip from an image with Ken Burns effect.

    Args:
        image_path: Path to the source image
        output_path: Path for the output video clip
        duration: Duration in seconds
        effect_type: 'zoom_in', 'zoom_out', 'pan_left', 'pan_right'
        fps: Frames per second
    """
    frames = int(duration * fps)

    # Ken Burns effect configurations
    if effect_type == "zoom_in":
        # Start at 1.0x zoom, end at 1.15x zoom, centered
        zoompan = f"zoompan=z='1+0.15*on/{frames}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s=1920x1080:fps={fps}"
    elif effect_type == "zoom_out":
        # Start at 1.15x zoom, end at 1.0x zoom
        zoompan = f"zoompan=z='1.15-0.15*on/{frames}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s=1920x1080:fps={fps}"
    elif effect_type == "pan_left":
        # Pan from right to left while slightly zoomed
        zoompan = f"zoompan=z='1.1':x='iw*0.1*(1-on/{frames})':y='ih/2-(ih/zoom/2)':d={frames}:s=1920x1080:fps={fps}"
    elif effect_type == "pan_right":
        # Pan from left to right while slightly zoomed
        zoompan = f"zoompan=z='1.1':x='iw*0.1*on/{frames}':y='ih/2-(ih/zoom/2)':d={frames}:s=1920x1080:fps={fps}"
    else:
        # Default: subtle zoom in
        zoompan = f"zoompan=z='1+0.1*on/{frames}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s=1920x1080:fps={fps}"

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", image_path,
        "-vf", zoompan,
        "-t", str(duration),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "medium",
        output_path
    ]

    subprocess.run(cmd, capture_output=True)
    return output_path


def concatenate_with_crossfade(clip_paths: list, output_path: str,
                                crossfade_duration: float = 1.0):
    """
    Concatenate video clips with crossfade transitions.

    Args:
        clip_paths: List of video clip paths
        output_path: Path for the output video
        crossfade_duration: Duration of crossfade in seconds
    """
    if len(clip_paths) == 1:
        # Just copy the single clip
        subprocess.run(["cp", clip_paths[0], output_path])
        return output_path

    if len(clip_paths) == 2:
        # Simple xfade between two clips
        # Get duration of first clip
        result = subprocess.run([
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            clip_paths[0]
        ], capture_output=True, text=True)
        clip1_duration = float(result.stdout.strip())
        offset = clip1_duration - crossfade_duration

        cmd = [
            "ffmpeg", "-y",
            "-i", clip_paths[0],
            "-i", clip_paths[1],
            "-filter_complex", f"xfade=transition=fade:duration={crossfade_duration}:offset={offset}",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-preset", "medium",
            output_path
        ]
        subprocess.run(cmd, capture_output=True)
        return output_path

    # For more than 2 clips, chain xfades
    # Build complex filter
    inputs = []
    for i, path in enumerate(clip_paths):
        inputs.extend(["-i", path])

    # Get all durations
    durations = []
    for path in clip_paths:
        result = subprocess.run([
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            path
        ], capture_output=True, text=True)
        durations.append(float(result.stdout.strip()))

    # Build xfade chain
    filter_parts = []
    current_offset = durations[0] - crossfade_duration

    for i in range(len(clip_paths) - 1):
        if i == 0:
            filter_parts.append(f"[0][1]xfade=transition=fade:duration={crossfade_duration}:offset={current_offset}[v{i}]")
        else:
            filter_parts.append(f"[v{i-1}][{i+1}]xfade=transition=fade:duration={crossfade_duration}:offset={current_offset}[v{i}]")
        current_offset += durations[i+1] - crossfade_duration

    filter_complex = ";".join(filter_parts)
    last_output = f"[v{len(clip_paths)-2}]"

    cmd = ["ffmpeg", "-y"] + inputs + [
        "-filter_complex", filter_complex,
        "-map", last_output,
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "medium",
        output_path
    ]
    subprocess.run(cmd, capture_output=True)
    return output_path


def add_audio_to_video(video_path: str, audio_path: str, output_path: str):
    """Add audio track to video."""
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-i", audio_path,
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "192k",
        output_path
    ]
    subprocess.run(cmd, capture_output=True)
    return output_path


def create_hook_video(
    image_dir: str,
    audio_path: str,
    output_path: str,
    image_durations: list = None
):
    """
    Create hook video from images and audio.

    Args:
        image_dir: Directory containing hook images
        audio_path: Path to hook audio file
        output_path: Path for output video
        image_durations: List of durations for each image (optional)
    """
    image_dir = Path(image_dir)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Get audio duration
    audio_duration = get_audio_duration(audio_path)
    print(f"Audio duration: {audio_duration:.2f}s")

    # Find hook images
    images = sorted(image_dir.glob("hook_img_*.png"))
    print(f"Found {len(images)} images")

    if not images:
        print("No images found!")
        return None

    # Calculate durations if not provided
    if image_durations is None:
        # For 2 images: ~65% for first (performance), ~35% for second (journey)
        if len(images) == 2:
            crossfade = 1.0
            # Account for crossfade overlap
            total_content = audio_duration + crossfade
            image_durations = [
                total_content * 0.65,  # ~30s for image 1
                total_content * 0.35   # ~17s for image 2
            ]
        else:
            # Equal distribution
            crossfade = 1.0 * (len(images) - 1)
            per_image = (audio_duration + crossfade) / len(images)
            image_durations = [per_image] * len(images)

    print(f"Image durations: {[f'{d:.2f}s' for d in image_durations]}")

    # Create temporary directory for clips
    temp_dir = output_path.parent / "temp_clips"
    temp_dir.mkdir(exist_ok=True)

    # Generate Ken Burns clips
    clips = []
    effects = ["zoom_in", "pan_right", "zoom_out", "pan_left"]  # Alternate effects

    for i, (img, duration) in enumerate(zip(images, image_durations)):
        clip_path = temp_dir / f"clip_{i}.mp4"
        effect = effects[i % len(effects)]
        print(f"Creating clip {i+1}: {img.name} ({duration:.2f}s, {effect})")
        create_ken_burns_clip(str(img), str(clip_path), duration, effect)
        clips.append(str(clip_path))

    # Concatenate clips with crossfade
    print("Concatenating clips with crossfade...")
    video_only = temp_dir / "video_only.mp4"
    concatenate_with_crossfade(clips, str(video_only), crossfade_duration=1.0)

    # Add audio
    print("Adding audio track...")
    add_audio_to_video(str(video_only), audio_path, str(output_path))

    # Cleanup temp files
    for clip in clips:
        os.remove(clip)
    os.remove(str(video_only))
    temp_dir.rmdir()

    print(f"\nSaved: {output_path}")
    return str(output_path)


if __name__ == "__main__":
    BASE_DIR = Path(__file__).parent.parent

    # Create hook video
    result = create_hook_video(
        image_dir=BASE_DIR / "Output" / "Visuals Included" / "hook",
        audio_path=BASE_DIR / "Output" / "audio" / "previews" / "hook_preview_paced.mp3",
        output_path=BASE_DIR / "Output" / "Visuals Included" / "hook_video.mp4"
    )

    if result:
        print(f"\n✓ Hook video created successfully!")
