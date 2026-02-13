"""
Fal AI API Utilities
Author: Sarath

Unified wrapper for Fal AI API interactions in the podcast enhancement system.
"""

import io
import base64
import requests
from pathlib import Path
from typing import Optional, Union

import fal_client


def call_fal_api(
    model_path: str,
    arguments: dict,
    with_logs: bool = False
) -> dict:
    """
    Call the Fal AI API with the specified model and arguments.

    Args:
        model_path: The Fal AI model path (e.g., "fal-ai/stable-audio")
        arguments: Dictionary of arguments for the model
        with_logs: Whether to show logs during generation

    Returns:
        API response as dictionary

    Raises:
        RuntimeError: If API call fails
    """
    try:
        result = fal_client.subscribe(
            model_path,
            arguments=arguments,
            with_logs=with_logs
        )
        return result
    except Exception as e:
        raise RuntimeError(f"Fal AI API error: {e}")


def extract_url_from_response(response: dict, media_type: str = "audio") -> Optional[str]:
    """
    Extract media URL from Fal AI API response.

    Handles various response formats from different Fal AI models.

    Args:
        response: API response dictionary
        media_type: Type of media ("audio" or "image")

    Returns:
        URL string or None if not found
    """
    if not isinstance(response, dict):
        return None

    if media_type == "audio":
        # Try various audio response formats
        # Format 1: {"audio_file": {"url": "..."}}
        audio_file = response.get("audio_file")
        if isinstance(audio_file, dict):
            url = audio_file.get("url")
            if url:
                return url

        # Format 2: {"audio_url": "..."}
        audio_url = response.get("audio_url")
        if audio_url:
            return audio_url

        # Format 3: {"audio": {"url": "..."}}
        audio = response.get("audio")
        if isinstance(audio, dict):
            url = audio.get("url")
            if url:
                return url
        elif isinstance(audio, str):
            return audio

    elif media_type == "image":
        # Format 1: {"images": [{"url": "..."}]}
        images = response.get("images", [])
        if images and len(images) > 0:
            first_image = images[0]
            if isinstance(first_image, dict):
                url = first_image.get("url")
                if url:
                    return url

        # Format 2: {"image_url": "..."}
        image_url = response.get("image_url")
        if image_url:
            return image_url

        # Format 3: {"image": {"url": "..."}}
        image = response.get("image")
        if isinstance(image, dict):
            url = image.get("url")
            if url:
                return url

    return None


def download_media(url: str, output_path: Union[str, Path]) -> str:
    """
    Download media from URL and save to file.

    Args:
        url: URL to download from
        output_path: Path to save the downloaded file

    Returns:
        Path to the saved file as string

    Raises:
        RuntimeError: If download fails
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        response = requests.get(url)
        response.raise_for_status()

        with open(output_path, "wb") as f:
            f.write(response.content)

        return str(output_path)

    except requests.RequestException as e:
        raise RuntimeError(f"Download failed: {e}")


def generate_audio(
    prompt: str,
    duration: int = 30,
    steps: int = 100,
    conditioning_audio: Optional[bytes] = None,
    conditioning_strength: float = 0.35
) -> Optional[bytes]:
    """
    Generate audio using Fal AI stable-audio model.

    Args:
        prompt: Text prompt for audio generation
        duration: Duration in seconds (max 47)
        steps: Number of generation steps
        conditioning_audio: Optional audio bytes for conditioning
        conditioning_strength: Strength of conditioning (0.0-1.0)

    Returns:
        Generated audio as bytes, or None if failed
    """
    arguments = {
        "prompt": prompt,
        "seconds_total": min(duration, 47),
        "steps": steps
    }

    if conditioning_audio is not None:
        audio_b64 = base64.b64encode(conditioning_audio).decode("utf-8")
        arguments["audio_input"] = f"data:audio/wav;base64,{audio_b64}"
        arguments["input_strength"] = conditioning_strength

    try:
        result = call_fal_api("fal-ai/stable-audio", arguments)
        audio_url = extract_url_from_response(result, "audio")

        if audio_url:
            response = requests.get(audio_url)
            response.raise_for_status()
            return response.content

        return None

    except Exception as e:
        print(f"Audio generation error: {e}")
        return None


def generate_image(
    prompt: str,
    image_size: str = "landscape_16_9",
    num_images: int = 1,
    enable_safety_checker: bool = False
) -> Optional[str]:
    """
    Generate image using Fal AI Flux model.

    Args:
        prompt: Text prompt for image generation
        image_size: Output image size
        num_images: Number of images to generate
        enable_safety_checker: Whether to enable safety filter

    Returns:
        URL to generated image, or None if failed
    """
    arguments = {
        "prompt": prompt,
        "image_size": image_size,
        "num_images": num_images,
        "enable_safety_checker": enable_safety_checker
    }

    try:
        result = call_fal_api("fal-ai/flux/dev", arguments)
        return extract_url_from_response(result, "image")

    except Exception as e:
        print(f"Image generation error: {e}")
        return None


def generate_speech(
    text: str,
    voice_id: str = "Friendly_Female_English",
    speed: float = 1.0
) -> Optional[str]:
    """
    Generate speech using Fal AI MiniMax Speech-01-HD.

    Args:
        text: Text to convert to speech
        voice_id: Voice ID to use
        speed: Speech speed multiplier

    Returns:
        URL to generated audio, or None if failed
    """
    arguments = {
        "text": text,
        "voice_id": voice_id,
        "speed": speed
    }

    try:
        result = call_fal_api("fal-ai/minimax/speech-01-hd", arguments)
        return extract_url_from_response(result, "audio")

    except Exception as e:
        print(f"Speech generation error: {e}")
        return None


def audio_segment_to_base64(audio_segment) -> str:
    """
    Convert a pydub AudioSegment to base64 string.

    Args:
        audio_segment: pydub AudioSegment object

    Returns:
        Base64 encoded string of the audio
    """
    buffer = io.BytesIO()
    audio_segment.export(buffer, format="wav")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def base64_to_audio_bytes(b64_string: str) -> bytes:
    """
    Convert base64 string to audio bytes.

    Args:
        b64_string: Base64 encoded audio string

    Returns:
        Decoded audio bytes
    """
    return base64.b64decode(b64_string)
