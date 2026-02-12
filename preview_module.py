"""
Generate preview audio for individual modules.
Uses audio design metadata for vocal intensity, pacing, and BGM mixing.
Allows user to review each module's TTS + BGM before final mixing.

Updated for sentence-level processing:
- Reads sentence-level TTS files (module_X_chunk_Y_sent_Z.wav)
- Applies intensity to entire sentences
- Places pauses only at sentence boundaries
"""

import os
import json
import argparse
from pathlib import Path
from dotenv import load_dotenv
from pydub import AudioSegment

load_dotenv()

from utils.audio_mixer import AudioMixer


class ModulePreviewer:
    def __init__(self, base_dir: str = None):
        self.base_dir = Path(base_dir) if base_dir else Path(__file__).parent
        self.tts_dir = self.base_dir / "Output" / "audio" / "tts"
        self.bgm_dir = self.base_dir / "Output" / "audio" / "bgm"
        self.preview_dir = self.base_dir / "Output" / "audio" / "previews"
        self.preview_dir.mkdir(parents=True, exist_ok=True)

        # Initialize audio mixer with design metadata support
        self.mixer = AudioMixer(output_dir=str(self.base_dir / "Output" / "audio"))
        self.mixer.load_design_metadata()

    def load_audio(self, path: str) -> AudioSegment:
        """Load an audio file."""
        return AudioSegment.from_file(path)

    def get_tts_files_for_module(self, module_id: int, sentence_level: bool = True) -> list:
        """Get list of TTS file metadata for a specific module."""
        tts_files = []

        if sentence_level:
            # Get sentence-level files (module_X_chunk_Y_sent_Z.wav)
            pattern = f"module_{module_id}_chunk_*_sent_*.wav"
            for tts_file in sorted(self.tts_dir.glob(pattern)):
                filename = tts_file.stem
                parts = filename.split("_")
                if len(parts) >= 6:
                    chunk_idx = int(parts[3]) - 1
                    sent_idx = int(parts[5]) - 1
                    tts_files.append({
                        "path": str(tts_file),
                        "type": "chunk_sentence",
                        "module_id": module_id,
                        "chunk_idx": chunk_idx,
                        "sentence_idx": sent_idx
                    })
        else:
            # Get chunk-level files (legacy: module_X_chunk_Y.wav)
            pattern = f"module_{module_id}_chunk_*.wav"
            for tts_file in sorted(self.tts_dir.glob(pattern)):
                filename = tts_file.stem
                if "_sent_" not in filename:  # Exclude sentence files
                    parts = filename.split("_")
                    if len(parts) >= 4:
                        chunk_idx = int(parts[3]) - 1
                        tts_files.append({
                            "path": str(tts_file),
                            "type": "chunk",
                            "module_id": module_id,
                            "chunk_idx": chunk_idx
                        })

        return sorted(tts_files, key=lambda x: (x.get("chunk_idx", 0), x.get("sentence_idx", 0)))

    def get_hook_sentence_files(self) -> list:
        """Get hook sentence-level TTS files."""
        hook_files = []
        for f in sorted(self.tts_dir.glob("hook_sent_*.wav")):
            filename = f.stem
            parts = filename.split("_")
            if len(parts) >= 3:
                sent_idx = int(parts[2]) - 1
                hook_files.append({
                    "path": str(f),
                    "type": "hook_sentence",
                    "sentence_idx": sent_idx
                })
        return sorted(hook_files, key=lambda x: x["sentence_idx"])

    def generate_hook_preview(self, sentence_level: bool = True, with_bgm: bool = True) -> str:
        """
        Generate preview for the hook.

        Args:
            sentence_level: Use sentence-level files (default: True)
            with_bgm: Add background music to hook (default: True)
        """
        print("\n" + "=" * 50)
        print("GENERATING HOOK PREVIEW")
        print("=" * 50)

        if sentence_level:
            # Use sentence-level files
            hook_sentences = self.get_hook_sentence_files()
            if not hook_sentences:
                # Fallback to single hook file
                hook_path = self.tts_dir / "hook.wav"
                if not hook_path.exists():
                    print(f"Error: No hook TTS files found")
                    return None
                sentence_level = False
            else:
                print(f"  Found {len(hook_sentences)} hook sentences")

        if sentence_level:
            # Process sentence-level hook
            hook_meta = self.mixer.design_metadata.get("hook", {}) if self.mixer.design_metadata else {}
            boost = hook_meta.get("vocal_parameters", {}).get("intensity_boost_percent", 20)

            processed_sentences = []
            for sent in hook_sentences:
                sent_audio = self.load_audio(sent["path"])

                # Strip silence from beginning and end of each sentence
                sent_audio = self._strip_silence(sent_audio)

                if boost > 0:
                    sent_audio = self.mixer.apply_intensity_boost(sent_audio, boost)
                processed_sentences.append(sent_audio)

            # Concatenate with NO pauses between sentences for seamless flow
            hook_audio = AudioSegment.empty()
            for sent_audio in processed_sentences:
                hook_audio = hook_audio + sent_audio

            print(f"  Applied {boost}% intensity boost, NO pauses between sentences")
        else:
            # Legacy chunk-level processing
            hook_path = self.tts_dir / "hook.wav"
            if not hook_path.exists():
                print(f"Error: Hook TTS not found at {hook_path}")
                return None

            hook_audio = self.load_audio(str(hook_path))

            if self.mixer.design_metadata and self.mixer.design_metadata.get("hook"):
                hook_meta = self.mixer.design_metadata["hook"]
                boost = hook_meta.get("vocal_parameters", {}).get("intensity_boost_percent", 0)

                if boost > 0:
                    print(f"  Applying {boost}% intensity boost")
                    hook_audio = self.mixer.apply_intensity_boost(hook_audio, boost)

        # Add BGM if requested
        if with_bgm:
            # Use module 1's BGM for the hook (wonder/intrigue theme)
            bgm_path = self.bgm_dir / "module_1_bgm.wav"
            if bgm_path.exists():
                print(f"  Adding BGM from module 1...")
                bgm_audio = self.load_audio(str(bgm_path))
                bgm_volume = -20  # Slightly lower for hook to keep focus on voice
                hook_audio = self.mixer.overlay_bgm(hook_audio, bgm_audio, bgm_volume_db=bgm_volume)
                print(f"  BGM volume: {bgm_volume}dB")
            else:
                print(f"  Warning: No BGM found at {bgm_path}")

        # Normalize and export
        hook_audio = hook_audio.normalize()

        output_path = self.preview_dir / "hook_preview.mp3"
        hook_audio.export(output_path, format="mp3", bitrate="192k")

        duration_sec = len(hook_audio) / 1000
        print(f"  Saved: {output_path} ({duration_sec:.1f}s)")
        print("=" * 50)

        return str(output_path)

    def _strip_silence(self, audio: AudioSegment, silence_thresh: int = -50, chunk_size: int = 10) -> AudioSegment:
        """
        Strip silence from beginning and end of audio.

        Args:
            audio: Audio segment to process
            silence_thresh: dB threshold for silence (default: -50dB)
            chunk_size: Size of chunks to analyze in ms (default: 10ms)
        """
        from pydub.silence import detect_leading_silence

        # Detect and trim leading silence
        start_trim = detect_leading_silence(audio, silence_threshold=silence_thresh, chunk_size=chunk_size)

        # Detect and trim trailing silence (reverse, detect leading, reverse back)
        end_trim = detect_leading_silence(audio.reverse(), silence_threshold=silence_thresh, chunk_size=chunk_size)

        # Apply trimming
        duration = len(audio)
        trimmed = audio[start_trim:duration - end_trim]

        return trimmed if len(trimmed) > 0 else audio

    def generate_module_preview(self, module_id: int, sentence_level: bool = True) -> str:
        """
        Generate preview for a specific module with:
        - Vocal intensity boosts based on tension levels
        - Dynamic pauses based on metadata
        - BGM overlay

        If sentence_level=True:
        - Processes sentence-level audio files
        - Applies intensity to entire sentences
        - Pauses only at sentence boundaries (400ms) and chunk boundaries (800ms)
        """
        print(f"\n" + "=" * 50)
        print(f"GENERATING MODULE {module_id} PREVIEW" + (" (Sentence-Level)" if sentence_level else ""))
        print("=" * 50)

        # Get TTS files for this module
        tts_files = self.get_tts_files_for_module(module_id, sentence_level=sentence_level)
        if not tts_files:
            # Try falling back to chunk-level if sentence-level not found
            if sentence_level:
                print(f"  No sentence-level files found, trying chunk-level...")
                tts_files = self.get_tts_files_for_module(module_id, sentence_level=False)
                sentence_level = False

        if not tts_files:
            print(f"Error: No TTS files found for module {module_id}")
            return None

        # Get module metadata
        module_meta = self.mixer.get_module_metadata(module_id)
        if module_meta:
            print(f"  Title: {module_meta.get('title', 'Unknown')}")
            print(f"  Theme: {module_meta.get('theme_group', 'unknown')}")
            print(f"  BGM Emotion: {module_meta.get('bgm_emotion', 'neutral')}")
            print(f"  BGM Intensity: {module_meta.get('bgm_intensity', 'medium')}")

        if sentence_level:
            # Sentence-level processing
            module_voice = self._process_module_sentence_level(module_id, tts_files)
        else:
            # Legacy chunk-level processing
            module_voice = self._process_module_chunk_level(module_id, tts_files)

        # Load and mix BGM
        bgm_path = self.bgm_dir / f"module_{module_id}_bgm.wav"
        if bgm_path.exists():
            print(f"  Mixing with BGM...")
            bgm_audio = self.load_audio(str(bgm_path))
            bgm_volume = -18
            if self.mixer.design_metadata:
                bgm_volume = self.mixer.design_metadata.get("global_parameters", {}).get("bgm_base_volume_db", -18)
            mixed_audio = self.mixer.overlay_bgm(module_voice, bgm_audio, bgm_volume_db=bgm_volume)
            print(f"    BGM volume: {bgm_volume}dB")
        else:
            print(f"  Warning: No BGM found at {bgm_path}")
            mixed_audio = module_voice

        # Normalize and export
        mixed_audio = mixed_audio.normalize()

        output_path = self.preview_dir / f"module_{module_id}_preview.mp3"
        mixed_audio.export(output_path, format="mp3", bitrate="192k")

        duration_sec = len(mixed_audio) / 1000
        print(f"\n  Saved: {output_path}")
        print(f"  Duration: {duration_sec:.1f}s ({duration_sec/60:.1f} minutes)")
        print("=" * 50)

        return str(output_path)

    def _process_module_sentence_level(self, module_id: int, tts_files: list) -> AudioSegment:
        """Process module with sentence-level files."""
        # Group by chunk
        chunks = {}
        for tts in tts_files:
            chunk_idx = tts["chunk_idx"]
            if chunk_idx not in chunks:
                chunks[chunk_idx] = []
            chunks[chunk_idx].append(tts)

        print(f"\n  Processing {len(chunks)} chunks with sentence-level audio...")

        processed_chunks = []
        chunk_metadata_list = []

        for chunk_idx in sorted(chunks.keys()):
            sentences = sorted(chunks[chunk_idx], key=lambda x: x["sentence_idx"])
            chunk_meta = self.mixer.get_chunk_metadata(module_id, chunk_idx)

            # Get intensity for this chunk (applies to all sentences)
            intensity = chunk_meta.get("vocal_parameters", {}).get("intensity_boost_percent", 0) if chunk_meta else 0
            is_critical = chunk_meta.get("is_critical", False) if chunk_meta else False
            tension = chunk_meta.get("tension_level", "?") if chunk_meta else "?"

            status = "CRITICAL" if is_critical else "normal"
            print(f"    Chunk {chunk_idx}: {len(sentences)} sentences | {status} | tension={tension} | boost={intensity}%")

            # Process sentences
            processed_sentences = []
            for sent in sentences:
                sent_audio = self.load_audio(sent["path"])
                if intensity > 0:
                    sent_audio = self.mixer.apply_intensity_boost(sent_audio, intensity)
                processed_sentences.append(sent_audio)

            # Concatenate sentences with brief pauses (400ms)
            chunk_audio = self.mixer.concatenate_sentences(processed_sentences, pause_between_ms=400)
            processed_chunks.append(chunk_audio)
            chunk_metadata_list.append(chunk_meta)

        # Combine chunks with pauses at chunk boundaries (800ms)
        print("\n  Combining chunks with pauses at chunk boundaries...")
        return self.mixer.concatenate_with_dynamic_pauses(
            processed_chunks,
            chunk_metadata_list,
            default_pause_ms=800
        )

    def _process_module_chunk_level(self, module_id: int, tts_files: list) -> AudioSegment:
        """Process module with legacy chunk-level files."""
        print(f"\n  Processing {len(tts_files)} chunks...")

        voice_segments = []
        chunk_metadata_list = []

        for tts in tts_files:
            chunk_idx = tts["chunk_idx"]
            chunk_audio = self.load_audio(tts["path"])
            chunk_meta = self.mixer.get_chunk_metadata(module_id, chunk_idx)

            if chunk_meta:
                boost = chunk_meta.get("vocal_parameters", {}).get("intensity_boost_percent", 0)
                is_critical = chunk_meta.get("is_critical", False)
                tension = chunk_meta.get("tension_level", "?")
                emotion = chunk_meta.get("emotion", "neutral")
                pause_after = chunk_meta.get("vocal_parameters", {}).get("pause_after_chunk_ms",
                              chunk_meta.get("vocal_parameters", {}).get("pause_after_ms", 300))

                if boost > 0:
                    chunk_audio = self.mixer.apply_intensity_boost(chunk_audio, boost)

                status = "CRITICAL" if is_critical else "normal"
                print(f"    Chunk {chunk_idx}: {status} | emotion={emotion} | tension={tension} | boost={boost}% | pause={pause_after}ms")
            else:
                print(f"    Chunk {chunk_idx}: no metadata")

            voice_segments.append(chunk_audio)
            chunk_metadata_list.append(chunk_meta)

        print("\n  Combining chunks with dynamic pauses...")
        return self.mixer.concatenate_with_dynamic_pauses(
            voice_segments,
            chunk_metadata_list,
            default_pause_ms=800
        )

    def generate_all_previews(self, sentence_level: bool = True) -> dict:
        """Generate previews for all modules with full audio design metadata."""
        results = {}

        # Generate hook preview
        hook_path = self.generate_hook_preview(sentence_level=sentence_level)
        if hook_path:
            results["hook"] = hook_path

        # Generate module previews (1-4)
        for module_id in range(1, 5):
            path = self.generate_module_preview(module_id, sentence_level=sentence_level)
            if path:
                results[f"module_{module_id}"] = path

        return results

    def print_design_summary(self):
        """Print a summary of the audio design metadata."""
        if not self.mixer.design_metadata:
            print("No audio design metadata loaded.")
            return

        meta = self.mixer.design_metadata
        print("\n" + "=" * 60)
        print("AUDIO DESIGN SUMMARY")
        print("=" * 60)

        print(f"\nTitle: {meta.get('title', 'Unknown')}")

        # Global parameters
        global_params = meta.get("global_parameters", {})
        print(f"\nGlobal Parameters:")
        print(f"  Critical boost: {global_params.get('critical_intensity_boost_percent', 35)}%")
        print(f"  Standard pause: {global_params.get('standard_pause_ms', 300)}ms")
        print(f"  Critical pause: {global_params.get('critical_pause_ms', 2500)}ms")
        print(f"  BGM volume: {global_params.get('bgm_base_volume_db', -18)}dB")

        # Modules summary
        print(f"\nModules:")
        for module in meta.get("modules", []):
            module_id = module.get("id")
            title = module.get("title", "Unknown")
            theme = module.get("theme_group", "unknown")
            bgm_emotion = module.get("bgm_emotion", "neutral")
            bgm_intensity = module.get("bgm_intensity", "medium")

            chunks = module.get("chunks", [])
            critical_count = sum(1 for c in chunks if c.get("is_critical", False))

            print(f"\n  Module {module_id}: {title}")
            print(f"    Theme: {theme} | BGM: {bgm_emotion} ({bgm_intensity})")
            print(f"    Chunks: {len(chunks)} | Critical: {critical_count}")

            # Show critical chunks
            for chunk in chunks:
                if chunk.get("is_critical"):
                    idx = chunk.get("chunk_idx")
                    emotion = chunk.get("emotion")
                    tension = chunk.get("tension_level")
                    boost = chunk.get("vocal_parameters", {}).get("intensity_boost_percent", 0)
                    pause = chunk.get("vocal_parameters", {}).get("pause_after_ms", 300)
                    print(f"      * Chunk {idx}: {emotion} (T{tension}) → +{boost}%, {pause}ms pause")

        # Summary stats
        summary = meta.get("summary", {})
        print(f"\nOverall Statistics:")
        print(f"  Total chunks: {summary.get('total_chunks', 0)}")
        print(f"  Critical chunks: {summary.get('critical_chunks', 0)} ({summary.get('critical_percentage', 0)}%)")
        print(f"  Peak keyword chunks: {summary.get('peak_keyword_chunks', 0)}")

        print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Generate preview audio for individual modules with audio design metadata"
    )
    parser.add_argument(
        "--module",
        type=int,
        choices=[1, 2, 3, 4],
        help="Generate preview for specific module (1-4)"
    )
    parser.add_argument(
        "--hook",
        action="store_true",
        help="Generate preview for hook only"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Generate previews for all modules"
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Print audio design metadata summary"
    )
    parser.add_argument(
        "--sentence-level",
        action="store_true",
        default=True,
        help="Use sentence-level processing (default: True)"
    )
    parser.add_argument(
        "--chunk-level",
        action="store_true",
        help="Use legacy chunk-level processing instead of sentence-level"
    )

    args = parser.parse_args()

    # Determine processing mode
    sentence_level = not args.chunk_level

    previewer = ModulePreviewer()

    if args.summary:
        previewer.print_design_summary()
    elif args.hook:
        previewer.generate_hook_preview(sentence_level=sentence_level)
    elif args.module:
        previewer.generate_module_preview(args.module, sentence_level=sentence_level)
    elif args.all:
        results = previewer.generate_all_previews(sentence_level=sentence_level)
        print("\n" + "=" * 60)
        print("ALL PREVIEWS GENERATED" + (" (Sentence-Level)" if sentence_level else ""))
        print("=" * 60)
        for name, path in results.items():
            print(f"  {name}: {path}")
        print("=" * 60)
    else:
        # Default: show summary and generate all
        previewer.print_design_summary()
        print("\n")
        results = previewer.generate_all_previews(sentence_level=sentence_level)
        print("\n" + "=" * 60)
        print("ALL PREVIEWS GENERATED" + (" (Sentence-Level)" if sentence_level else ""))
        print("=" * 60)
        for name, path in results.items():
            print(f"  {name}: {path}")
        print("=" * 60)


if __name__ == "__main__":
    main()
