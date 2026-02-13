"""
FFmpeg Utilities
Author: Sarath

FFmpeg-based utilities for audio and video processing in the podcast enhancement system.
"""

import subprocess
from pathlib import Path
from typing import Optional


def get_audio_duration(audio_path: str) -> float:
    """
    Get duration of audio file in seconds using ffprobe.

    Args:
        audio_path: Path to the audio file

    Returns:
        Duration in seconds

    Raises:
        ValueError: If duration cannot be determined
    """
    result = subprocess.run([
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        audio_path
    ], capture_output=True, text=True)

    if result.returncode != 0:
        raise ValueError(f"Failed to get duration: {result.stderr}")

    return float(result.stdout.strip())


def get_video_duration(video_path: str) -> float:
    """
    Get duration of video file in seconds using ffprobe.

    Args:
        video_path: Path to the video file

    Returns:
        Duration in seconds

    Raises:
        ValueError: If duration cannot be determined
    """
    return get_audio_duration(video_path)  # Same ffprobe command works for video


def replace_audio_in_video(video_path: str, audio_path: str, output_path: str) -> str:
    """
    Replace audio track in a video file.

    Args:
        video_path: Path to the source video file
        audio_path: Path to the new audio file
        output_path: Path for the output video file

    Returns:
        Path to the output file

    Raises:
        RuntimeError: If FFmpeg command fails
    """
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
        raise RuntimeError(f"FFmpeg error: {result.stderr}")

    return output_path


def add_audio_to_video(video_path: str, audio_path: str, output_path: str) -> str:
    """
    Add audio track to video.

    Args:
        video_path: Path to the source video file
        audio_path: Path to the audio file to add
        output_path: Path for the output video file

    Returns:
        Path to the output file
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

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg error: {result.stderr}")

    return output_path


def concat_videos(video_paths: list, output_path: str) -> str:
    """
    Concatenate multiple videos into one.

    Args:
        video_paths: List of video file paths to concatenate
        output_path: Path for the output video file

    Returns:
        Path to the output file
    """
    output_dir = Path(output_path).parent
    concat_file = output_dir / "concat_list.txt"

    # Create concat file
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

    # Clean up concat file
    concat_file.unlink()

    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg error: {result.stderr}")

    return output_path


def create_video_from_image(
    image_path: str,
    output_path: str,
    duration: float,
    fps: int = 30
) -> str:
    """
    Create a video clip from a static image.

    Args:
        image_path: Path to the source image
        output_path: Path for the output video
        duration: Duration in seconds
        fps: Frames per second

    Returns:
        Path to the output file
    """
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", image_path,
        "-c:v", "libx264",
        "-t", str(duration),
        "-pix_fmt", "yuv420p",
        "-vf", f"scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,fps={fps}",
        output_path
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg error: {result.stderr}")

    return output_path


def create_ken_burns_clip(
    image_path: str,
    output_path: str,
    duration: float,
    effect_type: str = "zoom_in",
    fps: int = 30
) -> str:
    """
    Create a video clip from an image with Ken Burns effect.

    Args:
        image_path: Path to the source image
        output_path: Path for the output video clip
        duration: Duration in seconds
        effect_type: 'zoom_in', 'zoom_out', 'pan_left', 'pan_right'
        fps: Frames per second

    Returns:
        Path to the output file
    """
    frames = int(duration * fps)

    # Ken Burns effect configurations
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

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg error: {result.stderr}")

    return output_path


def concatenate_with_crossfade(
    clip_paths: list,
    output_path: str,
    crossfade_duration: float = 1.0
) -> str:
    """
    Concatenate video clips with crossfade transitions.

    Args:
        clip_paths: List of video clip paths
        output_path: Path for the output video
        crossfade_duration: Duration of crossfade in seconds

    Returns:
        Path to the output file
    """
    if len(clip_paths) == 1:
        subprocess.run(["cp", clip_paths[0], output_path])
        return output_path

    if len(clip_paths) == 2:
        clip1_duration = get_video_duration(clip_paths[0])
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
    inputs = []
    for path in clip_paths:
        inputs.extend(["-i", path])

    # Get all durations
    durations = [get_video_duration(path) for path in clip_paths]

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

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg error: {result.stderr}")

    return output_path


def extract_audio(video_path: str, output_path: str, format: str = "mp3") -> str:
    """
    Extract audio from video file.

    Args:
        video_path: Path to the video file
        output_path: Path for the output audio file
        format: Output format (mp3, wav, aac)

    Returns:
        Path to the output file
    """
    codec_map = {
        "mp3": "libmp3lame",
        "wav": "pcm_s16le",
        "aac": "aac"
    }

    codec = codec_map.get(format, "libmp3lame")

    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-vn",
        "-c:a", codec,
        "-b:a", "192k",
        output_path
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg error: {result.stderr}")

    return output_path
