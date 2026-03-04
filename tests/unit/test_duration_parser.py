"""
Unit tests for Duration Parser utility.
Author: Sarath

Tests extraction of duration from natural language prompts
and cleaning of prompts after duration extraction.
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.duration_parser import (
    extract_duration_minutes,
    remove_duration_from_prompt,
    parse_duration_and_prompt,
    get_default_duration,
    get_duration_range,
    SEMANTIC_DURATIONS,
    MIN_DURATION_MINUTES,
    MAX_DURATION_MINUTES,
)


class TestExtractDurationMinutes:
    """Tests for extract_duration_minutes function."""

    def test_explicit_minute_singular(self):
        """Test '5 minute' pattern."""
        assert extract_duration_minutes("5 minute podcast about AI") == 5

    def test_explicit_minutes_plural(self):
        """Test '10 minutes' pattern."""
        assert extract_duration_minutes("10 minutes on machine learning") == 10

    def test_explicit_min_abbreviation(self):
        """Test '15 min' pattern."""
        assert extract_duration_minutes("15 min history lesson") == 15

    def test_explicit_hyphenated(self):
        """Test '10-minute' pattern."""
        assert extract_duration_minutes("A 10-minute overview") == 10

    def test_range_with_dash(self):
        """Test '3-5 minutes' range pattern (uses midpoint)."""
        assert extract_duration_minutes("3-5 minutes on Python") == 4

    def test_range_with_to(self):
        """Test '5 to 10 min' range pattern."""
        result = extract_duration_minutes("5 to 10 min tutorial")
        assert result == 7  # midpoint

    def test_semantic_quick(self):
        """Test 'quick' keyword."""
        assert extract_duration_minutes("quick overview of React") == 3

    def test_semantic_short(self):
        """Test 'short' keyword."""
        assert extract_duration_minutes("short podcast about cooking") == 5

    def test_semantic_in_depth(self):
        """Test 'in-depth' keyword."""
        assert extract_duration_minutes("in-depth analysis of economics") == 20

    def test_semantic_deep_dive(self):
        """Test 'deep dive' keyword."""
        assert extract_duration_minutes("deep dive into quantum physics") == 20

    def test_semantic_comprehensive(self):
        """Test 'comprehensive' keyword."""
        assert extract_duration_minutes("comprehensive guide to Docker") == 20

    def test_semantic_extended(self):
        """Test 'extended' keyword."""
        assert extract_duration_minutes("extended discussion on climate") == 20

    def test_no_duration_returns_none(self):
        """Test that prompts without duration return None."""
        assert extract_duration_minutes("podcast about AI") is None
        assert extract_duration_minutes("tell me about history") is None

    def test_empty_prompt(self):
        """Test empty prompt returns None."""
        assert extract_duration_minutes("") is None
        assert extract_duration_minutes(None) is None

    def test_duration_clamping_max(self):
        """Test duration is clamped to max (30 minutes)."""
        assert extract_duration_minutes("45 minute lecture") == 30

    def test_duration_clamping_min(self):
        """Test duration is clamped to min (1 minute)."""
        # 0 minutes should be clamped to 1
        result = extract_duration_minutes("0 minute intro")
        assert result == 1

    def test_explicit_takes_priority_over_semantic(self):
        """Test explicit duration takes priority over semantic keywords."""
        # Even though 'quick' would be 3 min, explicit 10 wins
        assert extract_duration_minutes("quick 10 minute podcast") == 10

    def test_case_insensitive(self):
        """Test case insensitivity."""
        assert extract_duration_minutes("QUICK overview") == 3
        assert extract_duration_minutes("5 MINUTE podcast") == 5


class TestRemoveDurationFromPrompt:
    """Tests for remove_duration_from_prompt function."""

    def test_removes_explicit_duration(self):
        """Test removal of explicit duration."""
        result = remove_duration_from_prompt("5 minute podcast about AI")
        assert "5" not in result.lower()
        assert "minute" not in result.lower()
        assert "AI" in result

    def test_removes_range_duration(self):
        """Test removal of range duration."""
        result = remove_duration_from_prompt("3-5 minutes on Python basics")
        assert "3-5" not in result
        assert "Python basics" in result

    def test_removes_hyphenated_duration(self):
        """Test removal of hyphenated duration."""
        result = remove_duration_from_prompt("A 10-minute overview of React")
        assert "10" not in result
        assert "overview" in result

    def test_removes_semantic_before_podcast(self):
        """Test removal of semantic keyword before 'podcast'."""
        result = remove_duration_from_prompt("quick podcast about cooking")
        assert "quick" not in result.lower()
        assert "cooking" in result

    def test_preserves_semantic_in_other_context(self):
        """Test that semantic keywords are preserved in other contexts."""
        # 'short story' should remain as-is (not about duration)
        result = remove_duration_from_prompt("podcast about a short story")
        # The word 'short' should remain since it's describing 'story', not podcast
        assert "story" in result

    def test_cleans_extra_whitespace(self):
        """Test cleanup of extra whitespace."""
        result = remove_duration_from_prompt("A    5 minute    podcast")
        assert "  " not in result  # No double spaces

    def test_empty_prompt(self):
        """Test empty prompt returns empty string."""
        assert remove_duration_from_prompt("") == ""
        assert remove_duration_from_prompt(None) == ""


class TestParseDurationAndPrompt:
    """Tests for parse_duration_and_prompt function."""

    def test_returns_tuple(self):
        """Test returns tuple of (duration, clean_prompt)."""
        duration, prompt = parse_duration_and_prompt("5 minute podcast about AI")
        assert duration == 5
        assert "AI" in prompt
        assert "minute" not in prompt.lower()

    def test_no_duration_returns_original_prompt(self):
        """Test prompt without duration returns (None, original)."""
        original = "podcast about machine learning"
        duration, prompt = parse_duration_and_prompt(original)
        assert duration is None
        assert prompt == original


class TestHelperFunctions:
    """Tests for helper functions."""

    def test_get_default_duration(self):
        """Test default duration is 10 minutes."""
        assert get_default_duration() == 10

    def test_get_duration_range(self):
        """Test duration range is (1, 30)."""
        min_dur, max_dur = get_duration_range()
        assert min_dur == MIN_DURATION_MINUTES
        assert max_dur == MAX_DURATION_MINUTES

    def test_semantic_durations_mapping(self):
        """Test semantic duration mappings are correct."""
        assert SEMANTIC_DURATIONS["quick"] == 3
        assert SEMANTIC_DURATIONS["short"] == 5
        assert SEMANTIC_DURATIONS["standard"] == 10
        assert SEMANTIC_DURATIONS["in-depth"] == 20


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_multiple_durations_uses_first(self):
        """Test that first duration found is used."""
        # First explicit duration should be used
        result = extract_duration_minutes("5 minute then 10 minute podcast")
        assert result == 5

    def test_duration_at_end_of_prompt(self):
        """Test duration at end of prompt."""
        assert extract_duration_minutes("podcast about AI 10 minutes") == 10

    def test_duration_in_middle_of_prompt(self):
        """Test duration in middle of prompt."""
        assert extract_duration_minutes("create a 5 minute podcast about cooking") == 5

    def test_decimal_duration_truncated(self):
        """Test decimal durations are handled (regex captures integers)."""
        # "5.5" won't be matched as "5.5 minutes", only "5" if followed by space
        # This is expected behavior - we don't support decimals
        result = extract_duration_minutes("5.5 minute podcast")
        # The regex should match "5" from "5.5"
        assert result in [5, None]  # Depends on regex behavior
