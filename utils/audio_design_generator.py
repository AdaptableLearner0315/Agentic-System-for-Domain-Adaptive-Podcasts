"""
Audio Design Generator

Generates audio design metadata from enhanced script.
Computes vocal parameters (intensity, pacing) and BGM parameters (theme, transitions)
based on emotion and tension levels.

Now with sentence-level processing:
- Splits chunks into sentences
- Applies intensity to entire sentences (not just words)
- Places pauses only at sentence boundaries
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any


def split_into_sentences(text: str) -> List[str]:
    """
    Split text into sentences using regex.
    Handles common sentence endings: . ! ?
    Preserves abbreviations like "Dr." "Mr." "etc."
    """
    if not text or not text.strip():
        return []

    # Handle common abbreviations to avoid false splits
    text = text.replace("Dr.", "Dr<DOT>")
    text = text.replace("Mr.", "Mr<DOT>")
    text = text.replace("Mrs.", "Mrs<DOT>")
    text = text.replace("Ms.", "Ms<DOT>")
    text = text.replace("etc.", "etc<DOT>")
    text = text.replace("vs.", "vs<DOT>")
    text = text.replace("i.e.", "i<DOT>e<DOT>")
    text = text.replace("e.g.", "e<DOT>g<DOT>")

    # Split on sentence-ending punctuation followed by space
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())

    # Restore abbreviations and clean up
    result = []
    for s in sentences:
        s = s.replace("<DOT>", ".")
        s = s.strip()
        if s:
            result.append(s)

    return result

# Peak keywords that indicate particularly critical moments
PEAK_KEYWORDS = {
    "triumph", "breakthrough", "turning point", "decisive", "unprecedented",
    "revolutionary", "extraordinary", "captivated", "stunning", "impossible"
}

# Theme group mappings based on narrative arc
THEME_GROUPS = {
    "wonder": "origin_story",
    "curiosity": "origin_story",
    "tension": "breakthrough",
    "triumph": "breakthrough",
    "rebellion": "evolution",
    "intensity": "evolution",
    "liberation": "evolution",
    "mastery": "mastery",
    "excitement": "mastery"
}

# BGM intensity levels
BGM_INTENSITY_MAP = {
    "wonder": "low",
    "curiosity": "low",
    "reflection": "low",
    "melancholy": "low",
    "intrigue": "medium",
    "tension": "medium",
    "liberation": "medium",
    "triumph": "medium-high",
    "excitement": "medium-high",
    "mastery": "medium-high",
    "rebellion": "high",
    "explosive energy": "high"
}


class AudioDesignGenerator:
    def __init__(self, enhanced_script: dict):
        self.script = enhanced_script
        self.modules = enhanced_script.get("modules", [])
        self.hook = enhanced_script.get("hook", {})

    def _has_peak_keywords(self, chunk: dict) -> bool:
        """Check if chunk contains peak keywords indicating critical moment."""
        text = chunk.get("text", "").lower()
        keywords = [k.lower() for k in chunk.get("keywords", [])]

        # Check text and keywords for peak indicators
        for peak_word in PEAK_KEYWORDS:
            if peak_word in text or peak_word in keywords:
                return True
        return False

    def compute_vocal_parameters(self, chunk: dict) -> dict:
        """
        Compute intensity boost and pause duration based on tension.

        UPDATED: Higher intensity levels (100-120%) for critical moments.
        Intensity applies to ENTIRE sentences, not just words.

        Tension Level | Intensity Boost | Pause After Chunk
        1-2           | 0%              | 800ms
        3             | 50%             | 800ms
        4             | 100-110%        | 1000ms
        5             | 110-120%        | 1200ms
        """
        tension = chunk.get("tension_level", 2)
        is_critical = tension >= 4
        has_peak = self._has_peak_keywords(chunk)

        if tension >= 5:
            boost = 110 + (10 if has_peak else 0)  # 110-120%
            pause = 1200
        elif tension == 4:
            boost = 100 + (10 if has_peak else 0)  # 100-110%
            pause = 1000
        elif tension == 3:
            boost = 50
            pause = 800
        else:
            boost = 0
            pause = 800

        return {
            "intensity_boost_percent": boost,
            "pause_after_chunk_ms": pause,
            "pause_between_sentences_ms": 400,  # Brief pause between sentences
            "is_critical": is_critical,
            "has_peak_keywords": has_peak
        }

    def compute_sentence_level_metadata(self, chunk: dict) -> List[dict]:
        """
        Split chunk into sentences and compute per-sentence metadata.
        All sentences in a chunk inherit the chunk's tension-based intensity.
        """
        text = chunk.get("text", "")
        sentences = split_into_sentences(text)

        if not sentences:
            return []

        # Get chunk-level parameters (all sentences inherit these)
        chunk_params = self.compute_vocal_parameters(chunk)
        intensity = chunk_params["intensity_boost_percent"]
        is_critical = chunk_params["is_critical"]

        sentence_metadata = []
        for idx, sentence in enumerate(sentences):
            sentence_metadata.append({
                "sentence_idx": idx,
                "text": sentence,
                "intensity_boost_percent": intensity,  # Same for all sentences in chunk
                "is_critical": is_critical
            })

        return sentence_metadata

    def compute_bgm_parameters(self, module: dict) -> dict:
        """
        Determine BGM emotion and intensity for module consistency.
        Uses emotion_arc to determine primary emotion.
        """
        emotion_arc = module.get("emotion_arc", "")
        chunks = module.get("chunks", [])

        # Extract primary emotion from emotion_arc (first emotion in arc)
        if "->" in emotion_arc:
            primary_emotion = emotion_arc.split("->")[0].strip()
        else:
            primary_emotion = emotion_arc.strip()

        # Fallback to first chunk emotion if no arc
        if not primary_emotion and chunks:
            primary_emotion = chunks[0].get("emotion", "neutral")

        # Determine theme group and intensity
        theme_group = THEME_GROUPS.get(primary_emotion.lower(), "neutral")
        bgm_intensity = BGM_INTENSITY_MAP.get(primary_emotion.lower(), "medium")

        return {
            "primary_emotion": primary_emotion,
            "theme_group": theme_group,
            "bgm_intensity": bgm_intensity
        }

    def compute_transition(self, from_module: dict, to_module: dict) -> dict:
        """
        Compute transition parameters between modules.
        Ensures smooth transitions without abrupt intensity changes.
        """
        from_bgm = self.compute_bgm_parameters(from_module)
        to_bgm = self.compute_bgm_parameters(to_module)

        # Determine transition type based on intensity change
        intensity_order = ["low", "medium", "medium-high", "high"]
        from_idx = intensity_order.index(from_bgm["bgm_intensity"]) if from_bgm["bgm_intensity"] in intensity_order else 1
        to_idx = intensity_order.index(to_bgm["bgm_intensity"]) if to_bgm["bgm_intensity"] in intensity_order else 1

        intensity_change = to_idx - from_idx

        if intensity_change > 0:
            bgm_transition = "gradual_intensity_increase"
            duration_ms = 1500
        elif intensity_change < 0:
            bgm_transition = "gradual_intensity_decrease"
            duration_ms = 2000
        else:
            bgm_transition = "sustain"
            duration_ms = 1000

        return {
            "transition_type": "crossfade",
            "duration_ms": duration_ms,
            "bgm_transition": bgm_transition,
            "intensity_change": intensity_change
        }

    def generate_metadata(self) -> dict:
        """Generate complete audio design metadata with sentence-level processing."""
        metadata = {
            "audio_design_version": "2.0",  # Updated for sentence-level
            "title": self.script.get("title", "Unknown"),
            "global_parameters": {
                "base_voice_intensity_db": 0,
                "critical_intensity_boost_percent": 120,  # Updated: 100-120%
                "pause_between_sentences_ms": 400,  # Brief pause between sentences
                "pause_after_chunk_ms": 800,  # Pause at chunk boundaries
                "bgm_base_volume_db": -18
            },
            "hook": None,
            "modules": [],
            "module_transitions": []
        }

        # Process hook
        if self.hook:
            hook_text = self.hook.get("text", "")
            # Hook gets moderate boost for attention
            metadata["hook"] = {
                "text_preview": hook_text[:100] + "..." if len(hook_text) > 100 else hook_text,
                "emotion": self.hook.get("emotion", "intrigue"),
                "vocal_parameters": {
                    "intensity_boost_percent": 20,
                    "pause_after_ms": 2000
                },
                "bgm_parameters": None  # No BGM for hook
            }

        # Process modules
        for module in self.modules:
            module_id = module.get("id", 0)
            bgm_params = self.compute_bgm_parameters(module)

            module_meta = {
                "id": module_id,
                "title": module.get("title", f"Module {module_id}"),
                "emotion_arc": module.get("emotion_arc", ""),
                "theme_group": bgm_params["theme_group"],
                "bgm_emotion": bgm_params["primary_emotion"],
                "bgm_intensity": bgm_params["bgm_intensity"],
                "chunks": []
            }

            # Process chunks
            for chunk_idx, chunk in enumerate(module.get("chunks", [])):
                vocal_params = self.compute_vocal_parameters(chunk)
                sentence_metadata = self.compute_sentence_level_metadata(chunk)

                chunk_meta = {
                    "chunk_idx": chunk_idx,
                    "text_preview": chunk.get("text", "")[:80] + "...",
                    "full_text": chunk.get("text", ""),  # Full text for sentence extraction
                    "emotion": chunk.get("emotion", "neutral"),
                    "tension_level": chunk.get("tension_level", 2),
                    "keywords": chunk.get("keywords", []),
                    "is_critical": vocal_params["is_critical"],
                    "has_peak_keywords": vocal_params["has_peak_keywords"],
                    "vocal_parameters": {
                        "intensity_boost_percent": vocal_params["intensity_boost_percent"],
                        "pause_after_chunk_ms": vocal_params["pause_after_chunk_ms"],
                        "pause_between_sentences_ms": vocal_params["pause_between_sentences_ms"]
                    },
                    "sentences": sentence_metadata  # NEW: Sentence-level data
                }
                module_meta["chunks"].append(chunk_meta)

            metadata["modules"].append(module_meta)

        # Compute transitions between modules
        for i in range(len(self.modules) - 1):
            transition = self.compute_transition(self.modules[i], self.modules[i + 1])
            transition["from_module"] = self.modules[i].get("id", i + 1)
            transition["to_module"] = self.modules[i + 1].get("id", i + 2)
            metadata["module_transitions"].append(transition)

        # Add final fade out
        if self.modules:
            metadata["module_transitions"].append({
                "from_module": self.modules[-1].get("id", len(self.modules)),
                "to_module": None,
                "transition_type": "fade_out",
                "duration_ms": 3000,
                "bgm_transition": "fade_to_silence"
            })

        # Add summary statistics
        metadata["summary"] = self._compute_summary(metadata)

        return metadata

    def _compute_summary(self, metadata: dict) -> dict:
        """Compute summary statistics for the audio design."""
        total_chunks = 0
        critical_chunks = 0
        peak_chunks = 0

        for module in metadata["modules"]:
            for chunk in module["chunks"]:
                total_chunks += 1
                if chunk["is_critical"]:
                    critical_chunks += 1
                if chunk["has_peak_keywords"]:
                    peak_chunks += 1

        return {
            "total_modules": len(metadata["modules"]),
            "total_chunks": total_chunks,
            "critical_chunks": critical_chunks,
            "peak_keyword_chunks": peak_chunks,
            "critical_percentage": round(critical_chunks / total_chunks * 100, 1) if total_chunks > 0 else 0
        }


def generate_audio_design(script_path: str, output_path: str = None) -> dict:
    """
    Generate audio design metadata from enhanced script.

    Args:
        script_path: Path to enhanced_script.json
        output_path: Optional path for output JSON (defaults to audio/audio_design_metadata.json)

    Returns:
        Generated metadata dictionary
    """
    # Load enhanced script
    with open(script_path, "r") as f:
        enhanced_script = json.load(f)

    # Generate metadata
    generator = AudioDesignGenerator(enhanced_script)
    metadata = generator.generate_metadata()

    # Save to file
    if output_path is None:
        base_dir = Path(script_path).parent.parent
        output_dir = base_dir / "Output" / "audio"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "audio_design_metadata.json"

    with open(output_path, "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"Audio design metadata saved to: {output_path}")

    return metadata


def print_metadata_summary(metadata: dict):
    """Print a human-readable summary of the audio design metadata."""
    print("\n" + "=" * 60)
    print("AUDIO DESIGN METADATA SUMMARY")
    print("=" * 60)

    print(f"\nTitle: {metadata.get('title', 'Unknown')}")
    print(f"Version: {metadata.get('audio_design_version', '1.0')}")

    # Global parameters
    global_params = metadata.get("global_parameters", {})
    print(f"\nGlobal Parameters:")
    print(f"  Critical intensity boost: {global_params.get('critical_intensity_boost_percent', 35)}%")
    print(f"  Standard pause: {global_params.get('standard_pause_ms', 300)}ms")
    print(f"  Critical pause: {global_params.get('critical_pause_ms', 2500)}ms")
    print(f"  BGM base volume: {global_params.get('bgm_base_volume_db', -18)}dB")

    # Hook
    hook = metadata.get("hook")
    if hook:
        print(f"\nHook:")
        print(f"  Emotion: {hook.get('emotion', 'intrigue')}")
        print(f"  Intensity boost: {hook['vocal_parameters']['intensity_boost_percent']}%")
        print(f"  Pause after: {hook['vocal_parameters']['pause_after_ms']}ms")

    # Modules
    print(f"\nModules:")
    for module in metadata.get("modules", []):
        print(f"\n  Module {module['id']}: {module['title']}")
        print(f"    Theme group: {module['theme_group']}")
        print(f"    BGM emotion: {module['bgm_emotion']}")
        print(f"    BGM intensity: {module['bgm_intensity']}")
        print(f"    Chunks: {len(module['chunks'])}")

        # Show critical chunks
        critical = [c for c in module["chunks"] if c["is_critical"]]
        if critical:
            print(f"    Critical chunks: {len(critical)}")
            for c in critical:
                print(f"      - Chunk {c['chunk_idx']}: {c['emotion']} (tension={c['tension_level']}, boost={c['vocal_parameters']['intensity_boost_percent']}%)")

    # Transitions
    print(f"\nModule Transitions:")
    for trans in metadata.get("module_transitions", []):
        if trans["to_module"]:
            print(f"  {trans['from_module']} → {trans['to_module']}: {trans['bgm_transition']} ({trans['duration_ms']}ms)")
        else:
            print(f"  {trans['from_module']} → END: {trans['bgm_transition']} ({trans['duration_ms']}ms)")

    # Summary
    summary = metadata.get("summary", {})
    print(f"\nSummary:")
    print(f"  Total modules: {summary.get('total_modules', 0)}")
    print(f"  Total chunks: {summary.get('total_chunks', 0)}")
    print(f"  Critical chunks: {summary.get('critical_chunks', 0)} ({summary.get('critical_percentage', 0)}%)")
    print(f"  Peak keyword chunks: {summary.get('peak_keyword_chunks', 0)}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate audio design metadata from enhanced script")
    parser.add_argument(
        "--input",
        default="Output/enhanced_script.json",
        help="Path to enhanced script JSON"
    )
    parser.add_argument(
        "--output",
        help="Output path for metadata JSON (default: Output/audio/audio_design_metadata.json)"
    )

    args = parser.parse_args()

    # Resolve paths
    base_dir = Path(__file__).parent.parent
    input_path = base_dir / args.input

    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        exit(1)

    # Generate metadata
    metadata = generate_audio_design(str(input_path), args.output)

    # Print summary
    print_metadata_summary(metadata)
