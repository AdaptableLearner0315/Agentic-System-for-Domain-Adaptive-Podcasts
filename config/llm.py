"""
LLM Configuration
Author: Sarath

Configuration for Large Language Model usage in the podcast enhancement system.
"""

# Default Claude model for script enhancement
DEFAULT_MODEL = "claude-sonnet-4-20250514"

# Model options
MODEL_OPTIONS = {
    "sonnet": "claude-sonnet-4-20250514",
    "opus": "claude-opus-4-5-20250514",
    "haiku": "claude-3-5-haiku-20241022",
}

# Default parameters for LLM calls
DEFAULT_MAX_TOKENS = 8192
DEFAULT_TEMPERATURE = 0.7

# Director review thresholds
DIRECTOR_APPROVAL_SCORE = 7
DIRECTOR_CRITICAL_THRESHOLD = 6


def get_model_id(model_name: str) -> str:
    """
    Get the full model ID from a short name.

    Args:
        model_name: Short model name ('sonnet', 'opus', 'haiku')

    Returns:
        Full model ID string
    """
    return MODEL_OPTIONS.get(model_name.lower(), DEFAULT_MODEL)
