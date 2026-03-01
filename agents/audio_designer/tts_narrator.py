"""
TTS Narrator
Author: Sarath

Generates speech audio from text using Fal AI MiniMax Speech-01-HD.

Features:
- Sentence-level TTS generation for precise control
- Intensity boosting based on tension and strong words
- Variable pauses at sentence boundaries
- Emotion-responsive voice parameters (speed, emphasis)
- Multi-speaker support with different voice IDs

Text processing functions are imported from utils.text_processing.
"""

import fal_client
import requests
from pathlib import Path
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

from utils.text_processing import (
    preprocess_text_for_tts,
    get_intensity_for_sentence,
    split_into_sentences
)
from config.emotion_voice_mapping import get_emotion_voice_params, EMOTION_VOICE_PARAMS
from config.speaker_config import get_voice_id, DEFAULT_VOICE, AVAILABLE_VOICES

load_dotenv()

# MiniMax Speech-01 configuration (default voice)
MINIMAX_VOICE_ID = "Friendly_Female_English"  # Warm, engaging narrator


class TTSNarrator:
    """
    Text-to-Speech narrator using MiniMax Speech-01-HD.

    Features:
    - Sentence-level generation for precise intensity control
    - Automatic text preprocessing for TTS
    - Intensity calculation based on tension and strong words
    - Emotion-responsive voice parameters (speed, emphasis)
    - Multi-speaker support with different voice IDs
    """

    def __init__(
        self,
        output_dir: Optional[Path] = None,
        ref_audio_path: Optional[str] = None,
        use_female_voice: bool = True,
        default_voice_key: Optional[str] = None
    ):
        """
        Initialize TTS Narrator using MiniMax Speech-01-HD.

        Args:
            output_dir: Output directory for TTS files
            ref_audio_path: Not used (kept for backwards compatibility)
            use_female_voice: Not used (MiniMax uses voice_id)
            default_voice_key: Default voice key from AVAILABLE_VOICES (e.g., 'female_friendly')
        """
        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            self.output_dir = Path(__file__).parent.parent.parent / "Output" / "audio" / "tts"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Set default voice
        self.default_voice_key = default_voice_key or DEFAULT_VOICE
        self.voice_id = get_voice_id(self.default_voice_key)
        self.emotion_voice_enabled = True  # Enable emotion-responsive voice by default

        print(f"[TTSNarrator] Using MiniMax Speech-01-HD with voice: {self.voice_id}")

    def generate_speech(
        self,
        text: str,
        output_filename: str,
        is_emphasis: bool = False,
        emotion: str = "neutral",
        voice_id: Optional[str] = None,
        speaker: Optional[str] = None
    ) -> Optional[str]:
        """
        Generate speech from text using MiniMax Speech-01-HD.

        Args:
            text: Text to convert to speech
            output_filename: Name for the output file (without extension)
            is_emphasis: If True, use slightly faster speed for emphasis
            emotion: Emotion for voice parameter adjustment (e.g., 'wonder', 'tension')
            voice_id: Specific MiniMax voice_id to use (overrides default)
            speaker: Speaker role for multi-speaker scripts (e.g., 'host', 'guest')

        Returns:
            Path to the generated audio file
        """
        output_path = self.output_dir / f"{output_filename}.wav"

        # Preprocess text for better TTS output
        processed_text = preprocess_text_for_tts(text)

        print(f"  Generating TTS for: {output_filename}")

        # Determine voice to use
        actual_voice_id = voice_id or self.voice_id
        if speaker:
            print(f"    Speaker: {speaker}")

        # Get emotion-specific parameters
        base_speed = 1.0
        if self.emotion_voice_enabled and emotion and emotion.lower() != "neutral":
            emotion_params = get_emotion_voice_params(emotion)
            base_speed = emotion_params.get("speed", 1.0)
            print(f"    Emotion: {emotion} (speed: {base_speed}x)")

        # Apply emphasis boost on top of emotion speed
        if is_emphasis:
            speed = base_speed * 1.03  # 3% boost for emphasis
        else:
            speed = base_speed

        # Clamp speed to reasonable range
        speed = max(0.8, min(1.3, speed))

        result = fal_client.subscribe(
            'fal-ai/minimax/speech-01-hd',
            arguments={
                'text': processed_text,
                'voice_id': actual_voice_id,
                'speed': speed,
            },
            with_logs=False
        )

        # Get audio URL from response (handle different formats)
        audio_url = None

        if isinstance(result, dict):
            audio_url = result.get('audio_url')
            if not audio_url:
                audio = result.get('audio')
                if isinstance(audio, dict):
                    audio_url = audio.get('url')
                elif isinstance(audio, str):
                    audio_url = audio
            if not audio_url:
                audio_file = result.get('audio_file')
                if isinstance(audio_file, dict):
                    audio_url = audio_file.get('url')

        if audio_url:
            response = requests.get(audio_url)
            with open(output_path, 'wb') as f:
                f.write(response.content)
            print(f"    Saved: {output_path}")
            return str(output_path)
        else:
            print(f"    Error: No audio generated. Response: {result}")
            return None

    def set_emotion_voice_enabled(self, enabled: bool):
        """Enable or disable emotion-responsive voice parameters."""
        self.emotion_voice_enabled = enabled
        print(f"[TTSNarrator] Emotion voice {'enabled' if enabled else 'disabled'}")

    def generate_all_chunks(self, enhanced_script: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate TTS for all chunks in the enhanced script.

        Args:
            enhanced_script: The enhanced script dictionary

        Returns:
            List of generated audio file paths with metadata
        """
        audio_files = []

        # Generate hook
        hook = enhanced_script.get("hook", {})
        if hook.get("text"):
            emotion = hook.get("emotion", "intrigue")
            voice_id = hook.get("voice_id")
            speaker = hook.get("speaker")

            path = self.generate_speech(
                hook["text"],
                "hook",
                emotion=emotion,
                voice_id=voice_id,
                speaker=speaker
            )
            if path:
                audio_files.append({
                    "type": "hook",
                    "path": path,
                    "text": hook["text"],
                    "emotion": emotion,
                    "speaker": speaker,
                    "voice_id": voice_id
                })

        # Generate module chunks
        modules = enhanced_script.get("modules", [])
        for module in modules:
            module_id = module.get("id", 0)
            chunks = module.get("chunks", [])

            for chunk_idx, chunk in enumerate(chunks):
                text = chunk.get("text", "")
                if text:
                    filename = f"module_{module_id}_chunk_{chunk_idx + 1}"
                    emotion = chunk.get("emotion", "neutral")
                    voice_id = chunk.get("voice_id")
                    speaker = chunk.get("speaker")

                    path = self.generate_speech(
                        text,
                        filename,
                        emotion=emotion,
                        voice_id=voice_id,
                        speaker=speaker
                    )
                    if path:
                        audio_files.append({
                            "type": "chunk",
                            "module_id": module_id,
                            "chunk_idx": chunk_idx,
                            "path": path,
                            "text": text,
                            "emotion": emotion,
                            "speaker": speaker,
                            "voice_id": voice_id,
                            "module_title": module.get("title", "")
                        })

        return audio_files

    def generate_all_chunks_sentence_level(
        self,
        enhanced_script: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Generate TTS for all chunks at SENTENCE level.

        Each sentence gets its own audio file for precise control over:
        - Intensity boosting per sentence (based on strong words + tension)
        - Pauses only at sentence boundaries (not within)
        - Emotion-responsive voice parameters (speed, emphasis)
        - Multi-speaker support with different voices

        Args:
            enhanced_script: The enhanced script dictionary

        Returns:
            List of generated audio file metadata with sentence info and intensity
        """
        audio_files = []

        # Generate hook sentences
        hook = enhanced_script.get("hook", {})
        if hook.get("text"):
            hook_sentences = split_into_sentences(hook["text"])
            hook_emotion = hook.get("emotion", "intrigue")
            hook_voice_id = hook.get("voice_id")
            hook_speaker = hook.get("speaker")
            print(f"\nGenerating hook ({len(hook_sentences)} sentences, emotion={hook_emotion})...")

            for sent_idx, sentence in enumerate(hook_sentences):
                filename = f"hook_sent_{sent_idx + 1}"
                # Calculate intensity for this sentence
                intensity = get_intensity_for_sentence(sentence, tension_level=3)
                is_emphasis = intensity > 0

                path = self.generate_speech(
                    sentence,
                    filename,
                    is_emphasis=is_emphasis,
                    emotion=hook_emotion,
                    voice_id=hook_voice_id,
                    speaker=hook_speaker
                )
                if path:
                    audio_files.append({
                        "type": "hook_sentence",
                        "sentence_idx": sent_idx,
                        "total_sentences": len(hook_sentences),
                        "path": path,
                        "text": sentence,
                        "emotion": hook_emotion,
                        "speaker": hook_speaker,
                        "voice_id": hook_voice_id,
                        "intensity_boost_percent": intensity
                    })
                    if intensity > 0:
                        print(f"    Sentence {sent_idx + 1}: +{intensity}% intensity")

        # Generate module chunk sentences
        modules = enhanced_script.get("modules", [])
        for module in modules:
            module_id = module.get("id", 0)
            chunks = module.get("chunks", [])
            print(f"\nGenerating Module {module_id}: {module.get('title', '')}")

            for chunk_idx, chunk in enumerate(chunks):
                text = chunk.get("text", "")
                if not text:
                    continue

                tension_level = chunk.get("tension_level", 2)
                chunk_emotion = chunk.get("emotion", "neutral")
                chunk_voice_id = chunk.get("voice_id")
                chunk_speaker = chunk.get("speaker")
                sentences = split_into_sentences(text)
                print(f"  Chunk {chunk_idx + 1}: {len(sentences)} sentences (tension={tension_level}, emotion={chunk_emotion})")

                for sent_idx, sentence in enumerate(sentences):
                    filename = f"module_{module_id}_chunk_{chunk_idx + 1}_sent_{sent_idx + 1}"

                    # Calculate intensity based on tension level and strong words
                    intensity = get_intensity_for_sentence(sentence, tension_level)
                    is_emphasis = intensity > 0

                    path = self.generate_speech(
                        sentence,
                        filename,
                        is_emphasis=is_emphasis,
                        emotion=chunk_emotion,
                        voice_id=chunk_voice_id,
                        speaker=chunk_speaker
                    )
                    if path:
                        audio_files.append({
                            "type": "chunk_sentence",
                            "module_id": module_id,
                            "chunk_idx": chunk_idx,
                            "sentence_idx": sent_idx,
                            "total_sentences": len(sentences),
                            "path": path,
                            "text": sentence,
                            "emotion": chunk_emotion,
                            "speaker": chunk_speaker,
                            "voice_id": chunk_voice_id,
                            "tension_level": tension_level,
                            "intensity_boost_percent": intensity,
                            "module_title": module.get("title", "")
                        })
                        if intensity > 0:
                            print(f"      Sent {sent_idx + 1}: +{intensity}% intensity")

        return audio_files

    def generate_all_chunks_sentence_level_multi_speaker(
        self,
        enhanced_script: Dict[str, Any],
        speaker_voice_map: Optional[Dict[str, str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate TTS for multi-speaker scripts at SENTENCE level.

        This method handles scripts with multiple speakers, using different
        voice IDs for each speaker role.

        Args:
            enhanced_script: The enhanced script dictionary with speaker assignments
            speaker_voice_map: Optional mapping of speaker role -> voice_id
                              If not provided, uses voice_id from script or defaults

        Returns:
            List of generated audio file metadata
        """
        if speaker_voice_map:
            print(f"[TTSNarrator] Multi-speaker mode with {len(speaker_voice_map)} speakers")
            for speaker, voice in speaker_voice_map.items():
                print(f"    {speaker}: {voice}")

        # Use the standard sentence-level generation, which already handles
        # voice_id and speaker from the script
        return self.generate_all_chunks_sentence_level(enhanced_script)


if __name__ == "__main__":
    # Initialize narrator (uses MiniMax Speech-01-HD)
    narrator = TTSNarrator()

    # Test with sample text
    test_text = "Welcome to the podcast. Today we explore a remarkable story of courage and determination."
    path = narrator.generate_speech(test_text, "test_minimax_voice")
    print(f"Generated: {path}")
    print("\nMiniMax TTS test complete. Listen to the output to verify.")
