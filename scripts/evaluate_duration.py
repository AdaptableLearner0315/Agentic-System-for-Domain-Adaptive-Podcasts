#!/usr/bin/env python3
"""
Duration Evaluation CLI
Author: Sarath

Evaluates podcast output against target duration specifications.

Usage:
    python scripts/evaluate_duration.py --audio Output/final.mp3 --target 10
    python scripts/evaluate_duration.py --audio Output/final.mp3 --script Output/enhanced_script.json
    python scripts/evaluate_duration.py --script Output/enhanced_script.json  # Word-based estimate

Options:
    --audio PATH      Path to audio/video file to evaluate
    --target MINUTES  Target duration in minutes
    --script PATH     Path to enhanced_script.json (for word count and target extraction)
    --tolerance PCT   Acceptable deviation percentage (default: 15)
    --json            Output results as JSON
"""

import argparse
import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.duration_evaluator import (
    DurationEvaluator,
    DurationEvaluation,
    DEFAULT_TOLERANCE_PERCENT,
)


def main():
    parser = argparse.ArgumentParser(
        description="Evaluate podcast duration against target",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Evaluate audio against explicit target
  python scripts/evaluate_duration.py --audio Output/final.mp3 --target 10

  # Use target from script metadata
  python scripts/evaluate_duration.py --audio Output/final.mp3 --script Output/enhanced_script.json

  # Word-based estimate (no audio)
  python scripts/evaluate_duration.py --script Output/enhanced_script.json

  # Output as JSON
  python scripts/evaluate_duration.py --audio Output/final.mp3 --target 5 --json
        """
    )

    parser.add_argument(
        "--audio",
        type=str,
        help="Path to audio/video file to evaluate"
    )
    parser.add_argument(
        "--target",
        type=float,
        help="Target duration in minutes"
    )
    parser.add_argument(
        "--script",
        type=str,
        help="Path to enhanced_script.json"
    )
    parser.add_argument(
        "--tolerance",
        type=float,
        default=DEFAULT_TOLERANCE_PERCENT,
        help=f"Acceptable deviation percentage (default: {DEFAULT_TOLERANCE_PERCENT})"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON"
    )

    args = parser.parse_args()

    # Validate arguments
    if not args.audio and not args.script:
        parser.error("Must provide --audio and/or --script")

    if args.audio and not args.target and not args.script:
        parser.error("Must provide --target or --script when evaluating audio")

    evaluator = DurationEvaluator(tolerance_percent=args.tolerance)

    try:
        # Determine target duration
        target_minutes = args.target
        script_data = None

        if args.script:
            script_path = Path(args.script)
            if not script_path.exists():
                print(f"Error: Script file not found: {args.script}", file=sys.stderr)
                sys.exit(1)

            with open(script_path, 'r') as f:
                script_data = json.load(f)

            # Use script target if not explicitly provided
            if not target_minutes:
                target_minutes = script_data.get("target_duration_minutes")
                if not target_minutes:
                    print("Error: No target duration in script and --target not provided", file=sys.stderr)
                    sys.exit(1)

        if args.audio:
            # Full evaluation with audio
            audio_path = Path(args.audio)
            if not audio_path.exists():
                print(f"Error: Audio file not found: {args.audio}", file=sys.stderr)
                sys.exit(1)

            result = evaluator.evaluate(
                audio_path=str(audio_path),
                target_minutes=target_minutes,
                script_path=args.script
            )
        else:
            # Word-based estimate from script only
            if not script_data:
                print("Error: --script required for word-based estimate", file=sys.stderr)
                sys.exit(1)

            result = evaluator.evaluate_from_script(script_data)

        # Output results
        if args.json:
            print(json.dumps(result.to_dict(), indent=2))
        else:
            print(result)
            print()
            if result.is_within_tolerance:
                print("Result: PASS - Duration is within acceptable range")
            else:
                print("Result: FAIL - Duration is outside acceptable range")

        # Exit with appropriate code
        sys.exit(0 if result.is_within_tolerance else 1)

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
