"""
Podcast Enhancement Pipeline
Author: Sarath

Main entry point for the hyper-personalized podcast system.
Provides subcommands for each stage of the pipeline.

Supports two modes:
- Normal: Fast generation (~2 minutes) with parallel execution
- Pro: High-quality generation (~6 minutes) with full features

Supports three input modes:
- Generation: --prompt only → generate content from scratch
- Enhancement: --input/--files only → enhance existing content
- Hybrid: --prompt + --files → generate content informed by files

Usage:
    # MODE 1: Pure Generation (prompt only)
    python run_pipeline.py full --prompt "The history of electronic music" --mode normal
    python run_pipeline.py full --prompt "AI breakthroughs" --guidance "For beginners" --mode pro

    # MODE 2: Pure Enhancement (files only - existing behavior)
    python run_pipeline.py full --input transcript.txt --mode normal
    python run_pipeline.py full --files document.pdf audio.mp3 --mode pro
    python run_pipeline.py full --input "https://example.com/article" --mode normal

    # MODE 3: Hybrid (prompt + files as context)
    python run_pipeline.py full --prompt "Key insights" --files research.pdf --mode pro
    python run_pipeline.py full --prompt "Future of AI" --files paper1.pdf paper2.pdf --mode normal

    # Legacy commands (still supported)
    python run_pipeline.py enhance --input transcript.txt
    python run_pipeline.py audio --script Output/enhanced_script.json
    python run_pipeline.py visual --script Output/enhanced_script.json
    python run_pipeline.py preview --module 1
"""

import argparse
import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base directory
BASE_DIR = Path(__file__).parent


def _is_topic_prompt(prompt: str) -> bool:
    """
    Determine if a prompt looks like a topic/subject for generation
    vs. style guidance for enhancement.

    Args:
        prompt: The prompt string to analyze

    Returns:
        True if prompt looks like a topic, False if it looks like guidance
    """
    if not prompt:
        return False

    prompt_lower = prompt.lower().strip()

    # Guidance patterns - these suggest the prompt is style/focus guidance
    guidance_patterns = [
        "make it",
        "focus on",
        "emphasize",
        "for beginners",
        "for experts",
        "in the style of",
        "more engaging",
        "more technical",
        "simplified",
        "detailed",
        "conversational",
        "formal",
        "informal",
        "keep it",
        "ensure",
        "highlight",
    ]

    for pattern in guidance_patterns:
        if pattern in prompt_lower:
            return False

    # If the prompt is short and doesn't have guidance patterns,
    # it's likely a topic
    return True


def cmd_enhance(args):
    """
    Enhance a transcript with emotional arc and structure.

    Uses the ScriptEnhancer and Director agents to create
    an engaging, structured script with emotional mapping.
    """
    from agents.script_enhancer import ScriptEnhancer
    from agents.director import Director

    # Resolve input path
    input_path = Path(args.input)
    if not input_path.is_absolute():
        input_path = BASE_DIR / input_path

    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        return 1

    # Determine output path
    if args.output:
        output_path = Path(args.output)
        if not output_path.is_absolute():
            output_path = BASE_DIR / output_path
    else:
        output_path = BASE_DIR / "Output" / "enhanced_script.json"

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Load transcript
    print(f"Loading transcript from: {input_path}")
    with open(input_path, "r") as f:
        transcript = f.read()
    print(f"Transcript length: {len(transcript)} characters")

    # Determine model
    model_map = {
        "sonnet": "claude-sonnet-4-20250514",
        "opus": "claude-opus-4-20250514"
    }
    model_id = model_map.get(args.model, model_map["sonnet"])

    print(f"\n{'='*60}")
    print(f"Script Enhancement Pipeline")
    print(f"{'='*60}")
    print(f"Model: {model_id}")
    print(f"Max reviews: {args.max_reviews}")
    print(f"{'='*60}\n")

    # Initialize agents
    enhancer = ScriptEnhancer(model=model_id)
    director = Director(model=model_id)

    # Run enhancement loop
    review_history = []
    feedback = None
    enhanced_script = None
    approved = False
    review_count = 0

    while not approved and review_count < args.max_reviews:
        review_count += 1
        print(f"\n--- Round {review_count}/{args.max_reviews} ---")

        # Enhance script
        print("Enhancing script...")
        enhanced_script = enhancer.enhance(transcript, feedback)

        if "error" in enhanced_script:
            print(f"Enhancement error: {enhanced_script['error']}")
            return 1

        # Review script
        print("Director reviewing...")
        review_result = director.review(enhanced_script)

        # Record review
        review_entry = {
            "round": review_count,
            "score": review_result.get("score", 0),
            "approved": review_result.get("approved", False),
            "evaluation": review_result.get("evaluation", {}),
            "feedback": review_result.get("feedback", "")
        }
        review_history.append(review_entry)

        # Print review summary
        print(f"\nReview Score: {review_result.get('score', 'N/A')}/10")
        print(f"Approved: {review_result.get('approved', False)}")

        if review_result.get("approved"):
            approved = True
            print("\n*** APPROVED by Director! ***")
        else:
            feedback = review_result.get("feedback", "")
            print(f"\nFeedback: {feedback[:200]}...")

    # Add review history to script
    if enhanced_script and "error" not in enhanced_script:
        enhanced_script["review_history"] = review_history
        enhanced_script["final_status"] = {
            "approved": approved,
            "total_rounds": review_count,
            "final_score": review_history[-1]["score"] if review_history else 0
        }

    # Save result
    with open(output_path, "w") as f:
        json.dump(enhanced_script, f, indent=2)

    print(f"\n{'='*60}")
    print("ENHANCEMENT COMPLETE")
    print(f"{'='*60}")
    print(f"Output saved to: {output_path}")
    print(f"Final Status: {'APPROVED' if approved else 'MAX ITERATIONS REACHED'}")
    print(f"Final Score: {enhanced_script.get('final_status', {}).get('final_score', 0)}/10")

    return 0


def cmd_audio(args):
    """
    Generate audio from enhanced script.

    Generates TTS narration and background music, then mixes
    them together with VAD-based ducking.
    """
    from agents.tts_narrator import TTSNarrator
    from agents.music_generator import MusicGenerator
    from utils.audio_mixer import AudioMixer

    # Resolve script path
    script_path = Path(args.script)
    if not script_path.is_absolute():
        script_path = BASE_DIR / script_path

    if not script_path.exists():
        print(f"Error: Script file not found: {script_path}")
        return 1

    # Load enhanced script
    print(f"Loading enhanced script from: {script_path}")
    with open(script_path, "r") as f:
        enhanced_script = json.load(f)
    print(f"Title: {enhanced_script.get('title', 'Unknown')}")

    print(f"\n{'='*60}")
    print("Audio Generation Pipeline")
    print(f"{'='*60}")

    results = {
        "tts_files": [],
        "bgm_files": [],
        "final_audio": None
    }

    # Step 1: Generate TTS
    if not args.skip_tts:
        print("\n--- Step 1: Generating TTS Narration ---")
        narrator = TTSNarrator(use_female_voice=True)

        if args.sentence_level:
            results["tts_files"] = narrator.generate_all_chunks_sentence_level(enhanced_script)
        else:
            results["tts_files"] = narrator.generate_all_chunks(enhanced_script)

        print(f"Generated {len(results['tts_files'])} TTS files")
    else:
        print("\n--- Step 1: Skipping TTS (using existing files) ---")

    # Step 2: Generate BGM
    if not args.skip_bgm:
        print("\n--- Step 2: Generating Background Music ---")
        music_gen = MusicGenerator()
        modules = enhanced_script.get("modules", [])
        results["bgm_files"] = music_gen.generate_module_bgm(modules)
        print(f"Generated {len(results['bgm_files'])} BGM files")
    else:
        print("\n--- Step 2: Skipping BGM (using existing files) ---")

    # Step 3: Mix Audio
    if results["tts_files"]:
        print("\n--- Step 3: Mixing Final Audio ---")
        mixer = AudioMixer()

        if args.sentence_level:
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

        print(f"Final audio saved to: {results['final_audio']}")

    print(f"\n{'='*60}")
    print("AUDIO GENERATION COMPLETE")
    print(f"{'='*60}")

    return 0


def cmd_visual(args):
    """
    Generate images from enhanced script.

    Creates narrative-driven images for hook and each module
    using Fal AI Flux model.
    """
    from agents.image_generator import ImageGenerator
    from utils.video_assembler import create_hook_video

    # Resolve script path
    script_path = Path(args.script)
    if not script_path.is_absolute():
        script_path = BASE_DIR / script_path

    if not script_path.exists():
        print(f"Error: Script file not found: {script_path}")
        return 1

    print(f"\n{'='*60}")
    print("Visual Generation Pipeline")
    print(f"{'='*60}")

    generator = ImageGenerator()

    # Generate images for each section
    all_images = []

    # Hook images
    print("\n--- Generating Hook Images ---")
    hook_images = generator.generate_hook_images()
    all_images.extend(hook_images)

    # Module images
    for module_id in [1, 2, 3, 4]:
        print(f"\n--- Generating Module {module_id} Images ---")
        module_images = generator.generate_module_images(module_id)
        all_images.extend(module_images)

    print(f"\n{'='*60}")
    print("VISUAL GENERATION COMPLETE")
    print(f"{'='*60}")
    print(f"Total images generated: {len(all_images)}")

    return 0


def cmd_full(args):
    """
    Run the complete pipeline from transcript to final video.

    Supports two modes:
    - normal: Fast generation (~2 minutes)
    - pro: High-quality generation (~6 minutes)

    Also supports multi-format input (PDF, Word, audio, video, URL).
    """
    import asyncio

    mode = getattr(args, 'mode', 'normal')

    print(f"\n{'='*70}")
    print(f"FULL PODCAST ENHANCEMENT PIPELINE - {mode.upper()} MODE")
    print(f"{'='*70}")

    # Check if using new mode-based pipeline
    if mode in ('normal', 'pro'):
        return cmd_full_mode(args)

    # Legacy pipeline (original behavior)
    print("\n" + "="*60)
    print("STEP 1: SCRIPT ENHANCEMENT")
    print("="*60)

    enhance_args = argparse.Namespace(
        input=args.input,
        output="Output/enhanced_script.json",
        model=args.model,
        max_reviews=args.max_reviews
    )
    result = cmd_enhance(enhance_args)
    if result != 0:
        return result

    # Step 2: Generate audio
    print("\n" + "="*60)
    print("STEP 2: AUDIO GENERATION")
    print("="*60)

    audio_args = argparse.Namespace(
        script="Output/enhanced_script.json",
        skip_tts=False,
        skip_bgm=False,
        sentence_level=True
    )
    result = cmd_audio(audio_args)
    if result != 0:
        return result

    # Step 3: Generate visuals
    print("\n" + "="*60)
    print("STEP 3: VISUAL GENERATION")
    print("="*60)

    visual_args = argparse.Namespace(
        script="Output/enhanced_script.json"
    )
    result = cmd_visual(visual_args)
    if result != 0:
        return result

    # Step 4: Advanced BGM Pipeline (9-segment daisy-chain)
    print("\n" + "="*60)
    print("STEP 4: ADVANCED BGM PIPELINE")
    print("="*60)

    # Import and run advanced BGM pipeline
    try:
        from advanced_bgm_pipeline_v2 import (
            generate_all_segments,
            stitch_segments,
            mix_final,
            update_video
        )

        generate_all_segments()
        stitch_segments()
        mix_final()
        update_video()
    except ImportError as e:
        print(f"Warning: Could not run advanced BGM pipeline: {e}")

    print(f"\n{'='*70}")
    print("FULL PIPELINE COMPLETE")
    print(f"{'='*70}")
    print(f"\nOutputs:")
    print(f"  Script: Output/enhanced_script.json")
    print(f"  Audio:  Output/audio/final_v2/final_podcast_v2.mp3")
    print(f"  Video:  Output/Visuals Included/v2_daisy/final_podcast_video_v2.mp4")

    return 0


def cmd_full_mode(args):
    """
    Run the full pipeline using Normal or Pro mode.

    This uses the new optimized pipelines with:
    - Parallel execution
    - Multi-format input support
    - Progress streaming
    - Emotion mapping (Pro mode)
    - Multi-speaker support (Pro mode)

    Supports three input modes:
    - Generation: --prompt only → generate content from scratch
    - Enhancement: --input/--files only → enhance existing content
    - Hybrid: --prompt + --files → generate content informed by files
    """
    import asyncio
    import time
    from utils.smart_input_handler import SmartInputHandler, SmartInput

    mode = getattr(args, 'mode', 'normal')
    show_progress = not getattr(args, 'quiet', False)
    config_path = getattr(args, 'config', None)

    # Handle input arguments with backward compatibility
    prompt = getattr(args, 'prompt', None)
    guidance = getattr(args, 'guidance', None)
    files = getattr(args, 'files', None) or []
    input_path = getattr(args, 'input', None)

    # Backward compatibility: --input becomes first file if no --files specified
    if input_path and not files:
        files = [input_path]

    # Also support using --prompt as guidance when files are provided (legacy behavior)
    # But only if --guidance is not explicitly set
    legacy_prompt_as_guidance = prompt if (files and not guidance and not _is_topic_prompt(prompt)) else None
    if legacy_prompt_as_guidance:
        guidance = legacy_prompt_as_guidance
        prompt = None  # Clear prompt since it's being used as guidance

    # Validate inputs
    if not prompt and not files:
        print("Error: Must provide either --prompt or --input/--files")
        print("\nUsage examples:")
        print("  # Generate from topic (prompt only)")
        print("  python run_pipeline.py full --prompt 'History of AI' --mode normal")
        print("")
        print("  # Enhance existing content (files only)")
        print("  python run_pipeline.py full --input transcript.txt --mode normal")
        print("  python run_pipeline.py full --files doc.pdf audio.mp3 --mode pro")
        print("")
        print("  # Generate with file context (prompt + files)")
        print("  python run_pipeline.py full --prompt 'AI breakthroughs' --files research.pdf --mode pro")
        return 1

    # Create SmartInput
    smart_input = SmartInput(
        prompt=prompt,
        files=files,
        guidance=guidance,
    )

    # Determine input mode for display
    handler = SmartInputHandler()
    input_mode = handler.detect_mode(smart_input)

    start_time = time.time()

    print(f"\n{'='*70}")
    print(f"NELL PODCAST GENERATION - {mode.upper()} MODE")
    print(f"{'='*70}")
    print(f"Input mode: {input_mode.upper()}")
    if prompt:
        print(f"Topic/Prompt: {prompt[:60]}{'...' if len(prompt) > 60 else ''}")
    if files:
        print(f"Files: {', '.join(files)}")
    if guidance:
        print(f"Guidance: {guidance[:60]}{'...' if len(guidance) > 60 else ''}")
    if mode == "normal":
        print(f"Target time: ~2 minutes")
    else:
        print(f"Target time: ~6 minutes")
        # Show Pro mode specific settings
        speaker_format = getattr(args, 'speaker_format', 'auto')
        print(f"Speaker format: {speaker_format}")
        if not getattr(args, 'no_emotion_voice', False):
            print(f"Emotion voice sync: enabled")
        if not getattr(args, 'no_emotion_images', False):
            print(f"Emotion image alignment: enabled")
    print(f"{'='*70}\n")

    # Determine length based on mode
    length = "short" if mode == "normal" else "standard"

    try:
        # Process input using SmartInputHandler
        print("Processing input...")
        content = handler.process(smart_input, length=length)
        print(f"Content ready: {len(content.text)} characters from {content.source_type}")

        if mode == "normal":
            from pipelines.normal_pipeline import NormalPipeline, run_normal_pipeline
            from utils.progress_stream import ProgressStream, print_progress

            pipeline = NormalPipeline()
            progress = ProgressStream(callback=print_progress) if show_progress else None

            # Pass the already-processed content text directly
            # The pipeline's input_router will handle it as text
            result = asyncio.run(pipeline.run_with_content(content, progress))

        else:  # pro mode
            from pipelines.pro_pipeline import ProPipeline, ProConfig, run_pro_pipeline
            from utils.progress_stream import ProgressStream, print_progress

            # Load config if provided
            pro_config = None
            if config_path:
                from config.user_config import UserConfig
                user_config = UserConfig.load(config_path)
                pro_config = user_config.to_pro_config()
            else:
                pro_config = ProConfig()

            # Apply CLI overrides
            speaker_format = getattr(args, 'speaker_format', 'auto')
            pro_config.speaker_format = speaker_format

            # Parse manual speaker assignments
            speakers_arg = getattr(args, 'speakers', None)
            if speakers_arg:
                voice_overrides = {}
                for pair in speakers_arg.split(','):
                    if ':' in pair:
                        role, voice = pair.split(':', 1)
                        voice_overrides[role.strip()] = voice.strip()
                pro_config.voice_overrides = voice_overrides
                print(f"Voice overrides: {voice_overrides}")

            # Apply emotion settings from CLI
            if getattr(args, 'no_emotion_voice', False):
                pro_config.emotion_voice_sync = False
            if getattr(args, 'no_emotion_images', False):
                pro_config.emotion_image_alignment = False
            if getattr(args, 'no_emotion_validation', False):
                pro_config.emotion_validation = False

            pipeline = ProPipeline(config=pro_config)
            progress = ProgressStream(callback=print_progress) if show_progress else None

            # Pass the already-processed content
            result = asyncio.run(pipeline.run_with_content(content, progress))

        elapsed = time.time() - start_time

        print(f"\n{'='*70}")
        if result.success:
            print("GENERATION COMPLETE!")
            print(f"{'='*70}")
            print(f"Output: {result.output_path}")
            print(f"Time: {elapsed:.1f} seconds ({elapsed/60:.1f} minutes)")

            if hasattr(result, 'script') and result.script:
                print(f"Title: {result.script.get('title', 'Unknown')}")

            if mode == "normal":
                target = 120
                if elapsed <= target:
                    print(f"Status: WITHIN TARGET (target: {target}s)")
                else:
                    print(f"Status: Over target by {elapsed - target:.1f}s")
        else:
            print("GENERATION FAILED")
            print(f"{'='*70}")
            print(f"Error: {result.error}")
            return 1

        return 0

    except Exception as e:
        print(f"\n{'='*70}")
        print("GENERATION FAILED")
        print(f"{'='*70}")
        print(f"Error: {e}")
        return 1


def cmd_config(args):
    """
    Configure user preferences for podcast generation.
    """
    from config.user_config import run_config_wizard, get_default_config, save_default_config

    if args.show:
        # Show current config
        config = get_default_config()
        print("\n" + "="*50)
        print("Current Configuration")
        print("="*50)
        print(f"  Default mode: {config.default_mode}")
        print(f"  Voice preset: {config.voice_preset}")
        print(f"  Music genre: {config.music_genre}")
        print(f"  Image style: {config.image_style}")
        print(f"  Director review: {config.director_review}")
        print(f"  Max review rounds: {config.max_review_rounds}")
        return 0

    if args.reset:
        # Reset to defaults
        from config.user_config import UserConfig
        config = UserConfig()
        save_default_config(config)
        print("Configuration reset to defaults.")
        return 0

    # Run interactive wizard
    run_config_wizard()
    return 0


def cmd_preview(args):
    """
    Generate a preview for a specific module or hook.

    Creates audio previews with voice styling and BGM mixing
    for quality review before full pipeline execution.
    """
    from generate_clean_preview import generate_hook_preview, generate_module_preview

    print(f"\n{'='*60}")
    print("Preview Generation")
    print(f"{'='*60}")

    if args.module:
        if args.module not in [1, 2, 3, 4]:
            print(f"Error: Invalid module ID. Must be 1-4.")
            return 1

        print(f"\nGenerating preview for Module {args.module}...")
        output_path = generate_module_preview(args.module)
    elif args.hook:
        print("\nGenerating preview for Hook...")
        output_path = generate_hook_preview()
    elif args.all:
        print("\nGenerating all previews...")
        generate_hook_preview()
        for mid in [1, 2, 3, 4]:
            generate_module_preview(mid)
        output_path = BASE_DIR / "Output" / "audio" / "previews"
    else:
        print("Error: Specify --module N, --hook, or --all")
        return 1

    print(f"\n{'='*60}")
    print("PREVIEW GENERATION COMPLETE")
    print(f"{'='*60}")

    return 0


def cmd_bgm(args):
    """
    Generate background music using the 9-segment daisy-chain pipeline.

    Options:
        --generate: Generate all 9 BGM segments
        --stitch: Stitch segments with crossfades
        --mix: Mix with voice audio
        --video: Update final video with new audio
        --all: Run complete BGM pipeline
    """
    from advanced_bgm_pipeline_v2 import (
        generate_all_segments,
        stitch_segments,
        mix_final,
        update_video
    )

    print(f"\n{'='*60}")
    print("9-Segment Daisy-Chain BGM Pipeline")
    print(f"{'='*60}")

    if args.all:
        generate_all_segments()
        stitch_segments()
        mix_final()
        update_video()
    elif args.generate:
        generate_all_segments()
    elif args.stitch:
        stitch_segments()
    elif args.mix:
        mix_final()
    elif args.video:
        update_video()
    else:
        print("Error: Specify an action (--generate, --stitch, --mix, --video, or --all)")
        return 1

    print(f"\n{'='*60}")
    print("BGM PIPELINE COMPLETE")
    print(f"{'='*60}")

    return 0


def main():
    """Main entry point with subcommand routing."""
    parser = argparse.ArgumentParser(
        description="Nell - Agentic System for Hyper-Personalized Podcasts",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # MODE 1: Pure Generation (prompt only)
  python run_pipeline.py full --prompt "History of electronic music" --mode normal
  python run_pipeline.py full --prompt "AI breakthroughs" --guidance "For beginners" --mode pro

  # MODE 2: Pure Enhancement (files only - existing behavior)
  python run_pipeline.py full --input transcript.txt --mode normal
  python run_pipeline.py full --files document.pdf audio.mp3 --mode pro
  python run_pipeline.py full --input "https://example.com/article" --mode normal

  # MODE 3: Hybrid (prompt + files as context)
  python run_pipeline.py full --prompt "Key insights" --files research.pdf --mode pro
  python run_pipeline.py full --prompt "Future of AI" --files paper1.pdf paper2.pdf --mode normal

  # Configure preferences
  python run_pipeline.py config

  # Legacy commands (still supported)
  python run_pipeline.py enhance --input transcript.txt
  python run_pipeline.py audio --script Output/enhanced_script.json
  python run_pipeline.py visual --script Output/enhanced_script.json
  python run_pipeline.py preview --module 1
  python run_pipeline.py bgm --all

For detailed help on a subcommand:
  python run_pipeline.py <command> --help
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # =========================================================================
    # enhance command
    # =========================================================================
    enhance_parser = subparsers.add_parser(
        "enhance",
        help="Enhance transcript with emotional arc and structure"
    )
    enhance_parser.add_argument(
        "--input", "-i",
        required=True,
        help="Input transcript file"
    )
    enhance_parser.add_argument(
        "--output", "-o",
        help="Output JSON file (default: Output/enhanced_script.json)"
    )
    enhance_parser.add_argument(
        "--model", "-m",
        choices=["sonnet", "opus"],
        default="sonnet",
        help="Claude model to use (default: sonnet)"
    )
    enhance_parser.add_argument(
        "--max-reviews",
        type=int,
        default=3,
        help="Maximum review iterations (default: 3)"
    )

    # =========================================================================
    # audio command
    # =========================================================================
    audio_parser = subparsers.add_parser(
        "audio",
        help="Generate TTS narration and background music"
    )
    audio_parser.add_argument(
        "--script", "-s",
        required=True,
        help="Enhanced script JSON file"
    )
    audio_parser.add_argument(
        "--skip-tts",
        action="store_true",
        help="Skip TTS generation, use existing files"
    )
    audio_parser.add_argument(
        "--skip-bgm",
        action="store_true",
        help="Skip BGM generation, use existing files"
    )
    audio_parser.add_argument(
        "--sentence-level",
        action="store_true",
        help="Use sentence-level TTS generation"
    )

    # =========================================================================
    # visual command
    # =========================================================================
    visual_parser = subparsers.add_parser(
        "visual",
        help="Generate narrative-driven images"
    )
    visual_parser.add_argument(
        "--script", "-s",
        required=True,
        help="Enhanced script JSON file"
    )

    # =========================================================================
    # full command
    # =========================================================================
    full_parser = subparsers.add_parser(
        "full",
        help="Run complete pipeline (enhance -> audio -> visual -> video)"
    )
    full_parser.add_argument(
        "--input", "-i",
        help="Input file (txt, pdf, docx, mp3, mp4, or URL) - for backward compatibility"
    )
    full_parser.add_argument(
        "--prompt", "-p",
        help="Topic/prompt for content generation (triggers generation mode)"
    )
    full_parser.add_argument(
        "--files", "-f",
        nargs="+",
        help="Input files (PDF, audio, video, text, URL) - can specify multiple"
    )
    full_parser.add_argument(
        "--guidance", "-g",
        help="Style/focus guidance for generation or enhancement"
    )
    full_parser.add_argument(
        "--mode",
        choices=["normal", "pro", "legacy"],
        default="normal",
        help="Generation mode: normal (~2 min), pro (~6 min), legacy (original)"
    )
    full_parser.add_argument(
        "--config", "-c",
        help="Path to user config file (for Pro mode customization)"
    )
    full_parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Disable progress output"
    )
    full_parser.add_argument(
        "--model", "-m",
        choices=["sonnet", "opus"],
        default="sonnet",
        help="Claude model to use (default: sonnet, only for legacy mode)"
    )
    full_parser.add_argument(
        "--max-reviews",
        type=int,
        default=3,
        help="Maximum review iterations (default: 3, only for legacy mode)"
    )
    # NEW: Speaker format options (Pro mode only)
    full_parser.add_argument(
        "--speaker-format",
        choices=["auto", "single", "interview", "co_hosts", "narrator_characters"],
        default="auto",
        help="Speaker format (Pro mode): auto-detect, single narrator, interview, co-hosts, or narrator+characters"
    )
    full_parser.add_argument(
        "--speakers",
        help="Manual speaker-voice assignments (Pro mode): e.g., 'host:female_friendly,guest:male_professional'"
    )
    # NEW: Emotion options (Pro mode only)
    full_parser.add_argument(
        "--no-emotion-voice",
        action="store_true",
        help="Disable emotion-responsive voice parameters (Pro mode)"
    )
    full_parser.add_argument(
        "--no-emotion-images",
        action="store_true",
        help="Disable emotion-aligned image generation (Pro mode)"
    )
    full_parser.add_argument(
        "--no-emotion-validation",
        action="store_true",
        help="Disable emotion validation (Pro mode)"
    )

    # =========================================================================
    # preview command
    # =========================================================================
    preview_parser = subparsers.add_parser(
        "preview",
        help="Generate module or hook preview audio"
    )
    preview_parser.add_argument(
        "--module", "-m",
        type=int,
        choices=[1, 2, 3, 4],
        help="Module ID to preview (1-4)"
    )
    preview_parser.add_argument(
        "--hook",
        action="store_true",
        help="Generate hook preview"
    )
    preview_parser.add_argument(
        "--all",
        action="store_true",
        help="Generate all previews"
    )

    # =========================================================================
    # bgm command
    # =========================================================================
    bgm_parser = subparsers.add_parser(
        "bgm",
        help="Run 9-segment daisy-chain BGM pipeline"
    )
    bgm_parser.add_argument(
        "--generate",
        action="store_true",
        help="Generate all 9 BGM segments"
    )
    bgm_parser.add_argument(
        "--stitch",
        action="store_true",
        help="Stitch segments with crossfades"
    )
    bgm_parser.add_argument(
        "--mix",
        action="store_true",
        help="Mix BGM with voice audio"
    )
    bgm_parser.add_argument(
        "--video",
        action="store_true",
        help="Update video with new audio"
    )
    bgm_parser.add_argument(
        "--all",
        action="store_true",
        help="Run complete BGM pipeline"
    )

    # =========================================================================
    # config command
    # =========================================================================
    config_parser = subparsers.add_parser(
        "config",
        help="Configure user preferences for podcast generation"
    )
    config_parser.add_argument(
        "--show",
        action="store_true",
        help="Show current configuration"
    )
    config_parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset to default configuration"
    )

    # =========================================================================
    # Parse and route
    # =========================================================================
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return 0

    # Route to appropriate command handler
    commands = {
        "enhance": cmd_enhance,
        "audio": cmd_audio,
        "visual": cmd_visual,
        "full": cmd_full,
        "preview": cmd_preview,
        "bgm": cmd_bgm,
        "config": cmd_config,
    }

    handler = commands.get(args.command)
    if handler:
        return handler(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
