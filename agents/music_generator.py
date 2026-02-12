"""
Music Generator Agent

Generates background music using Fal AI based on emotion/theme.
"""

import os
import fal_client
import requests
from pathlib import Path


# Emotion to music prompt mapping - melodious and harmonious prompts
EMOTION_MUSIC_MAP = {
    "wonder": {
        "prompt": "soft piano melody with gentle ambient pads, smooth ethereal soundscape, melodic and harmonious, dreamy major key, flowing arpeggios, peaceful cinematic background",
        "duration": 30
    },
    "curiosity": {
        "prompt": "gentle melodic piano with soft synthesizer pads, playful and smooth, light harmonious textures, medium tempo, warm ambient background music",
        "duration": 30
    },
    "tension": {
        "prompt": "subtle dramatic strings with melodic progression, building anticipation, smooth orchestral layers, gentle crescendo, harmonious minor key, cinematic and elegant",
        "duration": 30
    },
    "triumph": {
        "prompt": "uplifting orchestral melody with inspiring piano, harmonious brass ensemble, soaring strings, triumphant and melodic, major key, smooth cinematic score",
        "duration": 30
    },
    "melancholy": {
        "prompt": "gentle melancholic piano melody, soft flowing strings, smooth and melodic, reflective harmonious ambient, slow tempo, warm emotional soundscape",
        "duration": 30
    },
    "intrigue": {
        "prompt": "smooth mysterious piano melody, gentle ambient textures, harmonious and melodic, subtle elegant progression, warm documentary style background",
        "duration": 30
    },
    "excitement": {
        "prompt": "upbeat melodic piano with smooth synthesizers, harmonious and joyful, gentle energy, major key, pleasant rhythmic background music",
        "duration": 30
    },
    "reflection": {
        "prompt": "calm melodic piano with gentle ambient pads, smooth peaceful soundscape, harmonious and meditative, soft flowing melodies, warm background",
        "duration": 30
    },
    "restlessness": {
        "prompt": "gentle building melody with soft rhythmic pulse, smooth anticipation, melodic progression, harmonious layered textures, warm ambient energy",
        "duration": 30
    },
    "explosive energy": {
        "prompt": "energetic melodic rock with harmonious guitar, smooth driving rhythm, uplifting crescendo, major key, pleasant powerful music",
        "duration": 30
    },
    "rebellion": {
        "prompt": "energetic but melodic rock music, driving rhythm with harmonious guitar riffs, smooth powerful progression, uplifting energy, pleasant rock soundscape",
        "duration": 30
    },
    "liberation": {
        "prompt": "soaring melodic strings with uplifting piano, triumphant harmony, smooth flowing melody, major key, gentle euphoric soundscape, harmonious freedom music",
        "duration": 30
    },
    "experimentation": {
        "prompt": "creative melodic textures with smooth ambient pads, harmonious innovative sounds, gentle electronic elements, pleasant artistic soundscape",
        "duration": 30
    },
    "mastery": {
        "prompt": "elegant piano melody with sophisticated strings, confident and smooth, harmonious arrangement, refined cinematic sound, gentle triumphant resolution",
        "duration": 30
    },
    "intensity": {
        "prompt": "building orchestral melody with smooth strings, harmonious dramatic progression, elegant crescendo, melodic and refined, cinematic tension",
        "duration": 30
    }
}

DEFAULT_MUSIC = {
    "prompt": "soft melodic ambient background music, gentle piano with smooth pads, harmonious and pleasant, warm cinematic soundscape",
    "duration": 30
}


class MusicGenerator:
    def __init__(self):
        self.output_dir = Path(__file__).parent.parent / "Output" / "audio" / "bgm"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def get_music_prompt(self, emotion: str) -> dict:
        """Get music generation parameters based on emotion."""
        emotion_lower = emotion.lower()
        return EMOTION_MUSIC_MAP.get(emotion_lower, DEFAULT_MUSIC)

    def generate_bgm(self, emotion: str, output_filename: str, duration: int = 30) -> str:
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

    def generate_module_bgm(self, modules: list) -> list:
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

            # Extract primary emotion from emotion arc (e.g., "wonder -> triumph" -> "wonder")
            primary_emotion = emotion_arc.split("->")[0].strip() if "->" in emotion_arc else emotion_arc

            # Also get emotions from chunks for variety
            chunks = module.get("chunks", [])
            chunk_emotions = [c.get("emotion", "neutral") for c in chunks]

            # Use the most intense emotion from the module
            all_emotions = [primary_emotion] + chunk_emotions
            # Pick the first valid emotion
            selected_emotion = "neutral"
            for em in all_emotions:
                if em.lower() in EMOTION_MUSIC_MAP:
                    selected_emotion = em
                    break

            filename = f"module_{module_id}_bgm"
            path = self.generate_bgm(selected_emotion, filename, duration=45)  # Max is 47 seconds

            if path:
                bgm_files.append({
                    "module_id": module_id,
                    "path": path,
                    "emotion": selected_emotion,
                    "module_title": module.get("title", "")
                })

        return bgm_files


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    generator = MusicGenerator()

    # Test with sample emotion
    path = generator.generate_bgm("wonder", "test_bgm", duration=15)
    print(f"Generated: {path}")
