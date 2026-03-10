"""
Speaker Assignment Agent
Author: Sarath

Assigns speakers to script chunks based on content analysis.
Supports automatic format detection and manual override.

Features:
- Auto-detect speaker format (interview, co-hosts, narrator+characters, single)
- Intelligent speaker assignment using pattern matching
- LLM-based assignment for complex cases
- Manual override support
"""

import re
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from agents.base_agent import BaseAgent
from config.llm import MODEL_OPTIONS
from config.speaker_config import (
    SPEAKER_FORMATS,
    AVAILABLE_VOICES,
    DEFAULT_VOICE,
    get_voice_id,
    get_default_voice_for_role,
    get_format_speakers,
)


@dataclass
class SpeakerAssignment:
    """Represents a speaker assignment for a chunk."""
    speaker_role: str
    voice_key: str
    voice_id: str
    confidence: float  # 0.0-1.0


@dataclass
class FormatDetectionResult:
    """Result of format detection."""
    detected_format: str
    confidence: float
    pattern_matches: Dict[str, int]
    recommendation: str


class SpeakerAssignmentAgent(BaseAgent):
    """
    Assigns speakers to script chunks based on content analysis.

    Features:
    - Automatic format detection
    - Pattern-based speaker identification
    - LLM-assisted assignment for complex cases
    - Manual override support
    """

    def __init__(self, model: str = None):
        """
        Initialize the Speaker Assignment Agent.

        Args:
            model: LLM model for complex assignments (default: sonnet from config)
        """
        if model is None:
            model = MODEL_OPTIONS["sonnet"]
        super().__init__(
            name="SpeakerAssignment",
            output_category="",
            model=model
        )

    def detect_format(self, content: str) -> FormatDetectionResult:
        """
        Auto-detect the best speaker format for content.

        Args:
            content: Raw content text to analyze

        Returns:
            FormatDetectionResult with detected format and confidence
        """
        pattern_matches: Dict[str, int] = {}

        # Count pattern matches for each format
        for format_id, format_config in SPEAKER_FORMATS.items():
            patterns = format_config.get("detection_patterns", [])
            match_count = 0

            for pattern in patterns:
                matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
                match_count += len(matches)

            # Weight by format priority
            weight = format_config.get("detection_weight", 1)
            pattern_matches[format_id] = match_count * weight

        # Find format with highest score
        if not pattern_matches or all(v == 0 for v in pattern_matches.values()):
            # No patterns matched, default to single narrator
            return FormatDetectionResult(
                detected_format="single",
                confidence=1.0,
                pattern_matches=pattern_matches,
                recommendation="No multi-speaker patterns detected. Using single narrator."
            )

        best_format = max(pattern_matches.keys(), key=lambda k: pattern_matches[k])
        best_score = pattern_matches[best_format]
        total_score = sum(pattern_matches.values())

        # Calculate confidence
        confidence = best_score / total_score if total_score > 0 else 0.0

        # Require minimum threshold for multi-speaker
        if best_format != "single" and best_score < 3:
            return FormatDetectionResult(
                detected_format="single",
                confidence=0.8,
                pattern_matches=pattern_matches,
                recommendation=f"Weak {best_format} signal ({best_score} matches). Using single narrator."
            )

        return FormatDetectionResult(
            detected_format=best_format,
            confidence=min(confidence, 0.95),  # Cap at 95%
            pattern_matches=pattern_matches,
            recommendation=f"Detected {best_format} format with {best_score} pattern matches."
        )

    def assign_speakers(
        self,
        script: Dict[str, Any],
        format_id: Optional[str] = None,
        manual_assignments: Optional[Dict[str, str]] = None,
        voice_overrides: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Assign speakers to each chunk in the script.

        Args:
            script: Enhanced script dictionary
            format_id: Speaker format to use (auto-detect if None)
            manual_assignments: Optional manual speaker assignments per chunk location
            voice_overrides: Optional voice overrides per speaker role

        Returns:
            Script with speaker and voice_id fields added to chunks
        """
        import copy
        result_script = copy.deepcopy(script)

        # Detect format if not specified
        if not format_id:
            # Combine all text for analysis
            all_text = self._extract_all_text(script)
            detection = self.detect_format(all_text)
            format_id = detection.detected_format
            self.log(f"Detected format: {format_id} (confidence: {detection.confidence:.1%})")
            self.log(f"  {detection.recommendation}")

        # Get format configuration
        format_config = SPEAKER_FORMATS.get(format_id, SPEAKER_FORMATS["single"])
        speakers = format_config.get("speakers", {})

        self.log(f"Using format: {format_config['name']}")
        for role, speaker_info in speakers.items():
            voice_key = voice_overrides.get(role) if voice_overrides else None
            voice_key = voice_key or speaker_info.get("default_voice", DEFAULT_VOICE)
            self.log(f"  {role}: {voice_key}")

        # Assign to hook
        if result_script.get("hook"):
            location = "hook"
            if manual_assignments and location in manual_assignments:
                speaker_role = manual_assignments[location]
            else:
                speaker_role = self._determine_speaker_for_chunk(
                    result_script["hook"], format_id, "hook"
                )

            voice_key = self._get_voice_for_role(speaker_role, format_id, voice_overrides)
            result_script["hook"]["speaker"] = speaker_role
            result_script["hook"]["voice_id"] = get_voice_id(voice_key)

        # Assign to module chunks
        for module in result_script.get("modules", []):
            module_id = module.get("id", 0)

            for chunk_idx, chunk in enumerate(module.get("chunks", [])):
                location = f"module_{module_id}_chunk_{chunk_idx + 1}"

                if manual_assignments and location in manual_assignments:
                    speaker_role = manual_assignments[location]
                else:
                    speaker_role = self._determine_speaker_for_chunk(
                        chunk, format_id, location
                    )

                voice_key = self._get_voice_for_role(speaker_role, format_id, voice_overrides)
                chunk["speaker"] = speaker_role
                chunk["voice_id"] = get_voice_id(voice_key)

        # Add format metadata to script
        result_script["speaker_format"] = format_id
        result_script["speaker_config"] = {
            "format_name": format_config["name"],
            "speakers": {
                role: {
                    "voice_key": self._get_voice_for_role(role, format_id, voice_overrides),
                    "voice_id": get_voice_id(self._get_voice_for_role(role, format_id, voice_overrides))
                }
                for role in speakers.keys()
            }
        }

        return result_script

    def _extract_all_text(self, script: Dict[str, Any]) -> str:
        """Extract all text from script for analysis."""
        texts = []

        hook = script.get("hook", {})
        if hook.get("text"):
            texts.append(hook["text"])

        for module in script.get("modules", []):
            for chunk in module.get("chunks", []):
                if chunk.get("text"):
                    texts.append(chunk["text"])

        return "\n".join(texts)

    def _determine_speaker_for_chunk(
        self,
        chunk: Dict[str, Any],
        format_id: str,
        location: str
    ) -> str:
        """
        Determine the speaker for a single chunk.

        Uses pattern matching for simple cases, can use LLM for complex.
        """
        text = chunk.get("text", "")
        format_config = SPEAKER_FORMATS.get(format_id, SPEAKER_FORMATS["single"])
        speakers = list(format_config.get("speakers", {}).keys())

        if not speakers:
            return "narrator"

        # Single narrator format
        if format_id == "single":
            return "narrator"

        # Interview format - look for Q/A patterns
        if format_id == "interview":
            if re.search(r'^(Q:|Host:|Question:)', text, re.IGNORECASE):
                return "host"
            if re.search(r'^(A:|Guest:|Answer:)', text, re.IGNORECASE):
                return "guest"
            # Default to host for narrative chunks
            return "host"

        # Co-hosts format - alternate between hosts
        if format_id == "co_hosts":
            # Use location to determine alternation
            if "chunk" in location:
                chunk_num = int(location.split("chunk_")[-1]) if "chunk_" in location else 1
                return "host_1" if chunk_num % 2 == 1 else "host_2"
            return "host_1"

        # Narrator + Characters - look for quotes
        if format_id == "narrator_characters":
            # Check for quoted speech
            if re.search(r'"[^"]{10,}"', text) or re.search(r"'[^']{10,}'", text):
                # Check if it's a quote within narration
                quote_ratio = len(re.findall(r'"[^"]+"', text)) / max(len(text.split()), 1)
                if quote_ratio > 0.3:
                    return "character"
            return "narrator"

        # Default to first speaker
        return speakers[0] if speakers else "narrator"

    def _get_voice_for_role(
        self,
        role: str,
        format_id: str,
        voice_overrides: Optional[Dict[str, str]] = None
    ) -> str:
        """Get voice key for a speaker role."""
        if voice_overrides and role in voice_overrides:
            return voice_overrides[role]

        return get_default_voice_for_role(format_id, role)

    def assign_speakers_with_llm(
        self,
        script: Dict[str, Any],
        format_id: str
    ) -> Dict[str, Any]:
        """
        Use LLM for intelligent speaker assignment.

        This is used for complex cases where pattern matching isn't sufficient.

        Args:
            script: Enhanced script
            format_id: Speaker format to use

        Returns:
            Script with speaker assignments
        """
        import json

        format_config = SPEAKER_FORMATS.get(format_id, SPEAKER_FORMATS["single"])
        speakers = format_config.get("speakers", {})

        # Build prompt for LLM
        prompt = f"""You are analyzing a podcast script to assign speakers.

Format: {format_config['name']}
Description: {format_config['description']}

Available speakers:
{json.dumps(speakers, indent=2)}

For each chunk, determine which speaker should deliver it based on:
- Content and tone
- Dialogue patterns
- Natural conversation flow

Script to analyze:
{json.dumps(script, indent=2)}

Return a JSON object mapping chunk locations to speaker roles:
{{
    "hook": "speaker_role",
    "module_1_chunk_1": "speaker_role",
    ...
}}
"""

        response = self.call_llm(prompt, max_tokens=2048)

        try:
            assignments = self.parse_json_response(response)
            return self.assign_speakers(
                script,
                format_id=format_id,
                manual_assignments=assignments
            )
        except ValueError:
            self.log("LLM assignment failed, using pattern-based", level="warning")
            return self.assign_speakers(script, format_id=format_id)

    def process(
        self,
        script: Dict[str, Any],
        format_id: Optional[str] = None,
        manual_assignments: Optional[Dict[str, str]] = None,
        voice_overrides: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Main processing method - assign speakers to script.

        Args:
            script: Enhanced script dictionary
            format_id: Optional format override
            manual_assignments: Optional manual speaker assignments
            voice_overrides: Optional voice overrides

        Returns:
            Script with speaker assignments
        """
        return self.assign_speakers(
            script,
            format_id=format_id,
            manual_assignments=manual_assignments,
            voice_overrides=voice_overrides
        )


if __name__ == "__main__":
    # Test format detection
    test_content_interview = """
    Q: What inspired you to start this project?
    A: It began when I realized the potential for AI in creative fields.
    Q: Can you tell us more about the technical challenges?
    A: Certainly. The main challenge was integrating multiple AI models.
    """

    test_content_narrative = """
    The sun set over the mountains as the narrator began to speak.
    "This is going to change everything," said the scientist, his voice trembling.
    The discovery would reshape our understanding of the universe.
    """

    agent = SpeakerAssignmentAgent()

    # Test detection
    result_interview = agent.detect_format(test_content_interview)
    print(f"Interview content detected as: {result_interview.detected_format}")
    print(f"  Confidence: {result_interview.confidence:.1%}")

    result_narrative = agent.detect_format(test_content_narrative)
    print(f"\nNarrative content detected as: {result_narrative.detected_format}")
    print(f"  Confidence: {result_narrative.confidence:.1%}")

    # Test assignment
    sample_script = {
        "hook": {"text": "Welcome to the show"},
        "modules": [
            {
                "id": 1,
                "chunks": [
                    {"text": "Q: First question?"},
                    {"text": "A: First answer."},
                ]
            }
        ]
    }

    assigned = agent.assign_speakers(sample_script, format_id="interview")
    print(f"\nAssigned script format: {assigned.get('speaker_format')}")
    print(f"Hook speaker: {assigned['hook'].get('speaker')}")
