"""
Quality Evaluator
Author: Sarath

Central quality evaluation framework for podcast generation.
Aggregates metrics from individual analyzers across all dimensions:
- Script (hook strength, emotional arc, narrative flow)
- Pacing (pause durations, tempo variation)
- Voice/TTS (clarity, emotion alignment)
- BGM (volume balance, ducking, transitions)
- Audio Mix (voice/BGM ratio, loudness)
- Video (image-audio sync, transitions)
- Ending (fadeout, conclusion quality)
- Duration (target vs actual)

Supports explainable quality traces with reasoning, strengths,
weaknesses, and suggestions (Pro mode).
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from pathlib import Path
import json

from utils.quality_trace import (
    QualityTrace,
    QualityTraceReport,
    QualityTraceBuilder,
    score_to_grade,
    EVALUATION_SEQUENCE,
)
from utils.reasoning_templates import build_reasoning


@dataclass
class QualityIssue:
    """A quality issue detected during evaluation."""
    dimension: str
    severity: str  # 'error', 'warning', 'info'
    message: str
    timestamp_ms: Optional[int] = None
    details: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "dimension": self.dimension,
            "severity": self.severity,
            "message": self.message,
        }
        if self.timestamp_ms is not None:
            result["timestamp_ms"] = self.timestamp_ms
        if self.details:
            result["details"] = self.details
        return result


@dataclass
class ScriptMetrics:
    """Script quality metrics."""
    hook_score: float = 0.0         # 0-10: Does hook grab attention?
    emotional_arc: float = 0.0      # 0-10: Variety and progression
    narrative_flow: float = 0.0     # 0-10: Coherence and transitions
    module_balance: float = 0.0     # 0-10: Even distribution
    word_count: int = 0
    module_count: int = 0
    chunk_count: int = 0
    issues: List[str] = field(default_factory=list)

    def score(self) -> float:
        """Calculate overall script score (0-100)."""
        return (self.hook_score + self.emotional_arc +
                self.narrative_flow + self.module_balance) * 2.5


@dataclass
class PacingMetrics:
    """Pacing quality metrics."""
    avg_sentence_pause_ms: float = 0.0
    pause_variation_pct: float = 0.0    # Higher = more natural
    emotion_alignment: float = 0.0       # Do pauses match emotion style?
    tempo_variation: float = 0.0         # Speed changes across sections
    uniform_pause_detected: bool = False
    issues: List[str] = field(default_factory=list)

    def score(self) -> float:
        """Calculate overall pacing score (0-100)."""
        base_score = 70.0
        # Penalize uniform pauses (robotic feel)
        if self.uniform_pause_detected:
            base_score -= 20
        # Reward variation
        base_score += min(self.pause_variation_pct / 2, 15)
        # Reward emotion alignment
        base_score += self.emotion_alignment * 1.5
        return max(0, min(100, base_score))


@dataclass
class VoiceMetrics:
    """Voice/TTS quality metrics."""
    sentence_count: int = 0
    failed_count: int = 0
    avg_duration_ms: float = 0.0
    emotion_coverage: float = 0.0        # % of sentences with emotion
    speed_variation: float = 0.0         # Natural tempo changes
    issues: List[str] = field(default_factory=list)

    def score(self) -> float:
        """Calculate overall voice score (0-100)."""
        if self.sentence_count == 0:
            return 0.0
        success_rate = (self.sentence_count - self.failed_count) / self.sentence_count
        base_score = success_rate * 80
        base_score += self.emotion_coverage * 0.1
        base_score += min(self.speed_variation * 2, 10)
        return max(0, min(100, base_score))


@dataclass
class BGMMetrics:
    """Background music quality metrics."""
    avg_volume_db: float = -18.0
    volume_range_db: float = 0.0         # Dynamic range of BGM volume
    ducking_detected: bool = False
    transition_count: int = 0
    transition_smoothness: float = 0.0   # Crossfade quality
    emotion_alignment: float = 0.0       # BGM mood matches content?
    issues: List[str] = field(default_factory=list)

    def score(self) -> float:
        """Calculate overall BGM score (0-100)."""
        base_score = 60.0
        # Reward ducking
        if self.ducking_detected:
            base_score += 15
        # Reward dynamic volume
        base_score += min(self.volume_range_db * 2, 10)
        # Reward emotion alignment
        base_score += self.emotion_alignment * 1.5
        return max(0, min(100, base_score))


@dataclass
class AudioMixMetrics:
    """Final audio mix quality metrics."""
    voice_bgm_ratio_db: float = 0.0      # Should be 12-18dB
    loudness_lufs: float = -16.0         # Overall loudness
    dynamic_range_db: float = 0.0        # Compression level
    clipping_detected: bool = False
    duration_seconds: float = 0.0
    issues: List[str] = field(default_factory=list)

    def score(self) -> float:
        """Calculate overall audio mix score (0-100)."""
        base_score = 70.0
        # Penalize clipping
        if self.clipping_detected:
            base_score -= 30
        # Check voice/BGM ratio (ideal: 12-18dB)
        if 12 <= self.voice_bgm_ratio_db <= 18:
            base_score += 15
        elif 10 <= self.voice_bgm_ratio_db <= 20:
            base_score += 8
        # Check loudness (ideal: -14 to -16 LUFS)
        if -16 <= self.loudness_lufs <= -14:
            base_score += 15
        return max(0, min(100, base_score))


@dataclass
class VideoMetrics:
    """Video quality metrics."""
    image_count: int = 0
    avg_image_duration_sec: float = 0.0
    transition_count: int = 0
    transition_quality: float = 0.0      # Crossfades smooth?
    resolution_ok: bool = True
    total_duration_sec: float = 0.0
    issues: List[str] = field(default_factory=list)

    def score(self) -> float:
        """Calculate overall video score (0-100)."""
        if self.image_count == 0:
            return 0.0
        base_score = 60.0
        if self.resolution_ok:
            base_score += 20
        base_score += self.transition_quality * 2
        return max(0, min(100, base_score))


@dataclass
class EndingMetrics:
    """Ending quality metrics."""
    has_outro: bool = False              # Dedicated conclusion?
    fadeout_present: bool = False
    fadeout_duration_ms: int = 0
    final_level_db: float = 0.0          # Should be < -40dB
    is_abrupt: bool = False              # Cutoff detected?
    issues: List[str] = field(default_factory=list)

    def score(self) -> float:
        """Calculate overall ending score (0-100)."""
        base_score = 50.0
        if self.has_outro:
            base_score += 15
        if self.fadeout_present:
            base_score += 20
        if not self.is_abrupt:
            base_score += 15
        if self.final_level_db < -40:
            base_score += 10
        return max(0, min(100, base_score - (30 if self.is_abrupt else 0)))


@dataclass
class DurationMetrics:
    """Duration quality metrics."""
    target_minutes: float = 0.0
    actual_minutes: float = 0.0
    difference_percent: float = 0.0
    is_within_tolerance: bool = True
    tolerance_percent: float = 15.0
    issues: List[str] = field(default_factory=list)

    def score(self) -> float:
        """Calculate overall duration score (0-100)."""
        if self.is_within_tolerance:
            # Perfect score if within 5%, scales down to 70 at tolerance boundary
            deviation = abs(self.difference_percent)
            if deviation <= 5:
                return 100.0
            return max(70, 100 - (deviation - 5) * 3)
        # Outside tolerance: lower score
        return max(0, 70 - abs(self.difference_percent - self.tolerance_percent) * 2)


@dataclass
class QualityMetrics:
    """Complete quality metrics for a podcast generation."""
    job_id: str = ""

    # Individual dimension metrics
    script: ScriptMetrics = field(default_factory=ScriptMetrics)
    pacing: PacingMetrics = field(default_factory=PacingMetrics)
    voice: VoiceMetrics = field(default_factory=VoiceMetrics)
    bgm: BGMMetrics = field(default_factory=BGMMetrics)
    audio_mix: AudioMixMetrics = field(default_factory=AudioMixMetrics)
    video: VideoMetrics = field(default_factory=VideoMetrics)
    ending: EndingMetrics = field(default_factory=EndingMetrics)
    duration: DurationMetrics = field(default_factory=DurationMetrics)

    # Aggregated issues
    issues: List[QualityIssue] = field(default_factory=list)

    def overall_score(self) -> float:
        """Calculate weighted overall quality score (0-100)."""
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
        scores = {
            "script": self.script.score(),
            "pacing": self.pacing.score(),
            "voice": self.voice.score(),
            "bgm": self.bgm.score(),
            "audio_mix": self.audio_mix.score(),
            "video": self.video.score(),
            "duration": self.duration.score(),
            "ending": self.ending.score(),
        }
        return sum(scores[k] * weights[k] for k in weights)

    def get_grade(self, score: float) -> str:
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

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary for JSON serialization."""
        overall = self.overall_score()
        return {
            "job_id": self.job_id,
            "overall_score": round(overall, 1),
            "overall_grade": self.get_grade(overall),
            "grades": {
                "script": {
                    "score": round(self.script.score(), 1),
                    "grade": self.get_grade(self.script.score())
                },
                "pacing": {
                    "score": round(self.pacing.score(), 1),
                    "grade": self.get_grade(self.pacing.score())
                },
                "voice": {
                    "score": round(self.voice.score(), 1),
                    "grade": self.get_grade(self.voice.score())
                },
                "bgm": {
                    "score": round(self.bgm.score(), 1),
                    "grade": self.get_grade(self.bgm.score())
                },
                "audio_mix": {
                    "score": round(self.audio_mix.score(), 1),
                    "grade": self.get_grade(self.audio_mix.score())
                },
                "video": {
                    "score": round(self.video.score(), 1),
                    "grade": self.get_grade(self.video.score())
                },
                "duration": {
                    "score": round(self.duration.score(), 1),
                    "grade": self.get_grade(self.duration.score())
                },
                "ending": {
                    "score": round(self.ending.score(), 1),
                    "grade": self.get_grade(self.ending.score())
                },
            },
            "issues": [issue.to_dict() for issue in self.issues],
            "recommendations": self._generate_recommendations(),
        }

    def _generate_recommendations(self) -> List[str]:
        """Generate actionable recommendations based on issues."""
        recommendations = []

        # Pacing recommendations
        if self.pacing.uniform_pause_detected:
            recommendations.append(
                "Enable emotion-based pause durations for more natural pacing"
            )

        # BGM recommendations
        if not self.bgm.ducking_detected:
            recommendations.append(
                "Enable BGM ducking to prevent voice masking"
            )
        if self.bgm.volume_range_db < 3:
            recommendations.append(
                "Add dynamic BGM volume variation for emotional impact"
            )

        # Ending recommendations
        if self.ending.is_abrupt:
            recommendations.append(
                "Add fadeout to final audio to prevent abrupt ending"
            )
        if not self.ending.has_outro:
            recommendations.append(
                "Ensure outro module has conclusion rather than cliffhanger"
            )

        # Audio mix recommendations
        if self.audio_mix.clipping_detected:
            recommendations.append(
                "Reduce gain to prevent audio clipping"
            )
        if self.audio_mix.voice_bgm_ratio_db < 12:
            recommendations.append(
                "Increase voice/BGM ratio for better clarity"
            )

        # Duration recommendations
        if not self.duration.is_within_tolerance:
            if self.duration.actual_minutes > self.duration.target_minutes:
                recommendations.append(
                    "Consider tightening script or increasing narration pace"
                )
            else:
                recommendations.append(
                    "Consider expanding content or adding more detail"
                )

        return recommendations


class QualityEvaluator:
    """
    Central quality evaluation orchestrator.

    Coordinates individual analyzers and aggregates results
    into a comprehensive quality report.
    """

    def __init__(self, job_id: str = "", output_dir: Optional[Path] = None):
        """
        Initialize the Quality Evaluator.

        Args:
            job_id: Unique identifier for the job being evaluated
            output_dir: Directory for saving quality reports
        """
        self.job_id = job_id
        self.output_dir = output_dir or Path("Output")
        self.metrics = QualityMetrics(job_id=job_id)

    def analyze_script(self, script: Dict[str, Any]) -> ScriptMetrics:
        """
        Analyze script quality.

        Args:
            script: Enhanced script dictionary

        Returns:
            ScriptMetrics with analysis results
        """
        from utils.analyzers.script_analyzer import ScriptAnalyzer
        analyzer = ScriptAnalyzer()
        self.metrics.script = analyzer.analyze(script)
        return self.metrics.script

    def analyze_pacing(
        self,
        tts_results: List[Dict[str, Any]],
        pause_metadata: Optional[Dict[str, Any]] = None
    ) -> PacingMetrics:
        """
        Analyze pacing quality.

        Args:
            tts_results: TTS generation results with timing info
            pause_metadata: Optional pause duration metadata

        Returns:
            PacingMetrics with analysis results
        """
        from utils.analyzers.pacing_analyzer import PacingAnalyzer
        analyzer = PacingAnalyzer()
        self.metrics.pacing = analyzer.analyze(tts_results, pause_metadata)
        return self.metrics.pacing

    def analyze_voice(self, tts_results: List[Dict[str, Any]]) -> VoiceMetrics:
        """
        Analyze voice/TTS quality.

        Args:
            tts_results: TTS generation results

        Returns:
            VoiceMetrics with analysis results
        """
        from utils.analyzers.voice_analyzer import VoiceAnalyzer
        analyzer = VoiceAnalyzer()
        self.metrics.voice = analyzer.analyze(tts_results)
        return self.metrics.voice

    def analyze_bgm(
        self,
        bgm_results: List[Dict[str, Any]],
        ducking_data: Optional[Dict[str, Any]] = None
    ) -> BGMMetrics:
        """
        Analyze BGM quality.

        Args:
            bgm_results: BGM generation results
            ducking_data: Optional ducking configuration data

        Returns:
            BGMMetrics with analysis results
        """
        from utils.analyzers.bgm_analyzer import BGMAnalyzer
        analyzer = BGMAnalyzer()
        self.metrics.bgm = analyzer.analyze(bgm_results, ducking_data)
        return self.metrics.bgm

    def analyze_audio_mix(self, audio_path: str) -> AudioMixMetrics:
        """
        Analyze final audio mix quality.

        Args:
            audio_path: Path to final mixed audio file

        Returns:
            AudioMixMetrics with analysis results
        """
        from utils.analyzers.audio_mix_analyzer import AudioMixAnalyzer
        analyzer = AudioMixAnalyzer()
        self.metrics.audio_mix = analyzer.analyze(audio_path)
        return self.metrics.audio_mix

    def analyze_video(
        self,
        video_path: str,
        image_results: List[Dict[str, Any]]
    ) -> VideoMetrics:
        """
        Analyze video quality.

        Args:
            video_path: Path to final video file
            image_results: Image generation results

        Returns:
            VideoMetrics with analysis results
        """
        from utils.analyzers.video_analyzer import VideoAnalyzer
        analyzer = VideoAnalyzer()
        self.metrics.video = analyzer.analyze(video_path, image_results)
        return self.metrics.video

    def analyze_ending(self, audio_path: str) -> EndingMetrics:
        """
        Analyze ending quality.

        Args:
            audio_path: Path to final audio file

        Returns:
            EndingMetrics with analysis results
        """
        from utils.analyzers.ending_analyzer import EndingAnalyzer
        analyzer = EndingAnalyzer()
        self.metrics.ending = analyzer.analyze(audio_path)
        return self.metrics.ending

    def analyze_duration(
        self,
        audio_path: str,
        target_minutes: float
    ) -> DurationMetrics:
        """
        Analyze duration quality.

        Args:
            audio_path: Path to audio file
            target_minutes: Target duration in minutes

        Returns:
            DurationMetrics with analysis results
        """
        from utils.duration_evaluator import DurationEvaluator
        evaluator = DurationEvaluator()

        try:
            result = evaluator.evaluate(audio_path, target_minutes)
            self.metrics.duration = DurationMetrics(
                target_minutes=result.target_minutes,
                actual_minutes=result.actual_minutes,
                difference_percent=result.difference_percent,
                is_within_tolerance=result.is_within_tolerance,
                tolerance_percent=result.tolerance_percent,
            )
            if not result.is_within_tolerance:
                self.metrics.duration.issues.append(
                    f"Duration {result.actual_minutes:.1f}min differs from "
                    f"target {result.target_minutes:.1f}min by "
                    f"{result.difference_percent:+.1f}%"
                )
        except Exception as e:
            self.metrics.duration.issues.append(f"Duration analysis failed: {e}")

        return self.metrics.duration

    def collect_issues(self) -> List[QualityIssue]:
        """
        Collect all issues from dimension metrics.

        Returns:
            List of QualityIssue objects
        """
        self.metrics.issues = []

        # Collect issues from each dimension
        dimensions = [
            ("script", self.metrics.script),
            ("pacing", self.metrics.pacing),
            ("voice", self.metrics.voice),
            ("bgm", self.metrics.bgm),
            ("audio_mix", self.metrics.audio_mix),
            ("video", self.metrics.video),
            ("ending", self.metrics.ending),
            ("duration", self.metrics.duration),
        ]

        for dim_name, dim_metrics in dimensions:
            for issue_msg in dim_metrics.issues:
                # Determine severity based on keywords
                if any(word in issue_msg.lower() for word in ["fail", "error", "missing", "abrupt"]):
                    severity = "error"
                elif any(word in issue_msg.lower() for word in ["warn", "low", "uniform"]):
                    severity = "warning"
                else:
                    severity = "info"

                self.metrics.issues.append(QualityIssue(
                    dimension=dim_name,
                    severity=severity,
                    message=issue_msg,
                ))

        return self.metrics.issues

    def generate_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive quality report.

        Returns:
            Dictionary containing full quality report
        """
        self.collect_issues()
        return self.metrics.to_dict()

    def save_report(self, filename: str = "quality_report") -> str:
        """
        Save quality report to JSON file.

        Args:
            filename: Output filename (without extension)

        Returns:
            Path to saved report file
        """
        report = self.generate_report()
        output_path = self.output_dir / f"{filename}.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)

        return str(output_path)

    def log_summary(self) -> None:
        """Print quality summary to console."""
        report = self.generate_report()
        print("\n" + "=" * 50)
        print("QUALITY REPORT")
        print("=" * 50)
        print(f"Overall Score: {report['overall_score']}/100 ({report['overall_grade']})")
        print("\nDimension Scores:")
        for dim, data in report['grades'].items():
            print(f"  {dim:12}: {data['score']:5.1f} ({data['grade']})")

        if report['issues']:
            print(f"\nIssues ({len(report['issues'])}):")
            for issue in report['issues'][:5]:  # Show first 5
                severity_icon = {"error": "[!]", "warning": "[~]", "info": "[i]"}.get(
                    issue['severity'], "[?]"
                )
                print(f"  {severity_icon} [{issue['dimension']}] {issue['message']}")
            if len(report['issues']) > 5:
                print(f"  ... and {len(report['issues']) - 5} more")

        if report['recommendations']:
            print(f"\nRecommendations:")
            for rec in report['recommendations'][:3]:  # Show first 3
                print(f"  - {rec}")

        print("=" * 50 + "\n")

    # =========================================================================
    # QUALITY TRACE METHODS (Explainable Evaluation)
    # =========================================================================

    def build_script_trace(self, script: Optional[Dict[str, Any]] = None) -> QualityTrace:
        """
        Build explainable quality trace for script dimension.

        Args:
            script: Optional script dict. If None, uses already-analyzed metrics.

        Returns:
            QualityTrace with reasoning, strengths, and weaknesses.
        """
        if script:
            self.analyze_script(script)

        metrics = self.metrics.script
        score = round(metrics.score())

        # Build raw metrics dict for debugging
        raw_metrics = {
            "hook_score": metrics.hook_score,
            "emotional_arc": metrics.emotional_arc,
            "narrative_flow": metrics.narrative_flow,
            "module_balance": metrics.module_balance,
            "word_count": metrics.word_count,
            "module_count": metrics.module_count,
            "chunk_count": metrics.chunk_count,
            "score": score,
            "emotion_count": 0,  # Will be populated if available
        }

        # Get reasoning from templates
        reasoning, strengths, weaknesses = build_reasoning("script", raw_metrics)

        builder = (
            QualityTraceBuilder("script")
            .score(score)
            .reasoning(reasoning)
            .raw_metrics(raw_metrics)
            .sequence(EVALUATION_SEQUENCE["script"])
        )

        for s in strengths:
            builder.add_strength(s)
        for w in weaknesses:
            builder.add_weakness(w)

        return builder.build()

    def build_voice_trace(self, tts_results: Optional[List[Dict[str, Any]]] = None) -> QualityTrace:
        """Build explainable quality trace for voice dimension."""
        if tts_results:
            self.analyze_voice(tts_results)

        metrics = self.metrics.voice
        score = round(metrics.score())
        success_rate = 0
        if metrics.sentence_count > 0:
            success_rate = (metrics.sentence_count - metrics.failed_count) / metrics.sentence_count * 100

        raw_metrics = {
            "sentence_count": metrics.sentence_count,
            "failed_count": metrics.failed_count,
            "avg_duration_ms": metrics.avg_duration_ms,
            "emotion_coverage": metrics.emotion_coverage,
            "speed_variation": metrics.speed_variation,
            "success_rate": success_rate,
            "score": score,
        }

        reasoning, strengths, weaknesses = build_reasoning("voice", raw_metrics)

        builder = (
            QualityTraceBuilder("voice")
            .score(score)
            .reasoning(reasoning)
            .raw_metrics(raw_metrics)
            .sequence(EVALUATION_SEQUENCE["voice"])
        )

        for s in strengths:
            builder.add_strength(s)
        for w in weaknesses:
            builder.add_weakness(w)

        return builder.build()

    def build_pacing_trace(
        self,
        tts_results: Optional[List[Dict[str, Any]]] = None,
        pause_metadata: Optional[Dict[str, Any]] = None
    ) -> QualityTrace:
        """Build explainable quality trace for pacing dimension."""
        if tts_results:
            self.analyze_pacing(tts_results, pause_metadata)

        metrics = self.metrics.pacing
        score = round(metrics.score())

        raw_metrics = {
            "avg_sentence_pause_ms": metrics.avg_sentence_pause_ms,
            "pause_variation_pct": metrics.pause_variation_pct,
            "emotion_alignment": metrics.emotion_alignment,
            "tempo_variation": metrics.tempo_variation,
            "uniform_pause_detected": metrics.uniform_pause_detected,
            "score": score,
        }

        reasoning, strengths, weaknesses = build_reasoning("pacing", raw_metrics)

        builder = (
            QualityTraceBuilder("pacing")
            .score(score)
            .reasoning(reasoning)
            .raw_metrics(raw_metrics)
            .sequence(EVALUATION_SEQUENCE["pacing"])
        )

        for s in strengths:
            builder.add_strength(s)
        for w in weaknesses:
            builder.add_weakness(w)

        return builder.build()

    def build_bgm_trace(
        self,
        bgm_results: Optional[List[Dict[str, Any]]] = None,
        ducking_data: Optional[Dict[str, Any]] = None
    ) -> QualityTrace:
        """Build explainable quality trace for BGM dimension."""
        if bgm_results:
            self.analyze_bgm(bgm_results, ducking_data)

        metrics = self.metrics.bgm
        score = round(metrics.score())

        raw_metrics = {
            "avg_volume_db": metrics.avg_volume_db,
            "volume_range_db": metrics.volume_range_db,
            "ducking_detected": metrics.ducking_detected,
            "transition_count": metrics.transition_count,
            "transition_smoothness": metrics.transition_smoothness,
            "emotion_alignment": metrics.emotion_alignment,
            "score": score,
        }

        reasoning, strengths, weaknesses = build_reasoning("bgm", raw_metrics)

        builder = (
            QualityTraceBuilder("bgm")
            .score(score)
            .reasoning(reasoning)
            .raw_metrics(raw_metrics)
            .sequence(EVALUATION_SEQUENCE["bgm"])
        )

        for s in strengths:
            builder.add_strength(s)
        for w in weaknesses:
            builder.add_weakness(w)

        return builder.build()

    def build_audio_mix_trace(self, audio_path: Optional[str] = None) -> QualityTrace:
        """Build explainable quality trace for audio mix dimension."""
        if audio_path:
            self.analyze_audio_mix(audio_path)

        metrics = self.metrics.audio_mix
        score = round(metrics.score())

        raw_metrics = {
            "voice_bgm_ratio_db": metrics.voice_bgm_ratio_db,
            "loudness_lufs": metrics.loudness_lufs,
            "dynamic_range_db": metrics.dynamic_range_db,
            "clipping_detected": metrics.clipping_detected,
            "duration_seconds": metrics.duration_seconds,
            "score": score,
        }

        reasoning, strengths, weaknesses = build_reasoning("audio_mix", raw_metrics)

        builder = (
            QualityTraceBuilder("audio_mix")
            .score(score)
            .reasoning(reasoning)
            .raw_metrics(raw_metrics)
            .sequence(EVALUATION_SEQUENCE["audio_mix"])
        )

        for s in strengths:
            builder.add_strength(s)
        for w in weaknesses:
            builder.add_weakness(w)

        return builder.build()

    def build_video_trace(
        self,
        video_path: Optional[str] = None,
        image_results: Optional[List[Dict[str, Any]]] = None
    ) -> QualityTrace:
        """Build explainable quality trace for video dimension."""
        if video_path and image_results:
            self.analyze_video(video_path, image_results)

        metrics = self.metrics.video
        score = round(metrics.score())

        raw_metrics = {
            "image_count": metrics.image_count,
            "avg_image_duration_sec": metrics.avg_image_duration_sec,
            "transition_count": metrics.transition_count,
            "transition_quality": metrics.transition_quality,
            "resolution_ok": metrics.resolution_ok,
            "total_duration_sec": metrics.total_duration_sec,
            "score": score,
        }

        reasoning, strengths, weaknesses = build_reasoning("video", raw_metrics)

        builder = (
            QualityTraceBuilder("video")
            .score(score)
            .reasoning(reasoning)
            .raw_metrics(raw_metrics)
            .sequence(EVALUATION_SEQUENCE["video"])
        )

        for s in strengths:
            builder.add_strength(s)
        for w in weaknesses:
            builder.add_weakness(w)

        return builder.build()

    def build_ending_trace(self, audio_path: Optional[str] = None) -> QualityTrace:
        """Build explainable quality trace for ending dimension."""
        if audio_path:
            self.analyze_ending(audio_path)

        metrics = self.metrics.ending
        score = round(metrics.score())

        raw_metrics = {
            "has_outro": metrics.has_outro,
            "fadeout_present": metrics.fadeout_present,
            "fadeout_duration_ms": metrics.fadeout_duration_ms,
            "final_level_db": metrics.final_level_db,
            "is_abrupt": metrics.is_abrupt,
            "score": score,
        }

        reasoning, strengths, weaknesses = build_reasoning("ending", raw_metrics)

        builder = (
            QualityTraceBuilder("ending")
            .score(score)
            .reasoning(reasoning)
            .raw_metrics(raw_metrics)
            .sequence(EVALUATION_SEQUENCE["ending"])
        )

        for s in strengths:
            builder.add_strength(s)
        for w in weaknesses:
            builder.add_weakness(w)

        return builder.build()

    def build_duration_trace(
        self,
        audio_path: Optional[str] = None,
        target_minutes: Optional[float] = None
    ) -> QualityTrace:
        """Build explainable quality trace for duration dimension."""
        if audio_path and target_minutes is not None:
            self.analyze_duration(audio_path, target_minutes)

        metrics = self.metrics.duration
        score = round(metrics.score())

        raw_metrics = {
            "target_minutes": metrics.target_minutes,
            "actual_minutes": metrics.actual_minutes,
            "difference_percent": metrics.difference_percent,
            "is_within_tolerance": metrics.is_within_tolerance,
            "tolerance_percent": metrics.tolerance_percent,
            "score": score,
        }

        reasoning, strengths, weaknesses = build_reasoning("duration", raw_metrics)

        builder = (
            QualityTraceBuilder("duration")
            .score(score)
            .reasoning(reasoning)
            .raw_metrics(raw_metrics)
            .sequence(EVALUATION_SEQUENCE["duration"])
        )

        for s in strengths:
            builder.add_strength(s)
        for w in weaknesses:
            builder.add_weakness(w)

        return builder.build()

    def build_trace_report(self, mode: str = "normal") -> QualityTraceReport:
        """
        Build complete quality trace report from all analyzed dimensions.

        Args:
            mode: Pipeline mode ("normal", "pro", "ultra")

        Returns:
            QualityTraceReport with all dimension traces
        """
        report = QualityTraceReport(
            job_id=self.job_id,
            mode=mode,
        )

        # Build traces for each dimension that has been analyzed
        if self.metrics.script.word_count > 0:
            report.add_trace(self.build_script_trace())

        if self.metrics.pacing.avg_sentence_pause_ms > 0:
            report.add_trace(self.build_pacing_trace())

        if self.metrics.voice.sentence_count > 0:
            report.add_trace(self.build_voice_trace())

        if self.metrics.bgm.avg_volume_db != -18.0 or self.metrics.bgm.transition_count > 0:
            report.add_trace(self.build_bgm_trace())

        if self.metrics.audio_mix.duration_seconds > 0:
            report.add_trace(self.build_audio_mix_trace())

        if self.metrics.video.image_count > 0:
            report.add_trace(self.build_video_trace())

        if self.metrics.ending.fadeout_duration_ms > 0 or self.metrics.ending.is_abrupt:
            report.add_trace(self.build_ending_trace())

        if self.metrics.duration.actual_minutes > 0:
            report.add_trace(self.build_duration_trace())

        # Calculate overall score
        report.calculate_overall()

        return report

    def save_trace_report(self, mode: str = "normal") -> str:
        """
        Save quality trace report to output directory.

        Args:
            mode: Pipeline mode

        Returns:
            Path to saved trace report
        """
        report = self.build_trace_report(mode)
        return report.save(self.output_dir)


__all__ = [
    'QualityMetrics',
    'QualityIssue',
    'ScriptMetrics',
    'PacingMetrics',
    'VoiceMetrics',
    'BGMMetrics',
    'AudioMixMetrics',
    'VideoMetrics',
    'EndingMetrics',
    'DurationMetrics',
    'QualityEvaluator',
    # Re-export trace classes for convenience
    'QualityTrace',
    'QualityTraceReport',
    'QualityTraceBuilder',
    'score_to_grade',
]
