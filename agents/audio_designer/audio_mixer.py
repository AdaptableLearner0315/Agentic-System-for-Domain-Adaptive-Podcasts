"""
Audio Mixer
Author: Sarath

Combines TTS voice audio with background music using pydub.
Supports audio design metadata for dynamic vocal intensity, pacing, and transitions.

Quality improvements:
- Dynamic pause durations based on emotion (not hardcoded 350ms)
- Adaptive BGM volume based on emotion
- Guaranteed fadeout on endings
"""

import json
from pydub import AudioSegment
from pathlib import Path
from typing import Dict, List, Optional, Any

from config.emotion_voice_mapping import (
    get_emotion_voice_params,
    get_pause_durations,
    PAUSE_STYLE_DURATIONS
)


# Emotion-based BGM volume mapping (adaptive instead of hardcoded -18dB)
EMOTION_BGM_VOLUME = {
    "reflection": -20,      # Quieter for contemplation
    "melancholy": -20,      # Quieter for emotional moments
    "wonder": -18,          # Balanced
    "curiosity": -18,       # Balanced
    "intrigue": -17,        # Slightly more present
    "tension": -15,         # More present for drama
    "excitement": -14,      # Energetic
    "triumph": -12,         # Bold and present
    "liberation": -14,      # Freeing
    "mastery": -16,         # Authoritative
    "intensity": -14,       # Powerful
    "explosive_energy": -13,  # High energy
    "rebellion": -14,       # Raw
    "restlessness": -16,    # Edgy
    "experimentation": -17,  # Creative
    "neutral": -18,         # Default
}


def get_pause_for_emotion(emotion: str, pause_type: str = "between_sentences") -> int:
    """
    Get emotion-appropriate pause duration.

    Args:
        emotion: Emotion name (e.g., 'wonder', 'tension')
        pause_type: 'between_sentences' or 'after_chunk'

    Returns:
        Pause duration in milliseconds
    """
    voice_params = get_emotion_voice_params(emotion)
    pause_style = voice_params.get("pause_style", "normal")
    durations = get_pause_durations(pause_style)
    return durations.get(pause_type, 350)


def get_bgm_volume_for_emotion(emotion: str) -> int:
    """
    Get emotion-appropriate BGM volume.

    Args:
        emotion: Emotion name

    Returns:
        BGM volume in dB
    """
    return EMOTION_BGM_VOLUME.get(emotion.lower(), -18)


class AudioMixer:
    """
    Audio mixer for combining TTS and BGM with dynamic effects.

    Features:
    - Sentence-level intensity boosting
    - Dynamic pause insertion based on metadata
    - VAD-based ducking support
    - Crossfade transitions
    """

    def __init__(self, output_dir: Optional[str] = None):
        """
        Initialize the Audio Mixer.

        Args:
            output_dir: Output directory for mixed audio files
        """
        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            self.output_dir = Path(__file__).parent.parent.parent / "Output" / "audio"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Audio design metadata
        self.design_metadata = None

    def load_audio(self, path: str) -> AudioSegment:
        """Load an audio file."""
        return AudioSegment.from_file(path)

    def load_design_metadata(self, metadata_path: Optional[str] = None) -> Optional[dict]:
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

        dB mapping:
            50% boost   -> ~3.1 dB (moderate tension)
            100% boost  -> ~6.25 dB (critical moments)
            110% boost  -> ~6.9 dB (peak critical)
            120% boost  -> ~7.5 dB (maximum peak with keywords)
        """
        if boost_percent <= 0:
            return audio

        # Formula: dB = percent * 0.0625 (linear scaling)
        db_boost = boost_percent * 0.0625

        print(f"      Applying {boost_percent}% intensity boost (+{db_boost:.1f}dB)")
        return audio + db_boost

    def fade_in(self, audio: AudioSegment, duration_ms: int = 2000) -> AudioSegment:
        """Apply fade in effect."""
        return audio.fade_in(duration_ms)

    def fade_out(self, audio: AudioSegment, duration_ms: int = 2000) -> AudioSegment:
        """Apply fade out effect."""
        return audio.fade_out(duration_ms)

    def crossfade(
        self,
        audio1: AudioSegment,
        audio2: AudioSegment,
        duration_ms: int = 1000
    ) -> AudioSegment:
        """Crossfade between two audio segments."""
        return audio1.append(audio2, crossfade=duration_ms)

    def overlay_bgm(
        self,
        voice: AudioSegment,
        bgm: AudioSegment,
        bgm_volume_db: float = -18
    ) -> AudioSegment:
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

    def get_transition_metadata(
        self,
        from_module: int,
        to_module: Optional[int]
    ) -> Optional[dict]:
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

    def concatenate_sentences(
        self,
        sentence_audios: List[AudioSegment],
        pause_between_ms: int = 350,
        emotion: Optional[str] = None
    ) -> AudioSegment:
        """
        Concatenate sentence audio segments with brief pauses between them.

        Pauses are ONLY at sentence boundaries, not within sentences.
        If emotion is provided, uses emotion-appropriate pause durations
        instead of the default 350ms.

        Args:
            sentence_audios: List of sentence AudioSegment objects
            pause_between_ms: Pause between sentences (default: 350ms, ignored if emotion provided)
            emotion: Optional emotion for dynamic pause duration

        Returns:
            Combined audio segment
        """
        if not sentence_audios:
            return AudioSegment.empty()

        # Use emotion-based pause if provided
        if emotion:
            pause_between_ms = get_pause_for_emotion(emotion, "between_sentences")

        result = sentence_audios[0]

        for sentence in sentence_audios[1:]:
            pause = AudioSegment.silent(duration=pause_between_ms)
            result = result + pause + sentence

        return result

    def mix_sentences_for_chunk(
        self,
        sentence_files: List[dict],
        chunk_metadata: Optional[dict] = None
    ) -> AudioSegment:
        """
        Mix sentence-level audio files for a single chunk.

        Applies:
        - Per-sentence intensity boost (from TTS metadata or chunk metadata)
        - Dynamic pauses between sentences based on emotion

        Args:
            sentence_files: List of sentence audio file metadata
            chunk_metadata: Optional chunk metadata (fallback for intensity and emotion)

        Returns:
            Combined chunk audio with intensity and pacing applied
        """
        if not sentence_files:
            return AudioSegment.empty()

        # Get emotion from sentence files or chunk metadata for dynamic pacing
        chunk_emotion = None
        if sentence_files and sentence_files[0].get("emotion"):
            chunk_emotion = sentence_files[0]["emotion"]
        elif chunk_metadata:
            chunk_emotion = chunk_metadata.get("emotion", "neutral")

        processed_sentences = []
        for sent_file in sentence_files:
            sent_audio = self.load_audio(sent_file["path"])

            # Get intensity from TTS metadata or fallback to chunk metadata
            intensity = sent_file.get("intensity_boost_percent", 0)
            if intensity == 0 and chunk_metadata:
                intensity = chunk_metadata.get("vocal_parameters", {}).get(
                    "intensity_boost_percent", 0
                )

            # Apply intensity boost to entire sentence
            if intensity > 0:
                sent_audio = self.apply_intensity_boost(sent_audio, intensity)

            processed_sentences.append(sent_audio)

        # Use emotion-based pause duration
        return self.concatenate_sentences(
            processed_sentences,
            emotion=chunk_emotion
        )

    def concatenate_with_dynamic_pauses(
        self,
        segments: List[AudioSegment],
        chunk_metadata: List[Optional[dict]],
        default_pause_ms: int = 800
    ) -> AudioSegment:
        """
        Concatenate audio segments (chunks) with dynamic pauses at CHUNK boundaries.

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
            if i - 1 < len(chunk_metadata) and chunk_metadata[i - 1]:
                meta = chunk_metadata[i - 1]
                pause_ms = meta.get("vocal_parameters", {}).get(
                    "pause_after_chunk_ms",
                    meta.get("vocal_parameters", {}).get("pause_after_ms", default_pause_ms)
                )
            else:
                pause_ms = default_pause_ms

            pause = AudioSegment.silent(duration=pause_ms)
            result = result + pause + segment

        return result

    def mix_podcast_sentence_level(
        self,
        tts_files: List[dict],
        bgm_files: List[dict],
        output_filename: str = "final_enhanced_v2",
        use_design_metadata: bool = True
    ) -> str:
        """
        Mix TTS voice files with BGM using SENTENCE-LEVEL processing.

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

        if use_design_metadata:
            self.load_design_metadata()

        # Create BGM lookup
        bgm_lookup = {bgm["module_id"]: bgm["path"] for bgm in bgm_files}

        # Organize TTS files
        hook_sentences = []
        module_chunks: Dict[int, Dict[int, List[dict]]] = {}

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

        # Sort
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

        # Process modules
        for module_idx, module_id in enumerate(module_ids):
            print(f"\n  Processing Module {module_id}...")
            chunk_indices = sorted(module_chunks[module_id].keys())
            module_meta = self.get_module_metadata(module_id)

            if module_meta:
                print(f"    Theme: {module_meta.get('theme_group', 'unknown')}")
                print(f"    BGM: {module_meta.get('bgm_emotion', 'neutral')} "
                      f"({module_meta.get('bgm_intensity', 'medium')})")

            processed_chunks = []
            chunk_metadata_list = []

            for chunk_idx in chunk_indices:
                sentences = module_chunks[module_id][chunk_idx]
                chunk_meta = self.get_chunk_metadata(module_id, chunk_idx)

                print(f"    Chunk {chunk_idx}: {len(sentences)} sentences", end="")
                if chunk_meta and chunk_meta.get("is_critical"):
                    print(f" [CRITICAL]")
                else:
                    print("")

                chunk_audio = self.mix_sentences_for_chunk(sentences, chunk_meta or {})
                processed_chunks.append(chunk_audio)
                chunk_metadata_list.append(chunk_meta)

            module_voice = self.concatenate_with_dynamic_pauses(
                processed_chunks, chunk_metadata_list, default_pause_ms=800
            )

            # Mix with BGM - use emotion-based volume if available
            bgm_volume = -18  # Default
            module_emotion = module_meta.get("bgm_emotion") if module_meta else None

            # Priority: emotion-based > metadata > default
            if module_emotion:
                bgm_volume = get_bgm_volume_for_emotion(module_emotion)
            elif self.design_metadata:
                bgm_volume = self.design_metadata.get("global_parameters", {}).get(
                    "bgm_base_volume_db", -18
                )

            if module_id in bgm_lookup:
                bgm_audio = self.load_audio(bgm_lookup[module_id])
                module_mixed = self.overlay_bgm(module_voice, bgm_audio, bgm_volume_db=bgm_volume)
                emotion_info = f" ({module_emotion})" if module_emotion else ""
                print(f"    Mixed with BGM at {bgm_volume}dB{emotion_info}")
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
                final_audio = self.crossfade(final_audio, segment, duration_ms=500)

        # ALWAYS apply final fadeout (guaranteed, not metadata-dependent)
        # This prevents abrupt endings which is a known quality issue
        final_trans = self.get_transition_metadata(module_ids[-1] if module_ids else 4, None)
        if final_trans and final_trans.get("transition_type") == "fade_out":
            fadeout_ms = final_trans.get("duration_ms", 3000)
        else:
            # Default fadeout even if no metadata
            fadeout_ms = 3000

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
        """Process hook sentences with per-sentence intensity boost and dynamic pacing."""
        hook_meta = self.design_metadata.get("hook", {}) if self.design_metadata else {}
        pause_after = hook_meta.get("vocal_parameters", {}).get("pause_after_ms", 2000)

        # Get hook emotion for dynamic pacing
        hook_emotion = None
        if hook_sentences and hook_sentences[0].get("emotion"):
            hook_emotion = hook_sentences[0]["emotion"]
        elif hook_meta:
            hook_emotion = hook_meta.get("emotion", "intrigue")

        processed = []
        for sent in hook_sentences:
            sent_audio = self.load_audio(sent["path"])

            intensity = sent.get("intensity_boost_percent", 0)
            if intensity > 0:
                sent_audio = self.apply_intensity_boost(sent_audio, intensity)

            processed.append(sent_audio)

        # Use emotion-based pause duration for hook sentences
        hook_audio = self.concatenate_sentences(processed, emotion=hook_emotion)
        hook_audio = hook_audio + AudioSegment.silent(duration=pause_after)

        pause_ms = get_pause_for_emotion(hook_emotion or "intrigue", "between_sentences")
        print(f"    Hook processed with {pause_ms}ms ({hook_emotion}) sentence pauses, {pause_after}ms pause after")

        return hook_audio


if __name__ == "__main__":
    mixer = AudioMixer()
    print("Audio mixer ready")

    metadata = mixer.load_design_metadata()
    if metadata:
        print(f"Loaded metadata for: {metadata.get('title')}")
        print(f"Modules: {len(metadata.get('modules', []))}")
