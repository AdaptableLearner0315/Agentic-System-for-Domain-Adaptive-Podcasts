"""
Quality Trace
Author: Sarath

Explainable quality evaluation traces for podcast generation.
Each QualityTrace contains reasoning, strengths, weaknesses, and suggestions
to provide transparency into quality scoring.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
from pathlib import Path


@dataclass
class QualityTrace:
    """
    Explainable quality trace for a single dimension.

    Provides human-readable reasoning and diagnostic data for
    understanding why a quality score is what it is.
    """
    dimension: str                              # "script", "voice", "bgm", etc.
    score: int = 0                              # 0-100
    grade: str = "F"                            # "A", "B+", "C", etc.
    reasoning: str = ""                         # 1-2 sentence human-readable explanation
    strengths: List[str] = field(default_factory=list)    # What's working well
    weaknesses: List[str] = field(default_factory=list)   # What's holding the score back
    suggestions: List[str] = field(default_factory=list)  # Pro mode only - actionable fixes
    sequence: int = 0                           # Evaluation order (1=first, 8=last)
    raw_metrics: Dict[str, Any] = field(default_factory=dict)  # Debug data
    enhanced: bool = False                      # True if LLM-enhanced (Pro mode)

    def to_dict(self) -> Dict[str, Any]:
        """Convert trace to dictionary for JSON serialization."""
        return {
            "dimension": self.dimension,
            "score": self.score,
            "grade": self.grade,
            "reasoning": self.reasoning,
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
            "suggestions": self.suggestions,
            "sequence": self.sequence,
            "raw_metrics": self.raw_metrics,
            "enhanced": self.enhanced,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QualityTrace':
        """Create QualityTrace from dictionary."""
        return cls(
            dimension=data.get("dimension", ""),
            score=data.get("score", 0),
            grade=data.get("grade", "F"),
            reasoning=data.get("reasoning", ""),
            strengths=data.get("strengths", []),
            weaknesses=data.get("weaknesses", []),
            suggestions=data.get("suggestions", []),
            sequence=data.get("sequence", 0),
            raw_metrics=data.get("raw_metrics", {}),
            enhanced=data.get("enhanced", False),
        )


@dataclass
class QualityTraceReport:
    """
    Complete quality trace report containing all dimension traces.

    Saved alongside podcast output for debugging and comparison.
    """
    job_id: str = ""
    mode: str = "normal"                        # "normal", "pro", "ultra"
    generated_at: str = ""                      # ISO timestamp
    overall_score: int = 0
    overall_grade: str = "F"
    traces: List[QualityTrace] = field(default_factory=list)

    def __post_init__(self):
        if not self.generated_at:
            self.generated_at = datetime.utcnow().isoformat() + "Z"

    def get_trace(self, dimension: str) -> Optional[QualityTrace]:
        """Get trace for a specific dimension."""
        for trace in self.traces:
            if trace.dimension == dimension:
                return trace
        return None

    def add_trace(self, trace: QualityTrace):
        """Add or update a trace for a dimension."""
        for i, existing in enumerate(self.traces):
            if existing.dimension == trace.dimension:
                self.traces[i] = trace
                return
        self.traces.append(trace)

    def calculate_overall(self, weights: Optional[Dict[str, float]] = None):
        """Calculate overall score from dimension traces."""
        if weights is None:
            weights = {
                "script": 0.15,
                "pacing": 0.15,
                "voice": 0.15,
                "bgm": 0.15,
                "audio_mix": 0.10,
                "video": 0.10,
                "duration": 0.10,
                "ending": 0.10,
            }

        total_weight = 0.0
        weighted_score = 0.0

        for trace in self.traces:
            weight = weights.get(trace.dimension, 0.1)
            weighted_score += trace.score * weight
            total_weight += weight

        if total_weight > 0:
            self.overall_score = int(weighted_score / total_weight * (1 / max(total_weight, 1)))
            # Recalculate properly
            self.overall_score = int(weighted_score)

        self.overall_grade = score_to_grade(self.overall_score)

    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary for JSON serialization."""
        return {
            "job_id": self.job_id,
            "mode": self.mode,
            "generated_at": self.generated_at,
            "overall_score": self.overall_score,
            "overall_grade": self.overall_grade,
            "traces": [trace.to_dict() for trace in self.traces],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QualityTraceReport':
        """Create QualityTraceReport from dictionary."""
        report = cls(
            job_id=data.get("job_id", ""),
            mode=data.get("mode", "normal"),
            generated_at=data.get("generated_at", ""),
            overall_score=data.get("overall_score", 0),
            overall_grade=data.get("overall_grade", "F"),
        )
        for trace_data in data.get("traces", []):
            report.traces.append(QualityTrace.from_dict(trace_data))
        return report

    def save(self, output_dir: Path) -> str:
        """Save report to output directory."""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "quality_trace.json"

        with open(output_path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

        return str(output_path)

    @classmethod
    def load(cls, path: Path) -> 'QualityTraceReport':
        """Load report from file."""
        with open(path, 'r') as f:
            data = json.load(f)
        return cls.from_dict(data)


def score_to_grade(score: int) -> str:
    """Convert numeric score to letter grade."""
    if score >= 93:
        return "A"
    elif score >= 90:
        return "A-"
    elif score >= 87:
        return "B+"
    elif score >= 83:
        return "B"
    elif score >= 80:
        return "B-"
    elif score >= 77:
        return "C+"
    elif score >= 73:
        return "C"
    elif score >= 70:
        return "C-"
    elif score >= 60:
        return "D"
    return "F"


class QualityTraceBuilder:
    """
    Builder for constructing QualityTrace objects.

    Provides fluent interface for building traces with
    automatic strength/weakness identification.
    """

    def __init__(self, dimension: str):
        """Initialize builder for a specific dimension."""
        self._trace = QualityTrace(dimension=dimension)

    def score(self, value: int) -> 'QualityTraceBuilder':
        """Set the score (0-100)."""
        self._trace.score = max(0, min(100, value))
        self._trace.grade = score_to_grade(self._trace.score)
        return self

    def reasoning(self, text: str) -> 'QualityTraceBuilder':
        """Set the reasoning explanation."""
        self._trace.reasoning = text
        return self

    def add_strength(self, strength: str) -> 'QualityTraceBuilder':
        """Add a strength indicator."""
        if strength and strength not in self._trace.strengths:
            self._trace.strengths.append(strength)
        return self

    def add_weakness(self, weakness: str) -> 'QualityTraceBuilder':
        """Add a weakness indicator."""
        if weakness and weakness not in self._trace.weaknesses:
            self._trace.weaknesses.append(weakness)
        return self

    def add_suggestion(self, suggestion: str) -> 'QualityTraceBuilder':
        """Add a suggestion (Pro mode)."""
        if suggestion and suggestion not in self._trace.suggestions:
            self._trace.suggestions.append(suggestion)
        return self

    def sequence(self, order: int) -> 'QualityTraceBuilder':
        """Set evaluation sequence order."""
        self._trace.sequence = order
        return self

    def raw_metrics(self, metrics: Dict[str, Any]) -> 'QualityTraceBuilder':
        """Set raw metrics for debugging."""
        self._trace.raw_metrics = metrics
        return self

    def enhanced(self, value: bool = True) -> 'QualityTraceBuilder':
        """Mark as LLM-enhanced."""
        self._trace.enhanced = value
        return self

    def build(self) -> QualityTrace:
        """Build and return the QualityTrace."""
        return self._trace


# Dimension evaluation sequence
EVALUATION_SEQUENCE = {
    "script": 1,
    "pacing": 2,
    "voice": 3,
    "bgm": 4,
    "audio_mix": 5,
    "video": 6,
    "ending": 7,
    "duration": 8,
}


__all__ = [
    'QualityTrace',
    'QualityTraceReport',
    'QualityTraceBuilder',
    'score_to_grade',
    'EVALUATION_SEQUENCE',
]
