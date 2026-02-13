"""
Audio Designer Agent
Author: Sarath

Consolidated agent for all audio processing in the podcast enhancement system.

Coordinates:
- TTS Narrator: Text-to-speech generation
- Voice Style Engine: Module-specific voice processing
- BGM Generator: Background music generation
- Audio Mixer: Final audio mixing and production

This agent provides a unified interface for the entire audio pipeline.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional

from agents.base_agent import BaseAgent
from agents.audio_designer.tts_narrator import TTSNarrator
from agents.audio_designer.voice_style_engine import VoiceStyleEngine
from agents.audio_designer.bgm_generator import BGMGenerator
from agents.audio_designer.audio_mixer import AudioMixer


class AudioDesignerAgent(BaseAgent):
    """
    Consolidated audio processing agent.

    Coordinates TTS generation, voice styling, BGM generation,
    and final audio mixing into a unified workflow.
    """

    def __init__(self):
        """Initialize the Audio Designer Agent and all submodules."""
        super().__init__(name="AudioDesigner", output_category="audio")

        # Initialize submodules with appropriate directories
        self.tts_narrator = TTSNarrator(self.output_dir / "tts")
        self.voice_style_engine = VoiceStyleEngine()
        self.bgm_generator = BGMGenerator(self.output_dir / "bgm")
        self.audio_mixer = AudioMixer(self.output_dir)

        self.log("Initialized with all audio submodules")

    def generate_tts(
        self,
        enhanced_script: Dict[str, Any],
        sentence_level: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Generate TTS audio for the enhanced script.

        Args:
            enhanced_script: Enhanced script dictionary
            sentence_level: If True, generate sentence-level audio for precision

        Returns:
            List of TTS file metadata
        """
        self.log("Generating TTS audio...")

        if sentence_level:
            tts_files = self.tts_narrator.generate_all_chunks_sentence_level(enhanced_script)
        else:
            tts_files = self.tts_narrator.generate_all_chunks(enhanced_script)

        self.log(f"Generated {len(tts_files)} TTS files")
        return tts_files

    def generate_bgm(
        self,
        enhanced_script: Dict[str, Any],
        use_daisy_chain: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Generate background music for the script.

        Args:
            enhanced_script: Enhanced script dictionary
            use_daisy_chain: If True, use 9-segment daisy-chain BGM

        Returns:
            List of BGM file metadata
        """
        self.log("Generating background music...")

        if use_daisy_chain:
            bgm_files = self.bgm_generator.generate_all_segments(use_daisy_chain=True)
        else:
            modules = enhanced_script.get("modules", [])
            bgm_files = self.bgm_generator.generate_module_bgm(modules)

        self.log(f"Generated {len(bgm_files)} BGM files")
        return bgm_files

    def apply_voice_styles(
        self,
        tts_files: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Apply module-specific voice styles to TTS audio.

        Args:
            tts_files: List of TTS file metadata

        Returns:
            Updated list with styled audio paths
        """
        from pydub import AudioSegment

        self.log("Applying voice styles...")
        styled_files = []

        for tts in tts_files:
            # Determine style key
            if tts["type"] in ["hook", "hook_sentence"]:
                style_key = "hook"
            elif "module_id" in tts:
                style_key = self.voice_style_engine.get_style_for_module(tts["module_id"])
            else:
                style_key = None

            if style_key:
                # Load audio
                audio = AudioSegment.from_file(tts["path"])

                # Apply style
                styled_audio = self.voice_style_engine.apply_style(audio, style_key)

                # Save styled version
                styled_path = Path(tts["path"]).with_suffix(".styled.wav")
                styled_audio.export(styled_path, format="wav")

                # Update metadata
                tts["original_path"] = tts["path"]
                tts["path"] = str(styled_path)
                tts["style_applied"] = style_key

            styled_files.append(tts)

        self.log(f"Applied styles to {len(styled_files)} files")
        return styled_files

    def mix_final_audio(
        self,
        tts_files: List[Dict[str, Any]],
        bgm_files: List[Dict[str, Any]],
        output_filename: str = "final_podcast",
        sentence_level: bool = True
    ) -> str:
        """
        Mix TTS and BGM into final podcast audio.

        Args:
            tts_files: List of TTS file metadata
            bgm_files: List of BGM file metadata
            output_filename: Output filename
            sentence_level: If True, use sentence-level mixing

        Returns:
            Path to final mixed audio
        """
        self.log("Mixing final audio...")

        if sentence_level:
            output_path = self.audio_mixer.mix_podcast_sentence_level(
                tts_files,
                bgm_files,
                output_filename=output_filename
            )
        else:
            # Use the full mix_podcast method if available
            output_path = self.audio_mixer.mix_podcast_sentence_level(
                tts_files,
                bgm_files,
                output_filename=output_filename
            )

        self.log(f"Final audio: {output_path}")
        return output_path

    def process(
        self,
        enhanced_script: Dict[str, Any],
        generate_tts: bool = True,
        generate_bgm: bool = True,
        apply_styles: bool = True,
        mix_audio: bool = True,
        sentence_level: bool = True,
        use_daisy_chain_bgm: bool = False,
        output_filename: str = "final_podcast"
    ) -> Dict[str, Any]:
        """
        Run the complete audio processing pipeline.

        Args:
            enhanced_script: Enhanced script dictionary
            generate_tts: Whether to generate TTS audio
            generate_bgm: Whether to generate background music
            apply_styles: Whether to apply voice styles
            mix_audio: Whether to mix final audio
            sentence_level: Use sentence-level processing
            use_daisy_chain_bgm: Use 9-segment daisy-chain BGM
            output_filename: Output filename for final audio

        Returns:
            Dictionary with all processing results
        """
        self.log("=" * 50)
        self.log("AUDIO DESIGNER PIPELINE")
        self.log("=" * 50)

        results = {
            "tts_files": [],
            "bgm_files": [],
            "final_audio": None
        }

        # Step 1: Generate TTS
        if generate_tts:
            results["tts_files"] = self.generate_tts(enhanced_script, sentence_level)

        # Step 2: Apply voice styles
        if apply_styles and results["tts_files"]:
            results["tts_files"] = self.apply_voice_styles(results["tts_files"])

        # Step 3: Generate BGM
        if generate_bgm:
            results["bgm_files"] = self.generate_bgm(enhanced_script, use_daisy_chain_bgm)

        # Step 4: Mix final audio
        if mix_audio and results["tts_files"] and results["bgm_files"]:
            results["final_audio"] = self.mix_final_audio(
                results["tts_files"],
                results["bgm_files"],
                output_filename=output_filename,
                sentence_level=sentence_level
            )

        self.log("=" * 50)
        self.log("AUDIO PIPELINE COMPLETE")
        self.log("=" * 50)

        return results

    def generate_voice_only(
        self,
        enhanced_script: Dict[str, Any],
        output_filename: str = "voice_only"
    ) -> str:
        """
        Generate voice-only audio (no BGM).

        Args:
            enhanced_script: Enhanced script dictionary
            output_filename: Output filename

        Returns:
            Path to voice-only audio
        """
        self.log("Generating voice-only audio...")

        # Generate TTS
        tts_files = self.generate_tts(enhanced_script, sentence_level=True)

        # Apply styles
        tts_files = self.apply_voice_styles(tts_files)

        # Mix without BGM
        from pydub import AudioSegment

        # Combine all TTS in order
        combined = AudioSegment.empty()

        # Sort by type and index
        hook_files = [f for f in tts_files if f["type"] == "hook_sentence"]
        hook_files.sort(key=lambda x: x["sentence_idx"])

        chunk_files = [f for f in tts_files if f["type"] == "chunk_sentence"]
        chunk_files.sort(key=lambda x: (x["module_id"], x["chunk_idx"], x["sentence_idx"]))

        # Combine hook
        for f in hook_files:
            audio = AudioSegment.from_file(f["path"])
            combined = combined + audio + AudioSegment.silent(duration=350)

        # Add pause after hook
        combined = combined + AudioSegment.silent(duration=1500)

        # Combine chunks
        current_module = None
        for f in chunk_files:
            if current_module != f["module_id"]:
                if current_module is not None:
                    combined = combined + AudioSegment.silent(duration=1000)
                current_module = f["module_id"]

            audio = AudioSegment.from_file(f["path"])
            combined = combined + audio + AudioSegment.silent(duration=350)

        # Normalize and export
        combined = combined.normalize()
        output_path = self.output_dir / f"{output_filename}.mp3"
        combined.export(output_path, format="mp3", bitrate="192k")

        self.log(f"Voice-only audio: {output_path}")
        return str(output_path)


if __name__ == "__main__":
    import json

    # Test initialization
    agent = AudioDesignerAgent()

    # Test with minimal script
    test_script = {
        "hook": {
            "text": "This is a test hook sentence.",
            "emotion": "intrigue"
        },
        "modules": [
            {
                "id": 1,
                "title": "Test Module",
                "emotion_arc": "wonder -> curiosity",
                "chunks": [
                    {
                        "text": "This is a test chunk.",
                        "emotion": "wonder",
                        "tension_level": 2
                    }
                ]
            }
        ]
    }

    print("AudioDesignerAgent initialized successfully")
    print(f"Output directory: {agent.output_dir}")
