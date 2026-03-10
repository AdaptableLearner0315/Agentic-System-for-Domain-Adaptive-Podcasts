#!/usr/bin/env python3
"""
Pre-Generate Assets CLI
Author: Sarath

Pre-generates music stems, voice phrases, and images for fast podcast generation.
Run once to populate the asset libraries, then Normal mode will use these
instead of making API calls (saving 15-25 seconds per generation).

Usage:
    python scripts/pregenerate_assets.py --all       # Pre-generate all assets
    python scripts/pregenerate_assets.py --bgm       # Pre-generate BGM stems only
    python scripts/pregenerate_assets.py --voice     # Pre-generate voice phrases only
    python scripts/pregenerate_assets.py --images    # Pre-generate images only
    python scripts/pregenerate_assets.py --status    # Show current asset status
"""

import argparse
import sys
import time
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def get_asset_status():
    """Get the current status of pre-generated assets."""
    from assets.music_manager import MusicAssetManager
    from assets.voice_manager import VoiceAssetManager

    music_manager = MusicAssetManager()
    voice_manager = VoiceAssetManager()

    # Count BGM stems
    bgm_total = sum(len(cfg["moods"]) for cfg in MusicAssetManager.STEM_CATEGORIES.values())
    bgm_available = music_manager.get_available_stem_count()

    # Count voice phrases
    voice_total = sum(len(phrases) for phrases in voice_manager.COMMON_PHRASES.values())
    voice_available = len([h for h, p in voice_manager._phrase_cache.items() if Path(p).exists()])

    return {
        "bgm": {"available": bgm_available, "total": bgm_total},
        "voice": {"available": voice_available, "total": voice_total},
    }


def print_status():
    """Print the current asset library status."""
    status = get_asset_status()

    print("\n" + "=" * 50)
    print("ASSET LIBRARY STATUS")
    print("=" * 50)

    bgm = status["bgm"]
    voice = status["voice"]

    bgm_pct = (bgm["available"] / bgm["total"] * 100) if bgm["total"] > 0 else 0
    voice_pct = (voice["available"] / voice["total"] * 100) if voice["total"] > 0 else 0

    print(f"\nBGM Stems:     {bgm['available']}/{bgm['total']} ({bgm_pct:.0f}%)")
    print(f"Voice Phrases: {voice['available']}/{voice['total']} ({voice_pct:.0f}%)")

    # Readiness indicator
    print("\n" + "-" * 50)
    if bgm["available"] >= 3:  # At least one per category
        print("BGM:   READY for fast generation")
    else:
        print("BGM:   Run 'python scripts/pregenerate_assets.py --bgm' to enable fast mode")

    if voice["available"] >= 4:  # At least a few phrases
        print("Voice: READY for caching benefits")
    else:
        print("Voice: Run 'python scripts/pregenerate_assets.py --voice' to enable caching")

    print("=" * 50 + "\n")


def pregenerate_bgm_stems():
    """Pre-generate all BGM music stems."""
    from assets.music_manager import MusicAssetManager
    from agents.audio_designer.bgm_generator import BGMGenerator
    from config.paths import AUDIO_DIR

    print("\n" + "=" * 50)
    print("PRE-GENERATING BGM STEMS")
    print("=" * 50)

    music_manager = MusicAssetManager()
    generator = BGMGenerator(output_dir=AUDIO_DIR / "bgm" / "stems")

    # Calculate total
    total_stems = sum(len(cfg["moods"]) for cfg in MusicAssetManager.STEM_CATEGORIES.values())
    generated = 0
    skipped = 0
    failed = 0

    start_time = time.time()

    for category, config in MusicAssetManager.STEM_CATEGORIES.items():
        print(f"\n[{category.upper()}] ({config['duration']}s stems)")

        for mood in config["moods"]:
            # Check if already exists
            if music_manager.get_stem_path(category, mood):
                print(f"  {mood}: CACHED")
                skipped += 1
                continue

            # Generate new stem
            print(f"  {mood}: Generating...", end=" ", flush=True)
            try:
                filename = f"stem_{category}_{mood}"
                path = generator.generate_bgm(mood, filename, config["duration"])

                if path:
                    music_manager.add_to_catalog(category, mood, path)
                    print("OK")
                    generated += 1
                else:
                    print("FAILED (no path)")
                    failed += 1

            except Exception as e:
                print(f"FAILED ({e})")
                failed += 1

    elapsed = time.time() - start_time

    print("\n" + "-" * 50)
    print(f"Generated: {generated}")
    print(f"Skipped:   {skipped} (already cached)")
    print(f"Failed:    {failed}")
    print(f"Time:      {elapsed:.1f}s")
    print("=" * 50 + "\n")

    return generated > 0 or skipped > 0


def pregenerate_voice_phrases():
    """Pre-generate common voice phrases."""
    from assets.voice_manager import VoiceAssetManager
    from agents.audio_designer.tts_narrator import TTSNarrator
    from config.paths import AUDIO_DIR

    print("\n" + "=" * 50)
    print("PRE-GENERATING VOICE PHRASES")
    print("=" * 50)

    voice_manager = VoiceAssetManager()
    narrator = TTSNarrator(output_dir=AUDIO_DIR / "tts" / "phrases")

    def tts_func(text: str, filename: str) -> str:
        return narrator.generate_speech(text, filename)

    start_time = time.time()

    # Use the built-in pregenerate method
    voice_manager.pregenerate_common_phrases(tts_func)

    elapsed = time.time() - start_time

    print(f"\nTime: {elapsed:.1f}s")
    print("=" * 50 + "\n")

    return True


def pregenerate_images():
    """Pre-generate a library of stock images."""
    import fal_client
    import requests
    from config.paths import VISUALS_DIR

    print("\n" + "=" * 50)
    print("PRE-GENERATING IMAGE LIBRARY")
    print("=" * 50)

    # Define a set of generic, reusable image prompts
    IMAGE_PROMPTS = [
        # Abstract/atmospheric
        "Abstract light rays through fog, ethereal atmosphere, cinematic photography",
        "Dramatic cloudy sky at golden hour, natural landscape, documentary style",
        "Bokeh lights in darkness, abstract background, film grain texture",

        # Technology
        "Close-up of digital circuitry, macro photography, blue tones, tech aesthetic",
        "Futuristic data visualization, holographic display, sci-fi atmosphere",

        # Nature
        "Misty forest at dawn, rays of light through trees, peaceful atmosphere",
        "Ocean waves at sunset, long exposure photography, calm and meditative",

        # People/concepts (silhouettes/abstract)
        "Silhouette of person looking at horizon, contemplative mood, warm backlight",
        "Hands typing on keyboard, close-up, professional workspace, shallow depth",

        # Urban
        "City skyline at night, long exposure light trails, urban energy",
    ]

    output_dir = VISUALS_DIR / "library"
    output_dir.mkdir(parents=True, exist_ok=True)

    generated = 0
    skipped = 0
    failed = 0

    start_time = time.time()

    for i, prompt in enumerate(IMAGE_PROMPTS):
        output_path = output_dir / f"stock_{i+1:02d}.png"

        # Check if already exists
        if output_path.exists():
            print(f"  [{i+1}/{len(IMAGE_PROMPTS)}] CACHED: {prompt[:40]}...")
            skipped += 1
            continue

        print(f"  [{i+1}/{len(IMAGE_PROMPTS)}] Generating: {prompt[:40]}...", end=" ", flush=True)

        try:
            result = fal_client.subscribe(
                "fal-ai/flux/dev",
                arguments={
                    "prompt": prompt,
                    "image_size": "landscape_16_9",
                    "num_images": 1,
                },
                with_logs=False
            )

            images = result.get("images", [])
            if images:
                image_url = images[0].get("url")
                if image_url:
                    response = requests.get(image_url)
                    with open(output_path, 'wb') as f:
                        f.write(response.content)
                    print("OK")
                    generated += 1
                else:
                    print("FAILED (no URL)")
                    failed += 1
            else:
                print("FAILED (no images)")
                failed += 1

        except Exception as e:
            print(f"FAILED ({e})")
            failed += 1

    elapsed = time.time() - start_time

    print("\n" + "-" * 50)
    print(f"Generated: {generated}")
    print(f"Skipped:   {skipped} (already cached)")
    print(f"Failed:    {failed}")
    print(f"Time:      {elapsed:.1f}s")
    print("=" * 50 + "\n")

    return generated > 0 or skipped > 0


def main():
    parser = argparse.ArgumentParser(
        description="Pre-generate assets for fast podcast generation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        "--all",
        action="store_true",
        help="Pre-generate all asset types (BGM, voice, images)"
    )
    parser.add_argument(
        "--bgm",
        action="store_true",
        help="Pre-generate BGM music stems (~5 minutes, 15 stems)"
    )
    parser.add_argument(
        "--voice",
        action="store_true",
        help="Pre-generate common voice phrases (~1 minute, 16 phrases)"
    )
    parser.add_argument(
        "--images",
        action="store_true",
        help="Pre-generate stock images (~2 minutes, 10 images)"
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show current asset library status"
    )

    args = parser.parse_args()

    # Default to status if no args
    if not any([args.all, args.bgm, args.voice, args.images, args.status]):
        print_status()
        print("Use --help for available options")
        return

    if args.status:
        print_status()
        return

    # Run requested pre-generation
    total_start = time.time()
    success = True

    if args.all or args.bgm:
        success = pregenerate_bgm_stems() and success

    if args.all or args.voice:
        success = pregenerate_voice_phrases() and success

    if args.all or args.images:
        success = pregenerate_images() and success

    total_elapsed = time.time() - total_start

    print("\n" + "=" * 50)
    print(f"TOTAL TIME: {total_elapsed:.1f}s ({total_elapsed/60:.1f} minutes)")
    print("=" * 50)

    # Show final status
    print_status()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
