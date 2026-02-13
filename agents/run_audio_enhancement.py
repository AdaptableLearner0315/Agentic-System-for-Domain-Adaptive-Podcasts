"""
Audio Enhancement Pipeline

Takes the enhanced script JSON and generates:
1. TTS narration for all chunks (or sentences for sentence-level mode)
2. Background music for each module
3. Final mixed audio file

Sentence-Level Mode (--sentence-level):
- Generates TTS for each sentence separately
- Applies intensity to entire sentences
- Places pauses only at sentence boundaries
"""

import os
import json
import argparse
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from agents.tts_narrator import TTSNarrator
from agents.music_generator import MusicGenerator
from utils.audio_mixer import AudioMixer
from utils.audio_design_generator import generate_audio_design


def load_enhanced_script(path: str) -> dict:
    """Load enhanced script from JSON file."""
    with open(path, "r") as f:
        return json.load(f)


def _load_sentence_level_tts(tts_dir: Path) -> list:
    """
    Load sentence-level TTS files from directory.

    Expected filenames:
    - hook_sent_1.wav, hook_sent_2.wav, ...
    - module_1_chunk_1_sent_1.wav, module_1_chunk_1_sent_2.wav, ...
    """
    tts_files = []

    for f in sorted(tts_dir.glob("*.wav")):
        filename = f.stem

        if filename.startswith("hook_sent_"):
            # Parse hook_sent_X format
            parts = filename.split("_")
            if len(parts) >= 3:
                sent_idx = int(parts[2]) - 1
                tts_files.append({
                    "path": str(f),
                    "type": "hook_sentence",
                    "sentence_idx": sent_idx,
                    "text": "",
                    "emotion": "intrigue"
                })
        elif "_sent_" in filename and filename.startswith("module_"):
            # Parse module_X_chunk_Y_sent_Z format
            parts = filename.split("_")
            if len(parts) >= 6:
                module_id = int(parts[1])
                chunk_idx = int(parts[3]) - 1
                sent_idx = int(parts[5]) - 1
                tts_files.append({
                    "path": str(f),
                    "type": "chunk_sentence",
                    "module_id": module_id,
                    "chunk_idx": chunk_idx,
                    "sentence_idx": sent_idx,
                    "text": "",
                    "emotion": "neutral"
                })

    return tts_files


def run_audio_enhancement(
    script_path: str,
    output_dir: str = None,
    skip_tts: bool = False,
    skip_bgm: bool = False,
    sentence_level: bool = False
) -> dict:
    """
    Run the full audio enhancement pipeline.

    Args:
        script_path: Path to enhanced_script.json
        output_dir: Output directory for audio files
        skip_tts: Skip TTS generation (use existing files)
        skip_bgm: Skip BGM generation (use existing files)
        sentence_level: Use sentence-level processing for precise control

    Returns:
        Dictionary with paths to generated files
    """
    print("\n" + "="*60)
    print("Audio Enhancement Pipeline" + (" (Sentence-Level)" if sentence_level else ""))
    print("="*60)

    # Base directory
    base_dir = Path(script_path).parent.parent

    # Load enhanced script
    print(f"\nLoading enhanced script from: {script_path}")
    enhanced_script = load_enhanced_script(script_path)
    print(f"Title: {enhanced_script.get('title', 'Unknown')}")

    # Count items to process
    hook = enhanced_script.get("hook", {})
    modules = enhanced_script.get("modules", [])
    total_chunks = sum(len(m.get("chunks", [])) for m in modules)
    print(f"Items to process: 1 hook + {total_chunks} chunks across {len(modules)} modules")

    results = {
        "tts_files": [],
        "bgm_files": [],
        "final_audio": None
    }

    # Step 0: Generate/update audio design metadata (for sentence-level info)
    if sentence_level:
        print("\n" + "-"*40)
        print("Step 0: Generating Audio Design Metadata")
        print("-"*40)
        metadata = generate_audio_design(script_path)
        print(f"Generated metadata with {metadata.get('summary', {}).get('total_chunks', 0)} chunks")

    # Step 1: Generate TTS
    if not skip_tts:
        print("\n" + "-"*40)
        print(f"Step 1: Generating TTS Narration" + (" (Sentence-Level)" if sentence_level else ""))
        print("-"*40)
        # Use female voice by default for professional podcast narration
        narrator = TTSNarrator(use_female_voice=True)

        if sentence_level:
            # Generate TTS for each sentence separately
            results["tts_files"] = narrator.generate_all_chunks_sentence_level(enhanced_script)
            print(f"\nGenerated {len(results['tts_files'])} sentence-level TTS files")
        else:
            results["tts_files"] = narrator.generate_all_chunks(enhanced_script)
            print(f"\nGenerated {len(results['tts_files'])} TTS files")
    else:
        print("\nSkipping TTS generation (using existing files)")
        # Load existing TTS files with proper metadata
        tts_dir = base_dir / "Output" / "audio" / "tts"
        if tts_dir.exists():
            if sentence_level:
                # Load sentence-level files (module_X_chunk_Y_sent_Z.wav)
                results["tts_files"] = _load_sentence_level_tts(tts_dir)
            else:
                # Load chunk-level files (legacy)
                for f in sorted(tts_dir.glob("*.wav")):
                    filename = f.stem
                    if filename == "hook":
                        results["tts_files"].append({
                            "path": str(f),
                            "type": "hook",
                            "text": "",
                            "emotion": "intrigue"
                        })
                    elif filename.startswith("module_") and "_sent_" not in filename:
                        # Parse module_X_chunk_Y format (exclude sentence files)
                        parts = filename.split("_")
                        if len(parts) >= 4:
                            module_id = int(parts[1])
                            chunk_idx = int(parts[3]) - 1
                            results["tts_files"].append({
                                "path": str(f),
                                "type": "chunk",
                                "module_id": module_id,
                                "chunk_idx": chunk_idx,
                                "text": "",
                                "emotion": "neutral"
                            })

    # Step 2: Generate BGM
    if not skip_bgm:
        print("\n" + "-"*40)
        print("Step 2: Generating Background Music")
        print("-"*40)
        music_gen = MusicGenerator()
        results["bgm_files"] = music_gen.generate_module_bgm(modules)
        print(f"\nGenerated {len(results['bgm_files'])} BGM files")
    else:
        print("\nSkipping BGM generation (using existing files)")
        bgm_dir = Path(output_dir or ".") / "Output" / "audio" / "bgm"
        if bgm_dir.exists():
            for f in sorted(bgm_dir.glob("*.wav")):
                # Extract module_id from filename (e.g., module_1_bgm.wav -> 1)
                filename = f.stem
                try:
                    parts = filename.split("_")
                    module_id = int(parts[1]) if len(parts) >= 2 else 0
                except (ValueError, IndexError):
                    module_id = 0
                results["bgm_files"].append({"path": str(f), "module_id": module_id})
            print(f"  Found {len(results['bgm_files'])} existing BGM files")

    # Step 3: Mix Audio
    print("\n" + "-"*40)
    print(f"Step 3: Mixing Final Audio" + (" (Sentence-Level)" if sentence_level else ""))
    print("-"*40)

    if results["tts_files"]:
        mixer = AudioMixer()

        if sentence_level:
            # Use sentence-level mixer
            results["final_audio"] = mixer.mix_podcast_sentence_level(
                results["tts_files"],
                results["bgm_files"],
                output_filename="final_enhanced_v2"
            )
        else:
            results["final_audio"] = mixer.mix_podcast(
                results["tts_files"],
                results["bgm_files"],
                output_filename="final_enhanced"
            )
        print(f"\nFinal audio saved to: {results['final_audio']}")
    else:
        print("Error: No TTS files to mix")

    # Summary
    print("\n" + "="*60)
    print("AUDIO ENHANCEMENT COMPLETE")
    print("="*60)
    print(f"TTS Files: {len(results['tts_files'])}")
    print(f"BGM Files: {len(results['bgm_files'])}")
    print(f"Final Audio: {results['final_audio']}")

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Generate enhanced audio from enhanced script"
    )
    parser.add_argument(
        "--input",
        default="Output/enhanced_script.json",
        help="Path to enhanced script JSON (default: Output/enhanced_script.json)"
    )
    parser.add_argument(
        "--skip-tts",
        action="store_true",
        help="Skip TTS generation, use existing files"
    )
    parser.add_argument(
        "--skip-bgm",
        action="store_true",
        help="Skip BGM generation, use existing files"
    )
    parser.add_argument(
        "--sentence-level",
        action="store_true",
        help="Use sentence-level processing for precise intensity and pause control"
    )

    args = parser.parse_args()

    # Resolve paths
    base_dir = Path(__file__).parent
    input_path = base_dir / args.input

    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        return

    # Run pipeline
    results = run_audio_enhancement(
        script_path=str(input_path),
        output_dir=str(base_dir),
        skip_tts=args.skip_tts,
        skip_bgm=args.skip_bgm,
        sentence_level=args.sentence_level
    )


if __name__ == "__main__":
    main()
