"""
Emotion Validator Agent
Author: Sarath

Validates emotion consistency across the podcast enhancement pipeline.
Ensures emotions are supported, properly distributed, and logically flow.

Features:
- Validates all emotions are in the supported list
- Checks tension-emotion alignment
- Validates emotion arc progression
- Provides auto-fix suggestions
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

from agents.base_agent import BaseAgent
from config.emotion_voice_mapping import SUPPORTED_EMOTIONS, is_valid_emotion


class ValidationSeverity(Enum):
    """Severity levels for validation issues."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ValidationIssue:
    """Represents a single validation issue."""
    severity: ValidationSeverity
    issue_type: str
    message: str
    location: str  # e.g., "hook", "module_1_chunk_2"
    suggestion: Optional[str] = None
    auto_fixable: bool = False
    fix_value: Optional[str] = None


@dataclass
class ValidationResult:
    """Result of emotion validation."""
    is_valid: bool
    issues: List[ValidationIssue]
    warnings_count: int
    errors_count: int
    critical_count: int
    suggestions: List[str]


class EmotionValidator(BaseAgent):
    """
    Validates emotion consistency across the pipeline.

    Checks:
    - All emotions are supported
    - Tension levels align with emotions
    - Emotion arcs progress logically
    - Distribution is balanced (variety check)
    """

    # Tension-emotion alignment rules
    # Maps tension levels to compatible emotions
    TENSION_EMOTION_ALIGNMENT = {
        1: ["wonder", "reflection", "melancholy", "mastery"],  # Low tension
        2: ["curiosity", "intrigue", "experimentation"],  # Low-mid
        3: ["tension", "restlessness", "intensity"],  # Mid
        4: ["excitement", "triumph", "rebellion", "liberation"],  # High
        5: ["explosive_energy", "intensity", "rebellion"]  # Peak
    }

    # Emotions that can follow each other in an arc
    VALID_TRANSITIONS = {
        "wonder": ["curiosity", "intrigue", "reflection"],
        "curiosity": ["tension", "wonder", "excitement", "intrigue"],
        "tension": ["triumph", "explosive_energy", "relief", "melancholy"],
        "triumph": ["reflection", "mastery", "liberation", "excitement"],
        "melancholy": ["reflection", "hope", "liberation", "wonder"],
        "intrigue": ["tension", "curiosity", "wonder", "excitement"],
        "excitement": ["triumph", "tension", "explosive_energy"],
        "reflection": ["mastery", "wonder", "melancholy"],
        "restlessness": ["rebellion", "liberation", "tension", "excitement"],
        "explosive_energy": ["rebellion", "liberation", "triumph"],
        "rebellion": ["liberation", "triumph", "explosive_energy"],
        "liberation": ["triumph", "mastery", "reflection", "wonder"],
        "experimentation": ["curiosity", "excitement", "mastery"],
        "mastery": ["triumph", "reflection", "liberation"],
        "intensity": ["triumph", "tension", "explosive_energy"],
    }

    def __init__(self):
        """Initialize the Emotion Validator."""
        super().__init__(
            name="EmotionValidator",
            output_category=""
        )
        self.supported_emotions = SUPPORTED_EMOTIONS

    def validate_script(self, script: Dict[str, Any]) -> ValidationResult:
        """
        Validate a complete enhanced script for emotion issues.

        Args:
            script: Enhanced script dictionary

        Returns:
            ValidationResult with issues and suggestions
        """
        issues: List[ValidationIssue] = []

        # Validate hook
        hook = script.get("hook", {})
        if hook:
            issues.extend(self._validate_chunk(hook, "hook"))

        # Validate modules
        modules = script.get("modules", [])
        previous_emotion = hook.get("emotion", "neutral")

        for module in modules:
            module_id = module.get("id", 0)
            emotion_arc = module.get("emotion_arc", "")

            # Validate emotion arc format
            if emotion_arc:
                issues.extend(self._validate_emotion_arc(emotion_arc, f"module_{module_id}"))

            # Validate chunks
            chunks = module.get("chunks", [])
            for chunk_idx, chunk in enumerate(chunks):
                location = f"module_{module_id}_chunk_{chunk_idx + 1}"
                issues.extend(self._validate_chunk(chunk, location))

                # Check transition from previous emotion
                current_emotion = chunk.get("emotion", "neutral")
                transition_issue = self._check_transition(
                    previous_emotion, current_emotion, location
                )
                if transition_issue:
                    issues.append(transition_issue)
                previous_emotion = current_emotion

        # Check overall emotion distribution
        issues.extend(self._check_emotion_distribution(script))

        # Compile result
        warnings = sum(1 for i in issues if i.severity == ValidationSeverity.WARNING)
        errors = sum(1 for i in issues if i.severity == ValidationSeverity.ERROR)
        criticals = sum(1 for i in issues if i.severity == ValidationSeverity.CRITICAL)

        is_valid = criticals == 0 and errors == 0
        suggestions = [i.suggestion for i in issues if i.suggestion]

        return ValidationResult(
            is_valid=is_valid,
            issues=issues,
            warnings_count=warnings,
            errors_count=errors,
            critical_count=criticals,
            suggestions=suggestions
        )

    def _validate_chunk(
        self,
        chunk: Dict[str, Any],
        location: str
    ) -> List[ValidationIssue]:
        """Validate a single chunk's emotion metadata."""
        issues = []

        emotion = chunk.get("emotion", "")
        tension_level = chunk.get("tension_level", 0)

        # Check emotion is supported
        if emotion and not is_valid_emotion(emotion):
            # Find closest match
            closest = self._find_closest_emotion(emotion)
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                issue_type="unsupported_emotion",
                message=f"Unknown emotion: '{emotion}'",
                location=location,
                suggestion=f"Use '{closest}' instead" if closest else f"Use one of: {', '.join(self.supported_emotions[:5])}...",
                auto_fixable=True,
                fix_value=closest
            ))

        # Check tension-emotion alignment
        if emotion and tension_level:
            alignment_issue = self._check_tension_alignment(
                emotion, tension_level, location
            )
            if alignment_issue:
                issues.append(alignment_issue)

        return issues

    def _validate_emotion_arc(
        self,
        emotion_arc: str,
        location: str
    ) -> List[ValidationIssue]:
        """Validate an emotion arc string (e.g., 'wonder -> curiosity')."""
        issues = []

        # Parse arc
        if " -> " in emotion_arc:
            parts = [p.strip() for p in emotion_arc.split(" -> ")]
            for emotion in parts:
                if not is_valid_emotion(emotion):
                    closest = self._find_closest_emotion(emotion)
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        issue_type="invalid_arc_emotion",
                        message=f"Invalid emotion in arc: '{emotion}'",
                        location=f"{location}_arc",
                        suggestion=f"Use '{closest}'" if closest else None,
                        auto_fixable=True,
                        fix_value=closest
                    ))

        return issues

    def _check_tension_alignment(
        self,
        emotion: str,
        tension_level: int,
        location: str
    ) -> Optional[ValidationIssue]:
        """Check if tension level aligns with emotion."""
        emotion_lower = emotion.lower()

        # Get compatible emotions for this tension level
        compatible = self.TENSION_EMOTION_ALIGNMENT.get(tension_level, [])

        if emotion_lower not in compatible:
            # Find suggested tension level for this emotion
            suggested_tension = None
            for level, emotions in self.TENSION_EMOTION_ALIGNMENT.items():
                if emotion_lower in emotions:
                    suggested_tension = level
                    break

            return ValidationIssue(
                severity=ValidationSeverity.WARNING,
                issue_type="tension_mismatch",
                message=f"Tension {tension_level} may not match emotion '{emotion}'",
                location=location,
                suggestion=f"Consider tension level {suggested_tension}" if suggested_tension else None
            )

        return None

    def _check_transition(
        self,
        from_emotion: str,
        to_emotion: str,
        location: str
    ) -> Optional[ValidationIssue]:
        """Check if emotion transition is natural."""
        from_lower = from_emotion.lower()
        to_lower = to_emotion.lower()

        if from_lower == to_lower:
            return None  # Same emotion is fine

        valid_next = self.VALID_TRANSITIONS.get(from_lower, [])

        if to_lower not in valid_next and valid_next:
            return ValidationIssue(
                severity=ValidationSeverity.INFO,
                issue_type="unusual_transition",
                message=f"Transition from '{from_emotion}' to '{to_emotion}' may feel abrupt",
                location=location,
                suggestion=f"Consider intermediate emotions like: {', '.join(valid_next[:3])}"
            )

        return None

    def _check_emotion_distribution(
        self,
        script: Dict[str, Any]
    ) -> List[ValidationIssue]:
        """Check overall emotion distribution for variety."""
        issues = []

        # Count emotions
        emotion_counts: Dict[str, int] = {}

        hook = script.get("hook", {})
        if hook.get("emotion"):
            emotion = hook["emotion"].lower()
            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1

        for module in script.get("modules", []):
            for chunk in module.get("chunks", []):
                emotion = chunk.get("emotion", "neutral").lower()
                emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1

        total_chunks = sum(emotion_counts.values())

        # Check for dominant emotion (>50%)
        for emotion, count in emotion_counts.items():
            if total_chunks > 0 and count / total_chunks > 0.5:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    issue_type="low_variety",
                    message=f"Emotion '{emotion}' is used in >50% of chunks ({count}/{total_chunks})",
                    location="script",
                    suggestion="Consider more emotional variety for engagement"
                ))

        # Check for lack of variety (< 3 different emotions)
        if len(emotion_counts) < 3 and total_chunks > 4:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.INFO,
                issue_type="limited_variety",
                message=f"Only {len(emotion_counts)} different emotions used",
                location="script",
                suggestion="Add more emotional variety (wonder, tension, triumph, etc.)"
            ))

        return issues

    def _find_closest_emotion(self, emotion: str) -> Optional[str]:
        """Find the closest supported emotion to a given string."""
        emotion_lower = emotion.lower()

        # Direct substring match
        for supported in self.supported_emotions:
            if emotion_lower in supported or supported in emotion_lower:
                return supported

        # Common typo/synonym mappings
        synonyms = {
            "happy": "triumph",
            "sad": "melancholy",
            "angry": "rebellion",
            "fear": "tension",
            "surprise": "wonder",
            "joy": "excitement",
            "anticipation": "intrigue",
            "trust": "reflection",
            "disgust": "rebellion",
            "energy": "explosive_energy",
            "calm": "reflection",
            "hope": "liberation",
            "anxiety": "tension",
            "peace": "mastery",
        }

        return synonyms.get(emotion_lower)

    def suggest_emotion_fixes(
        self,
        issues: List[ValidationIssue]
    ) -> Dict[str, str]:
        """
        Provide auto-fix suggestions for emotion issues.

        Args:
            issues: List of validation issues

        Returns:
            Dictionary mapping location -> fixed emotion value
        """
        fixes = {}

        for issue in issues:
            if issue.auto_fixable and issue.fix_value:
                fixes[issue.location] = issue.fix_value

        return fixes

    def apply_fixes(
        self,
        script: Dict[str, Any],
        fixes: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Apply auto-fixes to a script.

        Args:
            script: Enhanced script dictionary
            fixes: Dictionary of location -> fixed value

        Returns:
            Updated script with fixes applied
        """
        import copy
        fixed_script = copy.deepcopy(script)

        for location, fix_value in fixes.items():
            if location == "hook":
                fixed_script["hook"]["emotion"] = fix_value
            elif location.startswith("module_"):
                # Parse location: module_X_chunk_Y
                parts = location.split("_")
                if len(parts) >= 4:
                    module_id = int(parts[1])
                    chunk_idx = int(parts[3]) - 1

                    for module in fixed_script.get("modules", []):
                        if module.get("id") == module_id:
                            if chunk_idx < len(module.get("chunks", [])):
                                module["chunks"][chunk_idx]["emotion"] = fix_value

        return fixed_script

    def process(self, script: Dict[str, Any]) -> ValidationResult:
        """
        Main processing method - validate the script.

        Args:
            script: Enhanced script dictionary

        Returns:
            ValidationResult
        """
        return self.validate_script(script)

    def print_validation_report(self, result: ValidationResult):
        """Print a formatted validation report."""
        print("\n" + "=" * 60)
        print("EMOTION VALIDATION REPORT")
        print("=" * 60)

        status = "PASSED" if result.is_valid else "FAILED"
        print(f"\nStatus: {status}")
        print(f"Criticals: {result.critical_count}")
        print(f"Errors: {result.errors_count}")
        print(f"Warnings: {result.warnings_count}")

        if result.issues:
            print("\n--- Issues ---")
            for issue in result.issues:
                severity = issue.severity.value.upper()
                print(f"\n[{severity}] {issue.issue_type}")
                print(f"  Location: {issue.location}")
                print(f"  Message: {issue.message}")
                if issue.suggestion:
                    print(f"  Suggestion: {issue.suggestion}")

        if result.suggestions:
            print("\n--- Suggestions ---")
            for i, suggestion in enumerate(result.suggestions, 1):
                print(f"{i}. {suggestion}")

        print("\n" + "=" * 60)


if __name__ == "__main__":
    # Test with sample script
    sample_script = {
        "hook": {
            "text": "Test hook",
            "emotion": "intrigued"  # Typo
        },
        "modules": [
            {
                "id": 1,
                "title": "Test Module",
                "emotion_arc": "wonder -> curiosity",
                "chunks": [
                    {"text": "Chunk 1", "emotion": "wonder", "tension_level": 2},
                    {"text": "Chunk 2", "emotion": "happy", "tension_level": 3},  # Invalid
                ]
            }
        ]
    }

    validator = EmotionValidator()
    result = validator.validate_script(sample_script)
    validator.print_validation_report(result)

    if not result.is_valid:
        fixes = validator.suggest_emotion_fixes(result.issues)
        print(f"\nSuggested fixes: {fixes}")
