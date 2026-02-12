"""
Audio Mixer Utility

Combines TTS voice audio with background music using pydub.
Now supports audio design metadata for dynamic vocal intensity, pacing, and transitions.
"""

import json
from pydub import AudioSegment
from pathlib import Path
from typing import Dict, List, Optional, Any


class AudioMixer:
    def __init__(self, output_dir: str = None):
        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            self.output_dir = Path(__file__).parent.parent / "Output" / "audio"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Audio design metadata
        self.design_metadata = None

    def load_audio(self, path: str) -> AudioSegment:
        """Load an audio file."""
        return AudioSegment.from_file(path)

    def load_design_metadata(self, metadata_path: str = None) -> dict:
        """
        Load audio design metadata from JSON file.

        Args:
            metadata_path: Path to audio_design_metadata.json

        Returns:
            Metadata dictionary or None if not found
        """
        if metadata_path is None:
            metadata_path = self.output_dir / "audio_design_metadata.json"

        metadata_path = Path(metadata_path)
        if metadata_path.exists():
            with open(metadata_path, "r") as f:
                self.design_metadata = json.load(f)
            print(f"  Loaded audio design metadata from: {metadata_path}")
            return self.design_metadata
        else:
            print(f"  Warning: Audio design metadata not found at {metadata_path}")
            return None

    def adjust_volume(self, audio: AudioSegment, db_change: float) -> AudioSegment:
        """Adjust volume by decibels."""
        return audio + db_change

    def apply_intensity_boost(self, audio: AudioSegment, boost_percent: float) -> AudioSegment:
        """
        Apply vocal intensity boost based on percentage.

        Args:
            audio: Audio segment to boost
            boost_percent: Percentage boost (0-120%)

        Returns:
            Boosted audio segment

        UPDATED dB mapping for 100-120% range:
            50% boost   -> ~3.1 dB (moderate tension)
            100% boost  -> ~6.25 dB (critical moments)
            110% boost  -> ~6.9 dB (peak critical)
            120% boost  -> ~7.5 dB (maximum peak with keywords)
        """
        if boost_percent <= 0:
            return audio

        # Updated conversion for 100-120% intensity range
        # Formula: dB = percent * 0.0625 (linear scaling)
        # This gives us: 50%=3.1dB, 100%=6.25dB, 110%=6.9dB, 120%=7.5dB
        db_boost = boost_percent * 0.0625

        print(f"      Applying {boost_percent}% intensity boost (+{db_boost:.1f}dB)")
        return audio + db_boost

    def fade_in(self, audio: AudioSegment, duration_ms: int = 2000) -> AudioSegment:
        """Apply fade in effect."""
        return audio.fade_in(duration_ms)

    def fade_out(self, audio: AudioSegment, duration_ms: int = 2000) -> AudioSegment:
        """Apply fade out effect."""
        return audio.fade_out(duration_ms)

    def crossfade(self, audio1: AudioSegment, audio2: AudioSegment, duration_ms: int = 1000) -> AudioSegment:
        """Crossfade between two audio segments."""
        return audio1.append(audio2, crossfade=duration_ms)

    def overlay_bgm(self, voice: AudioSegment, bgm: AudioSegment, bgm_volume_db: float = -18) -> AudioSegment:
        """
        Overlay background music under voice.

        Args:
            voice: Voice audio segment
            bgm: Background music audio segment
            bgm_volume_db: Volume adjustment for BGM (default -18dB)

        Returns:
            Mixed audio segment
        """
        # Adjust BGM volume
        bgm_adjusted = self.adjust_volume(bgm, bgm_volume_db)

        # Loop BGM if it's shorter than voice
        if len(bgm_adjusted) < len(voice):
            loops_needed = (len(voice) // len(bgm_adjusted)) + 1
            bgm_adjusted = bgm_adjusted * loops_needed

        # Trim BGM to voice length
        bgm_adjusted = bgm_adjusted[:len(voice)]

        # Add fade in/out to BGM
        bgm_adjusted = self.fade_in(bgm_adjusted, 1000)
        bgm_adjusted = self.fade_out(bgm_adjusted, 2000)

        # Overlay
        return voice.overlay(bgm_adjusted)

    def get_chunk_metadata(self, module_id: int, chunk_idx: int) -> Optional[dict]:
        """
        Get metadata for a specific chunk from audio design metadata.

        Args:
            module_id: Module ID (1-based)
            chunk_idx: Chunk index within module (0-based)

        Returns:
            Chunk metadata dict or None
        """
        if not self.design_metadata:
            return None

        for module in self.design_metadata.get("modules", []):
            if module.get("id") == module_id:
                for chunk in module.get("chunks", []):
                    if chunk.get("chunk_idx") == chunk_idx:
                        return chunk
        return None

    def get_module_metadata(self, module_id: int) -> Optional[dict]:
        """
        Get metadata for a specific module.

        Args:
            module_id: Module ID (1-based)

        Returns:
            Module metadata dict or None
        """
        if not self.design_metadata:
            return None

        for module in self.design_metadata.get("modules", []):
            if module.get("id") == module_id:
                return module
        return None

    def get_transition_metadata(self, from_module: int, to_module: int) -> Optional[dict]:
        """
        Get transition metadata between two modules.

        Args:
            from_module: Source module ID
            to_module: Target module ID (or None for final)

        Returns:
            Transition metadata dict or None
        """
        if not self.design_metadata:
            return None

        for trans in self.design_metadata.get("module_transitions", []):
            if trans.get("from_module") == from_module and trans.get("to_module") == to_module:
                return trans
        return None

    def get_sentence_metadata(self, module_id: int, chunk_idx: int) -> List[dict]:
        """
        Get sentence-level metadata for a specific chunk.

        Args:
            module_id: Module ID (1-based)
            chunk_idx: Chunk index within module (0-based)

        Returns:
            List of sentence metadata dicts or empty list
        """
        chunk_meta = self.get_chunk_metadata(module_id, chunk_idx)
        if chunk_meta:
            return chunk_meta.get("sentences", [])
        return []

    def concatenate_sentences(
        self,
        sentence_audios: List[AudioSegment],
        pause_between_ms: int = 350
    ) -> AudioSegment:
        """
        Concatenate sentence audio segments with brief pauses between them.

        Pauses are ONLY at sentence boundaries, not within sentences.

        Args:
            sentence_audios: List of sentence AudioSegment objects
            pause_between_ms: Pause between sentences (default: 350ms)

        Returns:
            Combined audio segment
        """
        if not sentence_audios:
            return AudioSegment.empty()

        result = sentence_audios[0]

        for sentence in sentence_audios[1:]:
            pause = AudioSegment.silent(duration=pause_between_ms)
            result = result + pause + sentence

        return result

    def mix_sentences_for_chunk(
        self,
        sentence_files: List[dict],
        chunk_metadata: dict = None
    ) -> AudioSegment:
        """
        Mix sentence-level audio files for a single chunk.

        Applies:
        - Per-sentence intensity boost (from TTS metadata or chunk metadata)
        - Brief pauses between sentences (350ms)

        Args:
            sentence_files: List of sentence audio file metadata (with intensity_boost_percent)
            chunk_metadata: Optional chunk metadata (fallback for intensity)

        Returns:
            Combined chunk audio with intensity and pacing applied
        """
        if not sentence_files:
            return AudioSegment.empty()

        # Default pause between sentences
        pause_between = 350

        # Process each sentence with its own intensity
        processed_sentences = []
        for sent_file in sentence_files:
            sent_audio = self.load_audio(sent_file["path"])

            # Get intensity from TTS metadata (per-sentence) or fallback to chunk metadata
            intensity = sent_file.get("intensity_boost_percent", 0)
            if intensity == 0 and chunk_metadata:
                intensity = chunk_metadata.get("vocal_parameters", {}).get("intensity_boost_percent", 0)

            # Apply intensity boost to ENTIRE sentence
            if intensity > 0:
                sent_audio = self.apply_intensity_boost(sent_audio, intensity)

            processed_sentences.append(sent_audio)

        # Concatenate with brief pauses between sentences
        return self.concatenate_sentences(processed_sentences, pause_between_ms=pause_between)

    def concatenate_with_dynamic_pauses(
        self,
        segments: List[AudioSegment],
        chunk_metadata: List[dict],
        default_pause_ms: int = 800
    ) -> AudioSegment:
        """
        Concatenate audio segments (chunks) with dynamic pauses at CHUNK boundaries.

        Note: This is for chunk-level concatenation. For sentence-level,
        use concatenate_sentences() with shorter pauses.

        Args:
            segments: List of AudioSegment objects (processed chunks)
            chunk_metadata: List of chunk metadata dicts (parallel to segments)
            default_pause_ms: Default pause at chunk boundaries (800ms)

        Returns:
            Combined audio segment
        """
        if not segments:
            return AudioSegment.empty()

        result = segments[0]

        for i, segment in enumerate(segments[1:], 1):
            # Get pause duration from metadata (chunk boundary pause)
            if i - 1 < len(chunk_metadata) and chunk_metadata[i - 1]:
                meta = chunk_metadata[i - 1]
                # Use pause_after_chunk_ms (new field) or fall back to pause_after_ms (legacy)
                pause_ms = meta.get("vocal_parameters", {}).get("pause_after_chunk_ms",
                           meta.get("vocal_parameters", {}).get("pause_after_ms", default_pause_ms))
            else:
                pause_ms = default_pause_ms

            pause = AudioSegment.silent(duration=pause_ms)
            result = result + pause + segment

        return result

    def mix_podcast(
        self,
        tts_files: list,
        bgm_files: list,
        output_filename: str = "final_enhanced",
        use_design_metadata: bool = True
    ) -> str:
        """
        Mix TTS voice files with background music to create final podcast.
        Uses audio design metadata for dynamic intensity, pacing, and transitions.

        Args:
            tts_files: List of TTS file metadata (with 'path', 'module_id', etc.)
            bgm_files: List of BGM file metadata (with 'path', 'module_id', etc.)
            output_filename: Name for output file
            use_design_metadata: Whether to apply audio design metadata

        Returns:
            Path to final mixed audio file
        """
        print("\n" + "=" * 50)
        print("MIXING PODCAST AUDIO")
        print("=" * 50)

        # Load audio design metadata if requested
        if use_design_metadata:
            self.load_design_metadata()

        # Create BGM lookup by module ID
        bgm_lookup = {bgm["module_id"]: bgm["path"] for bgm in bgm_files}

        # Separate hook and chunks
        hook_tts = None
        module_chunks = {}  # module_id -> list of TTS segments

        for tts in tts_files:
            if tts["type"] == "hook":
                hook_tts = tts
            else:
                module_id = tts["module_id"]
                if module_id not in module_chunks:
                    module_chunks[module_id] = []
                module_chunks[module_id].append(tts)

        # Sort chunks within each module
        for module_id in module_chunks:
            module_chunks[module_id].sort(key=lambda x: x["chunk_idx"])

        mixed_segments = []
        module_ids = sorted(module_chunks.keys())

        # Process hook
        if hook_tts:
            print("\n  Processing hook...")
            hook_audio = self.load_audio(hook_tts["path"])

            # Apply hook intensity boost from metadata
            if self.design_metadata and self.design_metadata.get("hook"):
                hook_meta = self.design_metadata["hook"]
                boost = hook_meta.get("vocal_parameters", {}).get("intensity_boost_percent", 0)
                if boost > 0:
                    hook_audio = self.apply_intensity_boost(hook_audio, boost)

                pause_after = hook_meta.get("vocal_parameters", {}).get("pause_after_ms", 2000)
            else:
                pause_after = 1500

            # Add dramatic pause after hook
            hook_audio = hook_audio + AudioSegment.silent(duration=pause_after)
            mixed_segments.append(hook_audio)
            print(f"    Hook processed with {pause_after}ms pause after")

        # Process each module
        for module_idx, module_id in enumerate(module_ids):
            print(f"\n  Processing Module {module_id}...")
            chunks = module_chunks[module_id]
            module_meta = self.get_module_metadata(module_id)

            if module_meta:
                print(f"    Theme: {module_meta.get('theme_group', 'unknown')}")
                print(f"    BGM emotion: {module_meta.get('bgm_emotion', 'neutral')}")
                print(f"    BGM intensity: {module_meta.get('bgm_intensity', 'medium')}")

            # Process chunks with intensity and pacing
            module_voice_segments = []
            chunk_metadata_list = []

            for chunk in chunks:
                chunk_idx = chunk["chunk_idx"]
                chunk_audio = self.load_audio(chunk["path"])
                chunk_meta = self.get_chunk_metadata(module_id, chunk_idx)

                # Apply intensity boost
                if chunk_meta:
                    boost = chunk_meta.get("vocal_parameters", {}).get("intensity_boost_percent", 0)
                    is_critical = chunk_meta.get("is_critical", False)

                    if boost > 0:
                        chunk_audio = self.apply_intensity_boost(chunk_audio, boost)

                    if is_critical:
                        print(f"    Chunk {chunk_idx}: CRITICAL (tension={chunk_meta.get('tension_level')}, boost={boost}%)")
                    else:
                        print(f"    Chunk {chunk_idx}: normal (tension={chunk_meta.get('tension_level', '?')})")

                module_voice_segments.append(chunk_audio)
                chunk_metadata_list.append(chunk_meta)

            # Combine chunks with dynamic pauses
            if self.design_metadata:
                module_voice = self.concatenate_with_dynamic_pauses(
                    module_voice_segments,
                    chunk_metadata_list,
                    default_pause_ms=300
                )
            else:
                # Fallback to fixed pauses
                module_voice = self._concatenate_with_pause(module_voice_segments, pause_ms=300)

            # Get BGM for this module
            bgm_volume = self.design_metadata.get("global_parameters", {}).get("bgm_base_volume_db", -18) if self.design_metadata else -18

            if module_id in bgm_lookup:
                bgm_audio = self.load_audio(bgm_lookup[module_id])
                # Mix voice with BGM
                module_mixed = self.overlay_bgm(module_voice, bgm_audio, bgm_volume_db=bgm_volume)
                print(f"    Mixed with BGM at {bgm_volume}dB")
            else:
                module_mixed = module_voice
                print(f"    No BGM available for module {module_id}")

            # Get transition metadata for pause after this module
            next_module = module_ids[module_idx + 1] if module_idx + 1 < len(module_ids) else None
            trans_meta = self.get_transition_metadata(module_id, next_module)

            if trans_meta:
                transition_pause = trans_meta.get("duration_ms", 1000)
                print(f"    Transition to next: {trans_meta.get('bgm_transition', 'crossfade')} ({transition_pause}ms)")
            else:
                transition_pause = 1000 if next_module else 0

            # Add transition pause
            if transition_pause > 0:
                module_mixed = module_mixed + AudioSegment.silent(duration=transition_pause)

            mixed_segments.append(module_mixed)

        # Combine all segments with crossfades
        print("\n  Combining all segments...")
        final_audio = AudioSegment.empty()

        for i, segment in enumerate(mixed_segments):
            if i == 0:
                final_audio = segment
            else:
                # Get crossfade duration from transition metadata
                if i == 1:
                    # Hook to Module 1 - use standard crossfade
                    crossfade_ms = 500
                else:
                    # Module to Module transitions
                    from_module = module_ids[i - 2] if i >= 2 else 1
                    to_module = module_ids[i - 1] if i >= 1 and i - 1 < len(module_ids) else None
                    trans_meta = self.get_transition_metadata(from_module, to_module)
                    crossfade_ms = min(trans_meta.get("duration_ms", 500) // 3, 800) if trans_meta else 500

                # Apply crossfade
                final_audio = self.crossfade(final_audio, segment, duration_ms=crossfade_ms)

        # Final fadeout
        final_trans = self.get_transition_metadata(module_ids[-1] if module_ids else 4, None)
        if final_trans and final_trans.get("transition_type") == "fade_out":
            fadeout_ms = final_trans.get("duration_ms", 3000)
            print(f"  Applying final fadeout ({fadeout_ms}ms)")
            final_audio = self.fade_out(final_audio, fadeout_ms)

        # Final processing
        print("\n  Applying final processing...")
        # Normalize overall volume
        final_audio = final_audio.normalize()

        # Export
        output_path = self.output_dir / f"{output_filename}.mp3"
        print(f"  Exporting to: {output_path}")
        final_audio.export(output_path, format="mp3", bitrate="192k")

        # Print summary
        duration_sec = len(final_audio) / 1000
        print(f"\n  Final duration: {duration_sec:.1f}s ({duration_sec/60:.1f} minutes)")
        print("=" * 50)

        return str(output_path)

    def mix_podcast_sentence_level(
        self,
        tts_files: list,
        bgm_files: list,
        output_filename: str = "final_enhanced_v2",
        use_design_metadata: bool = True
    ) -> str:
        """
        Mix TTS voice files with BGM using SENTENCE-LEVEL processing.

        Key differences from mix_podcast():
        - Processes sentence-level audio files (module_X_chunk_Y_sent_Z.wav)
        - Applies intensity boost to entire sentences
        - Places pauses only at sentence boundaries (400ms) and chunk boundaries (800ms)

        Args:
            tts_files: List of sentence-level TTS metadata
            bgm_files: List of BGM file metadata
            output_filename: Name for output file
            use_design_metadata: Whether to apply audio design metadata

        Returns:
            Path to final mixed audio file
        """
        print("\n" + "=" * 50)
        print("MIXING PODCAST AUDIO (Sentence-Level)")
        print("=" * 50)

        # Load audio design metadata
        if use_design_metadata:
            self.load_design_metadata()

        # Create BGM lookup by module ID
        bgm_lookup = {bgm["module_id"]: bgm["path"] for bgm in bgm_files}

        # Organize TTS files by structure
        hook_sentences = []
        module_chunks = {}  # module_id -> chunk_idx -> [sentences]

        for tts in tts_files:
            if tts["type"] == "hook_sentence":
                hook_sentences.append(tts)
            elif tts["type"] == "chunk_sentence":
                module_id = tts["module_id"]
                chunk_idx = tts["chunk_idx"]

                if module_id not in module_chunks:
                    module_chunks[module_id] = {}
                if chunk_idx not in module_chunks[module_id]:
                    module_chunks[module_id][chunk_idx] = []

                module_chunks[module_id][chunk_idx].append(tts)

        # Sort sentences within each chunk
        hook_sentences.sort(key=lambda x: x["sentence_idx"])
        for module_id in module_chunks:
            for chunk_idx in module_chunks[module_id]:
                module_chunks[module_id][chunk_idx].sort(key=lambda x: x["sentence_idx"])

        mixed_segments = []
        module_ids = sorted(module_chunks.keys())

        # Process hook
        if hook_sentences:
            print(f"\n  Processing hook ({len(hook_sentences)} sentences)...")
            hook_audio = self._process_hook_sentences(hook_sentences)
            mixed_segments.append(hook_audio)

        # Process each module
        for module_idx, module_id in enumerate(module_ids):
            print(f"\n  Processing Module {module_id}...")
            chunk_indices = sorted(module_chunks[module_id].keys())
            module_meta = self.get_module_metadata(module_id)

            if module_meta:
                print(f"    Theme: {module_meta.get('theme_group', 'unknown')}")
                print(f"    BGM: {module_meta.get('bgm_emotion', 'neutral')} ({module_meta.get('bgm_intensity', 'medium')})")

            # Process chunks
            processed_chunks = []
            chunk_metadata_list = []

            for chunk_idx in chunk_indices:
                sentences = module_chunks[module_id][chunk_idx]
                chunk_meta = self.get_chunk_metadata(module_id, chunk_idx)

                print(f"    Chunk {chunk_idx}: {len(sentences)} sentences", end="")
                if chunk_meta and chunk_meta.get("is_critical"):
                    print(f" [CRITICAL: tension={chunk_meta.get('tension_level')}, boost={chunk_meta.get('vocal_parameters', {}).get('intensity_boost_percent', 0)}%]")
                else:
                    print("")

                # Mix sentences for this chunk
                chunk_audio = self.mix_sentences_for_chunk(sentences, chunk_meta or {})
                processed_chunks.append(chunk_audio)
                chunk_metadata_list.append(chunk_meta)

            # Combine chunks with pauses at chunk boundaries
            module_voice = self.concatenate_with_dynamic_pauses(
                processed_chunks,
                chunk_metadata_list,
                default_pause_ms=800
            )

            # Mix with BGM
            bgm_volume = self.design_metadata.get("global_parameters", {}).get("bgm_base_volume_db", -18) if self.design_metadata else -18

            if module_id in bgm_lookup:
                bgm_audio = self.load_audio(bgm_lookup[module_id])
                module_mixed = self.overlay_bgm(module_voice, bgm_audio, bgm_volume_db=bgm_volume)
                print(f"    Mixed with BGM at {bgm_volume}dB")
            else:
                module_mixed = module_voice
                print(f"    No BGM available")

            # Add transition pause
            next_module = module_ids[module_idx + 1] if module_idx + 1 < len(module_ids) else None
            trans_meta = self.get_transition_metadata(module_id, next_module)
            transition_pause = trans_meta.get("duration_ms", 1000) if trans_meta else 1000

            if transition_pause > 0 and next_module:
                module_mixed = module_mixed + AudioSegment.silent(duration=transition_pause)

            mixed_segments.append(module_mixed)

        # Combine all segments
        print("\n  Combining all segments...")
        final_audio = AudioSegment.empty()

        for i, segment in enumerate(mixed_segments):
            if i == 0:
                final_audio = segment
            else:
                crossfade_ms = 500
                final_audio = self.crossfade(final_audio, segment, duration_ms=crossfade_ms)

        # Final fadeout
        final_trans = self.get_transition_metadata(module_ids[-1] if module_ids else 4, None)
        if final_trans and final_trans.get("transition_type") == "fade_out":
            fadeout_ms = final_trans.get("duration_ms", 3000)
            print(f"  Applying final fadeout ({fadeout_ms}ms)")
            final_audio = self.fade_out(final_audio, fadeout_ms)

        # Normalize and export
        final_audio = final_audio.normalize()

        output_path = self.output_dir / f"{output_filename}.mp3"
        print(f"  Exporting to: {output_path}")
        final_audio.export(output_path, format="mp3", bitrate="192k")

        duration_sec = len(final_audio) / 1000
        print(f"\n  Final duration: {duration_sec:.1f}s ({duration_sec/60:.1f} minutes)")
        print("=" * 50)

        return str(output_path)

    def _process_hook_sentences(self, hook_sentences: List[dict]) -> AudioSegment:
        """Process hook sentences with per-sentence intensity boost and 350ms pauses."""
        # Get hook metadata for pause after
        hook_meta = self.design_metadata.get("hook", {}) if self.design_metadata else {}
        pause_after = hook_meta.get("vocal_parameters", {}).get("pause_after_ms", 2000)

        # Process each sentence with its own intensity
        processed = []
        for sent in hook_sentences:
            sent_audio = self.load_audio(sent["path"])

            # Get per-sentence intensity from TTS metadata
            intensity = sent.get("intensity_boost_percent", 0)
            if intensity > 0:
                sent_audio = self.apply_intensity_boost(sent_audio, intensity)

            processed.append(sent_audio)

        # Concatenate with 350ms pauses between sentences
        hook_audio = self.concatenate_sentences(processed, pause_between_ms=350)

        # Add pause after hook
        hook_audio = hook_audio + AudioSegment.silent(duration=pause_after)
        print(f"    Hook processed with 350ms sentence pauses, {pause_after}ms pause after")

        return hook_audio

    def _concatenate_with_pause(self, segments: list, pause_ms: int = 500) -> AudioSegment:
        """
        Legacy method: Concatenate audio segments with fixed pauses.
        """
        if not segments:
            return AudioSegment.empty()

        pause = AudioSegment.silent(duration=pause_ms)
        result = segments[0]

        for segment in segments[1:]:
            result = result + pause + segment

        return result

    def mix_module_preview(
        self,
        module_id: int,
        tts_files: list,
        bgm_path: str = None,
        output_filename: str = None
    ) -> str:
        """
        Generate a preview for a single module with audio design metadata applied.

        Args:
            module_id: Module ID to preview
            tts_files: List of TTS file metadata for this module
            bgm_path: Optional BGM file path
            output_filename: Output filename (default: module_X_preview)

        Returns:
            Path to preview file
        """
        print(f"\n  Generating preview for Module {module_id}...")

        # Load metadata
        self.load_design_metadata()
        module_meta = self.get_module_metadata(module_id)

        # Filter TTS files for this module
        module_tts = [t for t in tts_files if t.get("module_id") == module_id]
        module_tts.sort(key=lambda x: x["chunk_idx"])

        if not module_tts:
            print(f"    Error: No TTS files found for module {module_id}")
            return None

        # Process chunks
        voice_segments = []
        chunk_metadata_list = []

        for tts in module_tts:
            chunk_idx = tts["chunk_idx"]
            chunk_audio = self.load_audio(tts["path"])
            chunk_meta = self.get_chunk_metadata(module_id, chunk_idx)

            # Apply intensity boost
            if chunk_meta:
                boost = chunk_meta.get("vocal_parameters", {}).get("intensity_boost_percent", 0)
                if boost > 0:
                    chunk_audio = self.apply_intensity_boost(chunk_audio, boost)

            voice_segments.append(chunk_audio)
            chunk_metadata_list.append(chunk_meta)

        # Combine with dynamic pauses
        module_voice = self.concatenate_with_dynamic_pauses(
            voice_segments,
            chunk_metadata_list,
            default_pause_ms=300
        )

        # Mix with BGM if available
        if bgm_path and Path(bgm_path).exists():
            bgm_audio = self.load_audio(bgm_path)
            bgm_volume = self.design_metadata.get("global_parameters", {}).get("bgm_base_volume_db", -18) if self.design_metadata else -18
            module_mixed = self.overlay_bgm(module_voice, bgm_audio, bgm_volume_db=bgm_volume)
        else:
            module_mixed = module_voice

        # Normalize
        module_mixed = module_mixed.normalize()

        # Export
        preview_dir = self.output_dir / "previews"
        preview_dir.mkdir(parents=True, exist_ok=True)

        if output_filename is None:
            output_filename = f"module_{module_id}_preview"

        output_path = preview_dir / f"{output_filename}.mp3"
        module_mixed.export(output_path, format="mp3", bitrate="192k")

        duration_sec = len(module_mixed) / 1000
        print(f"    Preview saved: {output_path} ({duration_sec:.1f}s)")

        return str(output_path)


if __name__ == "__main__":
    # Test
    mixer = AudioMixer()
    print("Audio mixer ready")

    # Test loading metadata
    metadata = mixer.load_design_metadata()
    if metadata:
        print(f"Loaded metadata for: {metadata.get('title')}")
        print(f"Modules: {len(metadata.get('modules', []))}")
