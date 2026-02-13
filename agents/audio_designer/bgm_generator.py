"""
BGM Generator
Author: Sarath

Generates background music using Fal AI based on emotion/theme.

Features:
- Emotion-based music generation
- Module-specific BGM with theme matching
- Support for daisy-chain segment generation
"""

import fal_client
import requests
from pathlib import Path
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

from config.prompts import EMOTION_MUSIC_MAP, DEFAULT_MUSIC, BGM_SEGMENT_PROMPTS

load_dotenv()


class BGMGenerator:
    """
    Background Music Generator using Fal AI stable-audio.

    Features:
    - Emotion-to-music mapping
    - Module-specific BGM generation
    - Daisy-chain segment support for seamless transitions
    """

    def __init__(self, output_dir: Optional[Path] = None):
        """
        Initialize the BGM Generator.

        Args:
            output_dir: Output directory for BGM files
        """
        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            self.output_dir = Path(__file__).parent.parent.parent / "Output" / "audio" / "bgm"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        print(f"[BGMGenerator] Output directory: {self.output_dir}")

    def get_music_prompt(self, emotion: str) -> Dict[str, Any]:
        """
        Get music generation parameters based on emotion.

        Args:
            emotion: Emotion string from script metadata

        Returns:
            Dictionary with prompt and duration
        """
        emotion_lower = emotion.lower()
        return EMOTION_MUSIC_MAP.get(emotion_lower, DEFAULT_MUSIC)

    def generate_bgm(
        self,
        emotion: str,
        output_filename: str,
        duration: int = 30
    ) -> Optional[str]:
        """
        Generate background music based on emotion.

        Args:
            emotion: The emotion/mood for the music
            output_filename: Name for the output file (without extension)
            duration: Duration in seconds

        Returns:
            Path to the generated audio file
        """
        output_path = self.output_dir / f"{output_filename}.wav"

        music_params = self.get_music_prompt(emotion)
        prompt = music_params["prompt"]

        print(f"  Generating BGM for emotion '{emotion}': {output_filename}")

        try:
            result = fal_client.subscribe(
                "fal-ai/stable-audio",
                arguments={
                    "prompt": prompt,
                    "seconds_total": duration,
                    "steps": 100
                },
                with_logs=False
            )

            # Download the generated audio
            audio_url = result.get("audio_file", {}).get("url")
            if audio_url:
                response = requests.get(audio_url)
                with open(output_path, "wb") as f:
                    f.write(response.content)
                print(f"    Saved: {output_path}")
                return str(output_path)
            else:
                print(f"    Error: No audio generated")
                return None

        except Exception as e:
            print(f"    Error generating BGM: {e}")
            return None

    def generate_segment(
        self,
        segment_id: int,
        output_filename: Optional[str] = None,
        conditioning_audio: Optional[str] = None,
        conditioning_strength: float = 0.3
    ) -> Optional[str]:
        """
        Generate a BGM segment using daisy-chain configuration.

        Args:
            segment_id: Segment ID (1-9) from BGM_SEGMENT_PROMPTS
            output_filename: Optional custom filename
            conditioning_audio: Path to audio for conditioning (daisy-chain)
            conditioning_strength: Strength of conditioning (0.3-0.4)

        Returns:
            Path to generated segment
        """
        if segment_id not in BGM_SEGMENT_PROMPTS:
            print(f"  Error: Unknown segment ID {segment_id}")
            return None

        segment_config = BGM_SEGMENT_PROMPTS[segment_id]
        prompt = segment_config["prompt"]
        duration = min(segment_config["duration"], 47)  # Fal AI max is 47s

        if output_filename is None:
            safe_name = segment_config["name"].lower().replace(" ", "_").replace(":", "")
            output_filename = f"segment_{segment_id:02d}_{safe_name}"

        output_path = self.output_dir / f"{output_filename}.wav"

        print(f"  Generating segment {segment_id}: {segment_config['name']}")
        print(f"    Phase: {segment_config['phase']}")
        print(f"    Duration: {duration}s")

        try:
            arguments = {
                "prompt": prompt,
                "seconds_total": duration,
                "steps": 100
            }

            # Add conditioning if provided (for daisy-chain)
            if conditioning_audio:
                print(f"    Conditioning from: {conditioning_audio}")
                arguments["audio_input"] = conditioning_audio
                arguments["audio_strength"] = conditioning_strength

            result = fal_client.subscribe(
                "fal-ai/stable-audio",
                arguments=arguments,
                with_logs=False
            )

            audio_url = result.get("audio_file", {}).get("url")
            if audio_url:
                response = requests.get(audio_url)
                with open(output_path, "wb") as f:
                    f.write(response.content)
                print(f"    Saved: {output_path}")
                return str(output_path)
            else:
                print(f"    Error: No audio generated")
                return None

        except Exception as e:
            print(f"    Error generating segment: {e}")
            return None

    def generate_module_bgm(self, modules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate BGM for each module based on its emotion arc.

        Args:
            modules: List of modules from enhanced script

        Returns:
            List of generated BGM file paths with metadata
        """
        bgm_files = []

        for module in modules:
            module_id = module.get("id", 0)
            emotion_arc = module.get("emotion_arc", "neutral")

            # Extract primary emotion from emotion arc
            primary_emotion = emotion_arc.split("->")[0].strip() if "->" in emotion_arc else emotion_arc

            # Get emotions from chunks for variety
            chunks = module.get("chunks", [])
            chunk_emotions = [c.get("emotion", "neutral") for c in chunks]

            # Use the most intense emotion from the module
            all_emotions = [primary_emotion] + chunk_emotions
            selected_emotion = "neutral"
            for em in all_emotions:
                if em.lower() in EMOTION_MUSIC_MAP:
                    selected_emotion = em
                    break

            filename = f"module_{module_id}_bgm"
            path = self.generate_bgm(selected_emotion, filename, duration=45)

            if path:
                bgm_files.append({
                    "module_id": module_id,
                    "path": path,
                    "emotion": selected_emotion,
                    "module_title": module.get("title", "")
                })

        return bgm_files

    def generate_all_segments(
        self,
        use_daisy_chain: bool = True,
        conditioning_strength: float = 0.35
    ) -> List[Dict[str, Any]]:
        """
        Generate all 9 BGM segments with optional daisy-chain conditioning.

        Args:
            use_daisy_chain: Whether to use audio conditioning between segments
            conditioning_strength: Strength of audio conditioning

        Returns:
            List of all generated segment metadata
        """
        segments = []
        previous_audio = None

        for segment_id in range(1, 10):
            conditioning = previous_audio if use_daisy_chain and segment_id > 1 else None

            path = self.generate_segment(
                segment_id,
                conditioning_audio=conditioning,
                conditioning_strength=conditioning_strength
            )

            if path:
                config = BGM_SEGMENT_PROMPTS[segment_id]
                segments.append({
                    "segment_id": segment_id,
                    "name": config["name"],
                    "phase": config["phase"],
                    "path": path,
                    "duration": config["duration"]
                })
                previous_audio = path

        return segments


if __name__ == "__main__":
    generator = BGMGenerator()

    # Test with sample emotion
    path = generator.generate_bgm("wonder", "test_bgm", duration=15)
    print(f"Generated: {path}")
