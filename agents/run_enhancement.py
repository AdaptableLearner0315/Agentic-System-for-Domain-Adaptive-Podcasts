"""
Script Enhancement Pipeline

Runs the Script Enhancer with Director review loop.
The Director reviews each enhancement and provides feedback until satisfied or max iterations reached.
"""

import os
import json
import argparse
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from agents.script_enhancer import ScriptEnhancer
from agents.director import Director
from config.llm import MODEL_OPTIONS

# Model mapping - uses centralized config
MODELS = MODEL_OPTIONS


def load_transcript(path: str) -> str:
    """Load transcript from file."""
    with open(path, "r") as f:
        return f.read()


def save_result(result: dict, output_path: str):
    """Save result to JSON file."""
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\nSaved to: {output_path}")


def run_enhancement_loop(
    transcript: str,
    model: str = "sonnet",
    max_reviews: int = 3
) -> dict:
    """
    Run the enhancement loop with director review.

    Args:
        transcript: Raw transcript text
        model: Model to use ("sonnet" or "opus")
        max_reviews: Maximum review iterations

    Returns:
        Final enhanced script with review history
    """
    model_id = MODELS.get(model, MODELS["sonnet"])
    print(f"\n{'='*60}")
    print(f"Script Enhancement Pipeline")
    print(f"{'='*60}")
    print(f"Model: {model_id}")
    print(f"Max reviews: {max_reviews}")
    print(f"{'='*60}\n")

    # Initialize agents
    enhancer = ScriptEnhancer(model=model_id)
    director = Director(model=model_id)

    # Track review history
    review_history = []
    feedback = None
    enhanced_script = None
    approved = False
    review_count = 0

    while not approved and review_count < max_reviews:
        review_count += 1
        print(f"\n--- Round {review_count}/{max_reviews} ---")

        # Enhance script
        print("Enhancing script...")
        enhanced_script = enhancer.enhance(transcript, feedback)

        if "error" in enhanced_script:
            print(f"Enhancement error: {enhanced_script['error']}")
            break

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

        if review_result.get("evaluation"):
            print("\nEvaluation:")
            for criterion, eval_data in review_result["evaluation"].items():
                score = eval_data.get("score", "N/A")
                print(f"  - {criterion}: {score}/10")

        if review_result.get("approved"):
            approved = True
            print("\n*** APPROVED by Director! ***")
        else:
            feedback = review_result.get("feedback", "")
            print(f"\nFeedback: {feedback[:200]}...")

    # Prepare final result
    if enhanced_script and "error" not in enhanced_script:
        enhanced_script["review_history"] = review_history
        enhanced_script["final_status"] = {
            "approved": approved,
            "total_rounds": review_count,
            "final_score": review_history[-1]["score"] if review_history else 0
        }

    return enhanced_script


def main():
    parser = argparse.ArgumentParser(
        description="Enhance podcast script with AI-powered review loop"
    )
    parser.add_argument(
        "--model",
        choices=["sonnet", "opus"],
        default="sonnet",
        help="Claude model to use (default: sonnet)"
    )
    parser.add_argument(
        "--max-reviews",
        type=int,
        default=3,
        help="Maximum review iterations (default: 3)"
    )
    parser.add_argument(
        "--input",
        default="transcript_fal.txt",
        help="Input transcript file (default: transcript_fal.txt)"
    )
    parser.add_argument(
        "--output",
        default="Output/enhanced_script.json",
        help="Output JSON file (default: Output/enhanced_script.json)"
    )

    args = parser.parse_args()

    # Resolve paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    input_path = os.path.join(base_dir, args.input)
    output_path = os.path.join(base_dir, args.output)

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Check input exists
    if not os.path.exists(input_path):
        print(f"Error: Input file not found: {input_path}")
        return

    # Load transcript
    print(f"Loading transcript from: {input_path}")
    transcript = load_transcript(input_path)
    print(f"Transcript length: {len(transcript)} characters")

    # Run enhancement
    result = run_enhancement_loop(
        transcript=transcript,
        model=args.model,
        max_reviews=args.max_reviews
    )

    # Save result
    if result:
        save_result(result, output_path)

        # Print summary
        print(f"\n{'='*60}")
        print("ENHANCEMENT COMPLETE")
        print(f"{'='*60}")
        print(f"Final Status: {'APPROVED' if result.get('final_status', {}).get('approved') else 'MAX ITERATIONS REACHED'}")
        print(f"Total Rounds: {result.get('final_status', {}).get('total_rounds', 0)}")
        print(f"Final Score: {result.get('final_status', {}).get('final_score', 0)}/10")

        if result.get("hook"):
            print(f"\nHook Preview:")
            print(f"  {result['hook'].get('text', '')[:150]}...")

        if result.get("modules"):
            print(f"\nModules: {len(result['modules'])}")
            for module in result["modules"]:
                print(f"  - {module.get('id', '?')}: {module.get('title', 'Untitled')}")
    else:
        print("Enhancement failed!")


if __name__ == "__main__":
    main()
