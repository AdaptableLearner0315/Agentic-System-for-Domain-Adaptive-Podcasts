#!/usr/bin/env python
"""
Test script for the Quality Trace system.
Tests the explainable quality evaluation with mock data.
"""

import json
from pathlib import Path
from utils.quality_trace import QualityTrace, QualityTraceReport, QualityTraceBuilder, EVALUATION_SEQUENCE
from utils.reasoning_templates import build_reasoning
from utils.quality_evaluator import QualityEvaluator


def create_mock_script():
    """Create a mock enhanced script for testing."""
    return {
        "title": "The Rise of Electronic Music",
        "hook": {
            "text": "What if I told you that the sounds shaping modern music were born from machines that most people thought would never make art? Imagine a world where the boundaries between human creativity and electronic innovation blur into something entirely new.",
            "emotion": "intrigue"
        },
        "modules": [
            {
                "id": 1,
                "title": "The Origins",
                "emotion_arc": "curiosity->wonder",
                "chunks": [
                    {"text": "Electronic music began in the early 20th century.", "emotion": "curiosity", "tension_level": 2},
                    {"text": "Pioneers like Karlheinz Stockhausen pushed boundaries.", "emotion": "wonder", "tension_level": 3},
                    {"text": "The synthesizer changed everything.", "emotion": "excitement", "tension_level": 4},
                ]
            },
            {
                "id": 2,
                "title": "The Revolution",
                "emotion_arc": "tension->triumph",
                "chunks": [
                    {"text": "By the 1980s, electronic music dominated the charts.", "emotion": "triumph", "tension_level": 4},
                    {"text": "Artists like Kraftwerk became legends.", "emotion": "reflection", "tension_level": 3},
                ]
            },
            {
                "id": 3,
                "title": "The Future",
                "emotion_arc": "wonder->reflection",
                "chunks": [
                    {"text": "Today, AI is creating new possibilities.", "emotion": "wonder", "tension_level": 3},
                    {"text": "The story of electronic music continues to unfold.", "emotion": "reflection", "tension_level": 2},
                ]
            }
        ]
    }


def create_mock_tts_results():
    """Create mock TTS results for testing."""
    return [
        {"path": "/tmp/tts_1.wav", "emotion": "intrigue", "speed": 0.95, "duration_ms": 3200},
        {"path": "/tmp/tts_2.wav", "emotion": "curiosity", "speed": 1.0, "duration_ms": 2800},
        {"path": "/tmp/tts_3.wav", "emotion": "wonder", "speed": 1.05, "duration_ms": 3100},
        {"path": "/tmp/tts_4.wav", "emotion": "excitement", "speed": 1.1, "duration_ms": 2500},
        {"path": "/tmp/tts_5.wav", "emotion": "triumph", "speed": 1.0, "duration_ms": 3500},
        {"path": "/tmp/tts_6.wav", "emotion": "reflection", "speed": 0.9, "duration_ms": 2900},
        {"path": "/tmp/tts_7.wav", "emotion": "wonder", "speed": 1.0, "duration_ms": 3000},
        {"path": "/tmp/tts_8.wav", "emotion": "reflection", "speed": 0.95, "duration_ms": 3200},
    ]


def create_mock_bgm_results():
    """Create mock BGM results for testing."""
    return [
        {"path": "/tmp/bgm_1.wav", "emotion": "intrigue", "volume_db": -18},
        {"path": "/tmp/bgm_2.wav", "emotion": "curiosity", "volume_db": -17},
        {"path": "/tmp/bgm_3.wav", "emotion": "triumph", "volume_db": -15},
    ]


def test_quality_trace_builder():
    """Test the QualityTraceBuilder."""
    print("\n" + "=" * 60)
    print("Testing QualityTraceBuilder")
    print("=" * 60)

    trace = (
        QualityTraceBuilder("script")
        .score(85)
        .reasoning("Strong opening hook with attention-grabbing question. Good emotional arc.")
        .add_strength("Attention-grabbing hook")
        .add_strength("Clear emotional progression")
        .add_weakness("Outro could be stronger")
        .sequence(1)
        .raw_metrics({"hook_score": 9, "arc_score": 8})
        .build()
    )

    print(f"Dimension: {trace.dimension}")
    print(f"Score: {trace.score}")
    print(f"Grade: {trace.grade}")
    print(f"Reasoning: {trace.reasoning}")
    print(f"Strengths: {trace.strengths}")
    print(f"Weaknesses: {trace.weaknesses}")
    print(f"Sequence: {trace.sequence}")
    print(f"Raw Metrics: {trace.raw_metrics}")

    assert trace.score == 85
    assert trace.grade == "B"
    assert len(trace.strengths) == 2
    assert len(trace.weaknesses) == 1
    print("\n✓ QualityTraceBuilder test passed!")


def test_reasoning_templates():
    """Test the reasoning templates."""
    print("\n" + "=" * 60)
    print("Testing Reasoning Templates")
    print("=" * 60)

    # Test script reasoning
    script_metrics = {
        "score": 85,
        "hook_score": 9,
        "emotional_arc": 8,
        "narrative_flow": 8,
        "module_balance": 7,
        "emotion_count": 5,
        "has_question": True,
    }

    reasoning, strengths, weaknesses = build_reasoning("script", script_metrics)

    print(f"\nScript Reasoning:")
    print(f"  Reasoning: {reasoning}")
    print(f"  Strengths: {strengths}")
    print(f"  Weaknesses: {weaknesses}")

    # Test voice reasoning
    voice_metrics = {
        "score": 92,
        "sentence_count": 10,
        "failed_count": 0,
        "success_rate": 100,
        "emotion_coverage": 85,
        "speed_variation": 0.2,
    }

    reasoning, strengths, weaknesses = build_reasoning("voice", voice_metrics)

    print(f"\nVoice Reasoning:")
    print(f"  Reasoning: {reasoning}")
    print(f"  Strengths: {strengths}")
    print(f"  Weaknesses: {weaknesses}")

    # Test pacing reasoning
    pacing_metrics = {
        "score": 65,
        "pause_variation_pct": 5,
        "uniform_pause_detected": True,
        "emotion_alignment": 3,
    }

    reasoning, strengths, weaknesses = build_reasoning("pacing", pacing_metrics)

    print(f"\nPacing Reasoning (low score):")
    print(f"  Reasoning: {reasoning}")
    print(f"  Strengths: {strengths}")
    print(f"  Weaknesses: {weaknesses}")

    print("\n✓ Reasoning templates test passed!")


def test_quality_evaluator_traces():
    """Test the QualityEvaluator trace methods."""
    print("\n" + "=" * 60)
    print("Testing QualityEvaluator Trace Methods")
    print("=" * 60)

    evaluator = QualityEvaluator(job_id="test-job-001")

    # Analyze script
    script = create_mock_script()
    evaluator.analyze_script(script)

    # Build script trace
    script_trace = evaluator.build_script_trace()

    print(f"\nScript Trace:")
    print(f"  Score: {script_trace.score} ({script_trace.grade})")
    print(f"  Reasoning: {script_trace.reasoning}")
    print(f"  Strengths: {script_trace.strengths}")
    print(f"  Weaknesses: {script_trace.weaknesses}")
    print(f"  Sequence: {script_trace.sequence}")

    # Manually set some metrics for other dimensions (since we don't have real files)
    evaluator.metrics.voice.sentence_count = 8
    evaluator.metrics.voice.failed_count = 0
    evaluator.metrics.voice.emotion_coverage = 87.5
    evaluator.metrics.voice.speed_variation = 0.2
    evaluator.metrics.voice.avg_duration_ms = 3025

    voice_trace = evaluator.build_voice_trace()

    print(f"\nVoice Trace:")
    print(f"  Score: {voice_trace.score} ({voice_trace.grade})")
    print(f"  Reasoning: {voice_trace.reasoning}")
    print(f"  Strengths: {voice_trace.strengths}")
    print(f"  Weaknesses: {voice_trace.weaknesses}")

    # Set pacing metrics
    evaluator.metrics.pacing.avg_sentence_pause_ms = 350
    evaluator.metrics.pacing.pause_variation_pct = 25
    evaluator.metrics.pacing.emotion_alignment = 7
    evaluator.metrics.pacing.tempo_variation = 0.2
    evaluator.metrics.pacing.uniform_pause_detected = False

    pacing_trace = evaluator.build_pacing_trace()

    print(f"\nPacing Trace:")
    print(f"  Score: {pacing_trace.score} ({pacing_trace.grade})")
    print(f"  Reasoning: {pacing_trace.reasoning}")
    print(f"  Strengths: {pacing_trace.strengths}")
    print(f"  Weaknesses: {pacing_trace.weaknesses}")

    # Set BGM metrics
    evaluator.metrics.bgm.avg_volume_db = -17
    evaluator.metrics.bgm.volume_range_db = 5
    evaluator.metrics.bgm.ducking_detected = True
    evaluator.metrics.bgm.transition_count = 2
    evaluator.metrics.bgm.emotion_alignment = 8

    bgm_trace = evaluator.build_bgm_trace()

    print(f"\nBGM Trace:")
    print(f"  Score: {bgm_trace.score} ({bgm_trace.grade})")
    print(f"  Reasoning: {bgm_trace.reasoning}")
    print(f"  Strengths: {bgm_trace.strengths}")
    print(f"  Weaknesses: {bgm_trace.weaknesses}")

    print("\n✓ QualityEvaluator trace methods test passed!")


def test_trace_report():
    """Test the complete trace report generation."""
    print("\n" + "=" * 60)
    print("Testing QualityTraceReport")
    print("=" * 60)

    evaluator = QualityEvaluator(job_id="test-job-002", output_dir=Path("/tmp/nell_test"))

    # Set up metrics for all dimensions
    script = create_mock_script()
    evaluator.analyze_script(script)

    # Set voice metrics
    evaluator.metrics.voice.sentence_count = 8
    evaluator.metrics.voice.failed_count = 0
    evaluator.metrics.voice.emotion_coverage = 87.5
    evaluator.metrics.voice.speed_variation = 0.2
    evaluator.metrics.voice.avg_duration_ms = 3025

    # Set pacing metrics
    evaluator.metrics.pacing.avg_sentence_pause_ms = 350
    evaluator.metrics.pacing.pause_variation_pct = 25
    evaluator.metrics.pacing.emotion_alignment = 7
    evaluator.metrics.pacing.tempo_variation = 0.2

    # Set BGM metrics
    evaluator.metrics.bgm.avg_volume_db = -17
    evaluator.metrics.bgm.volume_range_db = 5
    evaluator.metrics.bgm.ducking_detected = True
    evaluator.metrics.bgm.transition_count = 2
    evaluator.metrics.bgm.emotion_alignment = 8

    # Set audio mix metrics
    evaluator.metrics.audio_mix.voice_bgm_ratio_db = 15
    evaluator.metrics.audio_mix.loudness_lufs = -15
    evaluator.metrics.audio_mix.clipping_detected = False
    evaluator.metrics.audio_mix.duration_seconds = 180

    # Set video metrics
    evaluator.metrics.video.image_count = 5
    evaluator.metrics.video.avg_image_duration_sec = 8
    evaluator.metrics.video.transition_quality = 7
    evaluator.metrics.video.resolution_ok = True

    # Set ending metrics
    evaluator.metrics.ending.has_outro = True
    evaluator.metrics.ending.fadeout_present = True
    evaluator.metrics.ending.fadeout_duration_ms = 2500
    evaluator.metrics.ending.final_level_db = -45
    evaluator.metrics.ending.is_abrupt = False

    # Set duration metrics
    evaluator.metrics.duration.target_minutes = 3
    evaluator.metrics.duration.actual_minutes = 3.2
    evaluator.metrics.duration.difference_percent = 6.7
    evaluator.metrics.duration.is_within_tolerance = True

    # Build trace report
    report = evaluator.build_trace_report(mode="pro")

    print(f"\nTrace Report Summary:")
    print(f"  Job ID: {report.job_id}")
    print(f"  Mode: {report.mode}")
    print(f"  Overall Score: {report.overall_score} ({report.overall_grade})")
    print(f"  Number of Traces: {len(report.traces)}")

    print(f"\nIndividual Traces:")
    for trace in sorted(report.traces, key=lambda t: t.sequence):
        print(f"\n  [{trace.sequence}] {trace.dimension.upper()}: {trace.score} ({trace.grade})")
        print(f"      {trace.reasoning[:80]}...")
        if trace.strengths:
            print(f"      Strengths: {trace.strengths[:2]}")
        if trace.weaknesses:
            print(f"      Weaknesses: {trace.weaknesses[:2]}")

    # Save report
    report_path = report.save(Path("/tmp/nell_test"))
    print(f"\n  Report saved to: {report_path}")

    # Verify JSON output
    with open(report_path) as f:
        saved_report = json.load(f)

    print(f"\n  Saved report keys: {list(saved_report.keys())}")
    print(f"  Number of saved traces: {len(saved_report['traces'])}")

    print("\n✓ QualityTraceReport test passed!")


def test_progress_stream_integration():
    """Test the ProgressStream trace integration."""
    print("\n" + "=" * 60)
    print("Testing ProgressStream Trace Integration")
    print("=" * 60)

    from utils.progress_stream import ProgressStream

    progress = ProgressStream(mode="pro")

    # Simulate quality trace update
    trace_data = {
        "dimension": "script",
        "score": 85,
        "grade": "B",
        "reasoning": "Strong opening hook with attention-grabbing question.",
        "strengths": ["Attention-grabbing hook", "Clear emotional arc"],
        "weaknesses": ["Outro could be stronger"],
        "suggestions": [],
        "sequence": 1,
        "raw_metrics": {"hook_score": 9},
        "enhanced": False,
    }

    progress.update_quality_trace("script", trace_data)

    # Get quality report
    report = progress._get_quality_report()

    print(f"\nProgress Quality Report:")
    print(f"  Overall Score: {report['overall_score']}")
    print(f"  Number of Scores: {len(report['scores'])}")
    print(f"  Number of Traces: {len(report['traces'])}")

    if report['traces']:
        trace = report['traces'][0]
        print(f"\n  First Trace:")
        print(f"    Dimension: {trace['dimension']}")
        print(f"    Score: {trace['score']}")
        print(f"    Reasoning: {trace['reasoning']}")

    print("\n✓ ProgressStream integration test passed!")


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("QUALITY TRACE SYSTEM TEST SUITE")
    print("=" * 60)

    test_quality_trace_builder()
    test_reasoning_templates()
    test_quality_evaluator_traces()
    test_trace_report()
    test_progress_stream_integration()

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED!")
    print("=" * 60)


if __name__ == "__main__":
    main()
