"""
Video Assembler - Combines images + audio into video with crossfade transitions.

Uses a single-pass FFmpeg pipeline to:
1. Scale/pad images to target resolution
2. Optionally apply Ken Burns effect (zoompan) — Pro mode only
3. Chain xfade transitions between images
4. Mux audio track

All done in ONE FFmpeg call with no intermediate files.
"""

import platform
import subprocess
import os
from pathlib import Path

SUBPROCESS_TIMEOUT = 120  # seconds


def _run_subprocess(cmd, timeout=None, **kwargs):
    """Run subprocess with timeout, raising RuntimeError on timeout."""
    effective_timeout = timeout or SUBPROCESS_TIMEOUT
    try:
        return subprocess.run(cmd, timeout=effective_timeout, **kwargs)
    except subprocess.TimeoutExpired:
        raise RuntimeError(
            f"FFmpeg process timed out after {effective_timeout}s. "
            f"Command: {' '.join(str(c) for c in cmd[:4])}..."
        )


def _detect_hw_encoder():
    """Detect the best available H.264 encoder.

    Tries h264_videotoolbox on macOS, falls back to libx264 ultrafast.

    Returns:
        Tuple of (encoder_name, encoder_args_list).
    """
    if platform.system() == "Darwin":
        try:
            result = subprocess.run(
                ["ffmpeg", "-encoders"],
                capture_output=True, text=True, timeout=5
            )
            if "h264_videotoolbox" in result.stdout:
                return ("h264_videotoolbox", ["-profile:v", "main", "-b:v", "2M"])
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
    return ("libx264", ["-preset", "ultrafast", "-crf", "28"])


def _build_static_filter_graph(
    num_images, per_image_duration, crossfade_duration, fps, width, height
):
    """Build a filter_complex string for static images with xfade transitions.

    Each image is scaled/padded to the target resolution, then trimmed
    to the calculated duration. Images are chained with xfade=fade.

    Args:
        num_images: Number of input images.
        per_image_duration: Display duration per image in seconds.
        crossfade_duration: Crossfade overlap in seconds.
        fps: Target frames per second.
        width: Target width.
        height: Target height.

    Returns:
        Tuple of (filter_complex_string, final_output_label).
    """
    parts = []
    for i in range(num_images):
        parts.append(
            f"[{i}:v]scale={width}:{height}:force_original_aspect_ratio=decrease,"
            f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,setsar=1,"
            f"fps={fps},format=yuv420p,"
            f"trim=duration={per_image_duration},setpts=PTS-STARTPTS[v{i}]"
        )

    if num_images == 1:
        return ";\n".join(parts), "v0"

    # Chain xfade transitions
    accumulated = per_image_duration - crossfade_duration
    for i in range(num_images - 1):
        left = f"v{i}" if i == 0 else f"xf{i - 1}"
        right = f"v{i + 1}"
        out = f"xf{i}" if i < num_images - 2 else "vout"
        parts.append(
            f"[{left}][{right}]xfade=transition=fade:"
            f"duration={crossfade_duration}:offset={accumulated:.4f}[{out}]"
        )
        if i < num_images - 2:
            accumulated += per_image_duration - crossfade_duration

    return ";\n".join(parts), "vout"


def _build_ken_burns_filter_graph(
    num_images, per_image_duration, crossfade_duration, fps, width, height
):
    """Build a filter_complex string with Ken Burns (zoompan) + xfade transitions.

    Each image gets a zoompan effect (cycling through zoom_in, pan_right,
    zoom_out, pan_left) and then images are chained with xfade.

    Args:
        num_images: Number of input images.
        per_image_duration: Display duration per image in seconds.
        crossfade_duration: Crossfade overlap in seconds.
        fps: Target frames per second.
        width: Target width.
        height: Target height.

    Returns:
        Tuple of (filter_complex_string, final_output_label).
    """
    frames = int(per_image_duration * fps)
    effects = []
    for i in range(num_images):
        effect_idx = i % 4
        if effect_idx == 0:  # zoom_in
            zp = f"z='1+0.15*on/{frames}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
        elif effect_idx == 1:  # pan_right
            zp = f"z='1.1':x='iw*0.1*on/{frames}':y='ih/2-(ih/zoom/2)'"
        elif effect_idx == 2:  # zoom_out
            zp = f"z='1.15-0.15*on/{frames}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
        else:  # pan_left
            zp = f"z='1.1':x='iw*0.1*(1-on/{frames})':y='ih/2-(ih/zoom/2)'"
        effects.append(zp)

    parts = []
    for i in range(num_images):
        parts.append(
            f"[{i}:v]zoompan={effects[i]}:d={frames}:s={width}x{height}:fps={fps},"
            f"format=yuv420p,setpts=PTS-STARTPTS[v{i}]"
        )

    if num_images == 1:
        return ";\n".join(parts), "v0"

    # Chain xfade transitions
    accumulated = per_image_duration - crossfade_duration
    for i in range(num_images - 1):
        left = f"v{i}" if i == 0 else f"xf{i - 1}"
        right = f"v{i + 1}"
        out = f"xf{i}" if i < num_images - 2 else "vout"
        parts.append(
            f"[{left}][{right}]xfade=transition=fade:"
            f"duration={crossfade_duration}:offset={accumulated:.4f}[{out}]"
        )
        if i < num_images - 2:
            accumulated += per_image_duration - crossfade_duration

    return ";\n".join(parts), "vout"


def get_audio_duration(audio_path: str) -> float:
    """Get duration of audio file in seconds."""
    result = _run_subprocess([
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

    Legacy helper kept for backward compatibility. New code should use
    create_podcast_video() with use_ken_burns=True.

    Args:
        image_path: Path to the source image
        output_path: Path for the output video clip
        duration: Duration in seconds
        effect_type: 'zoom_in', 'zoom_out', 'pan_left', 'pan_right'
        fps: Frames per second
    """
    frames = int(duration * fps)

    if effect_type == "zoom_in":
        zoompan = f"zoompan=z='1+0.15*on/{frames}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s=1920x1080:fps={fps}"
    elif effect_type == "zoom_out":
        zoompan = f"zoompan=z='1.15-0.15*on/{frames}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s=1920x1080:fps={fps}"
    elif effect_type == "pan_left":
        zoompan = f"zoompan=z='1.1':x='iw*0.1*(1-on/{frames})':y='ih/2-(ih/zoom/2)':d={frames}:s=1920x1080:fps={fps}"
    elif effect_type == "pan_right":
        zoompan = f"zoompan=z='1.1':x='iw*0.1*on/{frames}':y='ih/2-(ih/zoom/2)':d={frames}:s=1920x1080:fps={fps}"
    else:
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

    _run_subprocess(cmd, capture_output=True)
    return output_path


def concatenate_with_crossfade(clip_paths: list, output_path: str,
                                crossfade_duration: float = 1.0):
    """
    Concatenate video clips with crossfade transitions.

    Legacy helper kept for backward compatibility. New code should use
    create_podcast_video() directly.

    Args:
        clip_paths: List of video clip paths
        output_path: Path for the output video
        crossfade_duration: Duration of crossfade in seconds
    """
    if len(clip_paths) == 1:
        _run_subprocess(["cp", clip_paths[0], output_path])
        return output_path

    if len(clip_paths) == 2:
        result = _run_subprocess([
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
        _run_subprocess(cmd, capture_output=True)
        return output_path

    inputs = []
    for i, path in enumerate(clip_paths):
        inputs.extend(["-i", path])

    durations = []
    for path in clip_paths:
        result = _run_subprocess([
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            path
        ], capture_output=True, text=True)
        durations.append(float(result.stdout.strip()))

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
    _run_subprocess(cmd, capture_output=True)
    return output_path


def add_audio_to_video(video_path: str, audio_path: str, output_path: str):
    """Add audio track to video.

    Legacy helper kept for backward compatibility.
    """
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-i", audio_path,
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "192k",
        output_path
    ]
    _run_subprocess(cmd, capture_output=True)
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

    images = sorted(image_dir.glob("hook_img_*.png"))
    print(f"Found {len(images)} images")

    if not images:
        print("No images found!")
        return None

    return create_podcast_video(
        str(audio_path),
        [str(img) for img in images],
        str(output_path),
        crossfade_duration=1.0,
        use_ken_burns=True,
    )


def create_podcast_video(
    audio_path: str,
    image_paths: list,
    output_path: str,
    crossfade_duration: float = 1.0,
    *,
    use_ken_burns: bool = False,
    resolution: tuple = (1920, 1080),
    fps: int = 24,
    quality: str = "fast",
) -> str:
    """
    Create a full podcast video from audio and images in a single FFmpeg pass.

    Builds one FFmpeg command that reads all images + audio, applies
    scale/pad (or zoompan for Ken Burns), chains xfade transitions,
    and muxes audio — all in one encode pass with no intermediate files.

    Args:
        audio_path: Path to the mixed audio file.
        image_paths: List of image file paths (in order).
        output_path: Path for the final output video.
        crossfade_duration: Duration of crossfade between images in seconds.
        use_ken_burns: Apply Ken Burns (zoompan) effect. False = static images.
        resolution: Output resolution as (width, height).
        fps: Frames per second.
        quality: "fast" uses HW encoder or ultrafast preset;
                 "quality" uses libx264 medium preset.

    Returns:
        Path to the created video, or audio_path if no images provided.
    """
    output_path_obj = Path(output_path)
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)

    if not image_paths:
        return audio_path

    audio_duration = get_audio_duration(audio_path)
    width, height = resolution

    # Calculate per-image duration accounting for crossfade overlap
    num_images = len(image_paths)
    num_crossfades = max(num_images - 1, 0)
    total_content = audio_duration + num_crossfades * crossfade_duration
    per_image_duration = total_content / num_images

    # Build filter graph
    if use_ken_burns:
        filter_graph, output_label = _build_ken_burns_filter_graph(
            num_images, per_image_duration, crossfade_duration, fps, width, height
        )
    else:
        filter_graph, output_label = _build_static_filter_graph(
            num_images, per_image_duration, crossfade_duration, fps, width, height
        )

    # Select encoder
    if quality == "fast":
        encoder, encoder_args = _detect_hw_encoder()
    else:
        encoder = "libx264"
        encoder_args = ["-preset", "medium", "-crf", "23"]

    # Audio input is the last input (index = num_images)
    audio_index = num_images

    # Build single FFmpeg command
    cmd = ["ffmpeg", "-y"]

    # Add image inputs (set -framerate to match target fps to avoid excess frames)
    for img in image_paths:
        cmd.extend(["-framerate", str(fps), "-loop", "1", "-t", f"{per_image_duration + 1}", "-i", img])

    # Add audio input
    cmd.extend(["-i", audio_path])

    # Filter complex + mapping
    cmd.extend([
        "-filter_complex", filter_graph,
        "-map", f"[{output_label}]",
        "-map", f"{audio_index}:a",
        "-c:v", encoder,
    ])
    cmd.extend(encoder_args)
    cmd.extend([
        "-pix_fmt", "yuv420p",
        "-r", str(fps),
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        str(output_path),
    ])

    # Scale timeout to audio duration: fast ~0.15x realtime, quality ~0.5x realtime
    if quality == "fast":
        cmd_timeout = max(30, int(audio_duration * 0.15) + 10)
    else:
        cmd_timeout = max(180, int(audio_duration * 0.5) + 30)

    _run_subprocess(cmd, timeout=cmd_timeout, capture_output=True)

    return str(output_path)


if __name__ == "__main__":
    BASE_DIR = Path(__file__).parent.parent

    result = create_hook_video(
        image_dir=BASE_DIR / "Output" / "Visuals Included" / "hook",
        audio_path=BASE_DIR / "Output" / "audio" / "previews" / "hook_preview_paced.mp3",
        output_path=BASE_DIR / "Output" / "Visuals Included" / "hook_video.mp4"
    )

    if result:
        print(f"\nHook video created successfully!")
