"""
Duration Parser Utility
Author: Sarath

Extracts and parses duration specifications from natural language prompts.
Supports explicit time formats and semantic duration keywords.

Examples:
- "5 minute podcast about AI" -> 5
- "10 min history lesson" -> 10
- "quick overview of Python" -> 3
- "in-depth analysis of economics" -> 20
"""

import re
from typing import Optional, Tuple


# Semantic duration mappings (keyword -> minutes)
SEMANTIC_DURATIONS = {
    # Short durations
    "quick": 3,
    "brief": 3,
    "short": 5,
    "mini": 3,
    "bite-sized": 3,
    "bite sized": 3,
    # Standard durations
    "standard": 10,
    "normal": 10,
    "regular": 10,
    "medium": 10,
    # Long durations
    "long": 15,
    "extended": 20,
    "in-depth": 20,
    "in depth": 20,
    "detailed": 15,
    "comprehensive": 20,
    "thorough": 20,
    "deep dive": 20,
    "deep-dive": 20,
}

# Default duration when not specified
DEFAULT_DURATION_MINUTES = 10

# Duration limits
MIN_DURATION_MINUTES = 1
MAX_DURATION_MINUTES = 30

# Regex patterns for explicit duration extraction
# Matches: "5 minute", "10 min", "3-5 minutes", "15-minute", etc.
DURATION_PATTERNS = [
    # Range pattern: "3-5 minutes", "5 to 10 min"
    r"(\d+)\s*[-to]+\s*(\d+)\s*(?:minute|min)s?",
    # Single value with unit: "5 minute", "10 min", "15-minute"
    r"(\d+)\s*[-]?\s*(?:minute|min)s?",
]

# Patterns to identify semantic duration keywords in context
SEMANTIC_PATTERNS = [
    r"\b(quick)\b",
    r"\b(brief)\b",
    r"\b(short)\b",
    r"\b(mini)\b",
    r"\b(bite[- ]?sized)\b",
    r"\b(standard)\b",
    r"\b(normal)\b",
    r"\b(regular)\b",
    r"\b(medium)\b",
    r"\b(long)\b",
    r"\b(extended)\b",
    r"\b(in[- ]?depth)\b",
    r"\b(detailed)\b",
    r"\b(comprehensive)\b",
    r"\b(thorough)\b",
    r"\b(deep[- ]?dive)\b",
]


def extract_duration_minutes(prompt: str) -> Optional[int]:
    """
    Extract target duration in minutes from a natural language prompt.

    Supports:
    - Explicit time: "5 minute podcast", "10 min", "3-5 minutes" (uses midpoint)
    - Semantic: "quick" (3), "short" (5), "standard" (10), "in-depth" (20)

    Args:
        prompt: Natural language prompt text

    Returns:
        Duration in minutes, or None if no duration specification found
    """
    if not prompt:
        return None

    prompt_lower = prompt.lower()

    # Try explicit duration patterns first (more precise)
    for pattern in DURATION_PATTERNS:
        match = re.search(pattern, prompt_lower)
        if match:
            groups = match.groups()
            if len(groups) == 2 and groups[1]:
                # Range pattern - use midpoint
                try:
                    low = int(groups[0])
                    high = int(groups[1])
                    duration = (low + high) // 2
                    return _clamp_duration(duration)
                except ValueError:
                    continue
            elif len(groups) >= 1:
                # Single value pattern
                try:
                    duration = int(groups[0])
                    return _clamp_duration(duration)
                except ValueError:
                    continue

    # Try semantic duration keywords
    for pattern in SEMANTIC_PATTERNS:
        match = re.search(pattern, prompt_lower)
        if match:
            keyword = match.group(1).lower().replace(" ", "-")
            # Normalize variations
            if keyword in SEMANTIC_DURATIONS:
                return SEMANTIC_DURATIONS[keyword]
            # Try without hyphen
            keyword_no_hyphen = keyword.replace("-", " ")
            if keyword_no_hyphen in SEMANTIC_DURATIONS:
                return SEMANTIC_DURATIONS[keyword_no_hyphen]

    return None


def remove_duration_from_prompt(prompt: str) -> str:
    """
    Remove duration specifications from prompt to get clean topic.

    Removes both explicit ("5 minute") and semantic ("quick") duration markers.

    Args:
        prompt: Original prompt text

    Returns:
        Cleaned prompt with duration specifications removed
    """
    if not prompt:
        return ""

    result = prompt

    # Remove explicit duration patterns
    # "5 minute podcast" -> "podcast"
    # "a 10-minute overview" -> "a overview"
    result = re.sub(
        r"\b\d+\s*[-to]+\s*\d+\s*[-]?\s*(?:minute|min)s?\b",
        "",
        result,
        flags=re.IGNORECASE
    )
    result = re.sub(
        r"\b\d+\s*[-]?\s*(?:minute|min)s?\b",
        "",
        result,
        flags=re.IGNORECASE
    )

    # Remove semantic keywords when they appear as duration qualifiers
    # We're more careful here to avoid removing legitimate uses
    # e.g., "short story" should remain, but "short podcast about X" -> "podcast about X"
    semantic_removal_patterns = [
        r"\b(quick|brief|short|mini|bite[- ]?sized)\s+(?=podcast|episode|overview|summary|intro)",
        r"\b(long|extended|in[- ]?depth|detailed|comprehensive|thorough|deep[- ]?dive)\s+(?=podcast|episode|analysis|exploration|look)",
    ]

    for pattern in semantic_removal_patterns:
        result = re.sub(pattern, "", result, flags=re.IGNORECASE)

    # Clean up extra whitespace
    result = re.sub(r"\s+", " ", result).strip()
    # Remove leading "a " or "an " if that's all that remains before content
    result = re.sub(r"^(a|an)\s+(?=[a-z])", "", result, flags=re.IGNORECASE)

    return result


def parse_duration_and_prompt(prompt: str) -> Tuple[Optional[int], str]:
    """
    Extract duration and return cleaned prompt in one call.

    Args:
        prompt: Original prompt text

    Returns:
        Tuple of (duration_minutes, cleaned_prompt)
    """
    duration = extract_duration_minutes(prompt)
    clean_prompt = remove_duration_from_prompt(prompt) if duration else prompt
    return duration, clean_prompt


def _clamp_duration(duration: int) -> int:
    """Clamp duration to valid range."""
    return max(MIN_DURATION_MINUTES, min(MAX_DURATION_MINUTES, duration))


def get_default_duration() -> int:
    """Get the default duration in minutes."""
    return DEFAULT_DURATION_MINUTES


def get_duration_range() -> Tuple[int, int]:
    """Get the valid duration range (min, max)."""
    return (MIN_DURATION_MINUTES, MAX_DURATION_MINUTES)


__all__ = [
    'extract_duration_minutes',
    'remove_duration_from_prompt',
    'parse_duration_and_prompt',
    'get_default_duration',
    'get_duration_range',
    'SEMANTIC_DURATIONS',
    'DEFAULT_DURATION_MINUTES',
    'MIN_DURATION_MINUTES',
    'MAX_DURATION_MINUTES',
]
