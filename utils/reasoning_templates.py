"""
Reasoning Templates
Author: Sarath

Template-based reasoning generation for explainable quality evaluation.
Normal mode uses these templates directly (fast, deterministic).
Pro mode uses templates as base, then enhances with LLM.
"""

from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass


@dataclass
class StrengthWeaknessCheck:
    """Defines a check that maps to strength or weakness."""
    check_name: str
    strength_text: str      # Text if check passes
    weakness_text: str      # Text if check fails
    threshold: Optional[float] = None  # Optional threshold for numeric checks


# =============================================================================
# SCRIPT TEMPLATES
# =============================================================================

SCRIPT_REASONING_TEMPLATES = {
    "high": "{hook_assessment}. {arc_assessment}. {flow_note}.",
    "medium": "{hook_assessment}. {arc_assessment}. {flow_note}.",
    "low": "{hook_assessment}. {arc_assessment}. {flow_note}.",
}

SCRIPT_HOOK_ASSESSMENTS = {
    "excellent": "Strong opening hook with {hook_type}",
    "good": "Solid hook that {hook_quality}",
    "weak": "Hook needs work - {hook_issue}",
    "missing": "Missing hook section",
}

SCRIPT_ARC_ASSESSMENTS = {
    "excellent": "Excellent emotional progression across modules",
    "good": "Good emotional arc with {emotion_count} distinct emotions",
    "flat": "Limited emotional variety - script feels {tone}",
    "missing": "No emotional arc defined",
}

SCRIPT_FLOW_NOTES = {
    "smooth": "Smooth transitions throughout",
    "minor_issues": "Minor weakness in {issue_area}",
    "choppy": "Transitions between modules feel {issue_type}",
    "imbalanced": "Module balance could be improved",
}

SCRIPT_STRENGTH_WEAKNESS_CHECKS = [
    StrengthWeaknessCheck(
        "hook_question",
        "Attention-grabbing hook with rhetorical question",
        "Hook lacks engagement trigger (question, surprise)",
    ),
    StrengthWeaknessCheck(
        "hook_emotion",
        "Hook emotion matches opening intent",
        "Hook missing emotion tag",
    ),
    StrengthWeaknessCheck(
        "emotion_variety",
        "Clear emotional arc with variety",
        "Flat emotional tone throughout",
        threshold=3,  # Number of emotions
    ),
    StrengthWeaknessCheck(
        "tension_peaks",
        "Well-placed emotional peaks",
        "No emotional peaks (tension 4-5) in script",
    ),
    StrengthWeaknessCheck(
        "module_transitions",
        "Smooth transitions between modules",
        "Abrupt module transitions",
    ),
    StrengthWeaknessCheck(
        "module_balance",
        "Well-balanced module lengths",
        "Uneven module distribution",
        threshold=30,  # Deviation percentage
    ),
    StrengthWeaknessCheck(
        "outro_conclusion",
        "Strong conclusion in outro",
        "Outro lacks callback to opening hook",
    ),
]

SCRIPT_SUGGESTIONS = [
    ("hook_question", "Add a rhetorical question or surprising fact to the opening"),
    ("emotion_variety", "Introduce more emotional variety across modules"),
    ("tension_peaks", "Add a climactic moment with tension level 4-5"),
    ("outro_conclusion", "Add a callback to the opening question in the outro"),
    ("module_balance", "Redistribute content for more even module lengths"),
]


# =============================================================================
# VOICE TEMPLATES
# =============================================================================

VOICE_REASONING_TEMPLATES = {
    "high": "Voice generation {success_rate}% successful{variation_note}.",
    "medium": "Voice generation mostly successful ({success_rate}%){issue_note}.",
    "low": "Voice generation had issues{failure_note}.",
}

VOICE_STRENGTH_WEAKNESS_CHECKS = [
    StrengthWeaknessCheck(
        "success_rate",
        "Reliable voice generation",
        "{failed_count} of {total_count} voice segments failed",
        threshold=95,  # Success percentage
    ),
    StrengthWeaknessCheck(
        "emotion_coverage",
        "Good emotion expression in delivery",
        "Limited emotion variety in voice",
        threshold=80,  # Coverage percentage
    ),
    StrengthWeaknessCheck(
        "speed_variation",
        "Natural pacing variation",
        "Monotonous delivery speed",
        threshold=0.1,  # Minimum variation
    ),
    StrengthWeaknessCheck(
        "duration_reasonable",
        "Appropriate sentence durations",
        "Some sentences too {duration_issue}",
    ),
]

VOICE_SUGGESTIONS = [
    ("success_rate", "Retry failed TTS segments with alternative voice settings"),
    ("emotion_coverage", "Add more emotion tags to script chunks"),
    ("speed_variation", "Vary speaking speed based on emotional context"),
]


# =============================================================================
# PACING TEMPLATES
# =============================================================================

PACING_REASONING_TEMPLATES = {
    "high": "Natural pacing with {variation_note}{alignment_note}.",
    "medium": "Reasonable pacing{variation_note}{alignment_note}.",
    "low": "Pacing feels {issue_type}{alignment_note}.",
}

PACING_STRENGTH_WEAKNESS_CHECKS = [
    StrengthWeaknessCheck(
        "pause_variation",
        "Natural pause variation between sentences",
        "Uniform pauses create robotic feel",
        threshold=10,  # Variation percentage
    ),
    StrengthWeaknessCheck(
        "emotion_alignment",
        "Pauses match emotional context",
        "Pause durations don't match content emotion",
        threshold=5,  # Alignment score
    ),
    StrengthWeaknessCheck(
        "tempo_variation",
        "Good tempo variation across sections",
        "Flat tempo throughout",
        threshold=0.15,  # Tempo variation
    ),
    StrengthWeaknessCheck(
        "no_uniform_pauses",
        "Dynamic pause durations",
        "Fixed {pause_ms}ms pauses detected",
    ),
]

PACING_SUGGESTIONS = [
    ("pause_variation", "Enable emotion-based pause durations for more natural pacing"),
    ("emotion_alignment", "Adjust pause lengths to match emotional intensity"),
    ("tempo_variation", "Vary narration speed based on content type"),
]


# =============================================================================
# BGM TEMPLATES
# =============================================================================

BGM_REASONING_TEMPLATES = {
    "high": "Background music {ducking_status}{volume_note}{emotion_note}.",
    "medium": "Background music {ducking_status}{volume_note}{emotion_note}.",
    "low": "Background music needs adjustment{issue_note}.",
}

BGM_STRENGTH_WEAKNESS_CHECKS = [
    StrengthWeaknessCheck(
        "ducking_detected",
        "Music ducks appropriately under voice",
        "Music may compete with voice",
    ),
    StrengthWeaknessCheck(
        "volume_range",
        "Dynamic volume variation",
        "Flat background music volume",
        threshold=3,  # dB range
    ),
    StrengthWeaknessCheck(
        "emotion_alignment",
        "BGM mood matches content emotion",
        "BGM mood doesn't match script emotion",
        threshold=6,  # Alignment score out of 10
    ),
    StrengthWeaknessCheck(
        "transition_smoothness",
        "Smooth music transitions",
        "Abrupt music changes between segments",
        threshold=5,  # Smoothness score
    ),
    StrengthWeaknessCheck(
        "volume_appropriate",
        "Appropriate background volume level",
        "BGM volume {volume_issue}",
    ),
]

BGM_SUGGESTIONS = [
    ("ducking_detected", "Enable BGM ducking to prevent voice masking"),
    ("volume_range", "Add dynamic BGM volume variation for emotional impact"),
    ("emotion_alignment", "Adjust BGM prompts to better match script emotions"),
    ("volume_appropriate", "Adjust BGM volume to -18dB target level"),
]


# =============================================================================
# AUDIO MIX TEMPLATES
# =============================================================================

AUDIO_MIX_REASONING_TEMPLATES = {
    "high": "Clean audio mix with {ratio_note}{loudness_note}.",
    "medium": "Acceptable audio mix{ratio_note}{loudness_note}.",
    "low": "Audio mix has issues{issue_note}.",
}

AUDIO_MIX_STRENGTH_WEAKNESS_CHECKS = [
    StrengthWeaknessCheck(
        "no_clipping",
        "Clean audio without distortion",
        "Audio clipping detected",
    ),
    StrengthWeaknessCheck(
        "voice_bgm_ratio",
        "Good voice-to-BGM ratio ({ratio}dB)",
        "Voice-to-BGM ratio outside ideal range",
        threshold=12,  # Minimum dB ratio
    ),
    StrengthWeaknessCheck(
        "loudness_target",
        "Loudness meets broadcast standards",
        "Loudness ({lufs} LUFS) outside target range",
    ),
    StrengthWeaknessCheck(
        "dynamic_range",
        "Healthy dynamic range",
        "Over-compressed audio",
        threshold=6,  # Minimum dB range
    ),
]

AUDIO_MIX_SUGGESTIONS = [
    ("no_clipping", "Reduce gain to prevent audio clipping"),
    ("voice_bgm_ratio", "Adjust voice-to-BGM ratio to 12-18dB range"),
    ("loudness_target", "Normalize to -14 to -16 LUFS for streaming"),
]


# =============================================================================
# VIDEO TEMPLATES
# =============================================================================

VIDEO_REASONING_TEMPLATES = {
    "high": "Video quality is {quality_assessment}{timing_note}.",
    "medium": "Video meets requirements{timing_note}.",
    "low": "Video has {issue_type}{issue_note}.",
}

VIDEO_STRENGTH_WEAKNESS_CHECKS = [
    StrengthWeaknessCheck(
        "resolution_ok",
        "Standard resolution (1080p/720p)",
        "Non-standard resolution",
    ),
    StrengthWeaknessCheck(
        "image_timing",
        "Good image-to-audio timing",
        "Image durations {timing_issue}",
        threshold=3,  # Minimum seconds per image
    ),
    StrengthWeaknessCheck(
        "transition_quality",
        "Smooth image transitions",
        "Abrupt image changes",
        threshold=5,  # Quality score
    ),
    StrengthWeaknessCheck(
        "image_count",
        "Sufficient visual variety",
        "Limited number of images",
        threshold=3,  # Minimum images
    ),
]

VIDEO_SUGGESTIONS = [
    ("image_timing", "Adjust image durations to 3-15 seconds for better pacing"),
    ("transition_quality", "Add crossfade transitions between images"),
    ("image_count", "Generate more images for visual variety"),
]


# =============================================================================
# ENDING TEMPLATES
# =============================================================================

ENDING_REASONING_TEMPLATES = {
    "high": "Clean ending with {fadeout_note}{outro_note}.",
    "medium": "Acceptable ending{fadeout_note}{outro_note}.",
    "low": "Ending needs work{issue_note}.",
}

ENDING_STRENGTH_WEAKNESS_CHECKS = [
    StrengthWeaknessCheck(
        "has_fadeout",
        "Proper audio fadeout",
        "Missing fadeout - ends abruptly",
    ),
    StrengthWeaknessCheck(
        "has_outro",
        "Dedicated outro section",
        "No clear conclusion/outro",
    ),
    StrengthWeaknessCheck(
        "not_abrupt",
        "Smooth ending transition",
        "Abrupt audio cutoff detected",
    ),
    StrengthWeaknessCheck(
        "final_level",
        "Clean fade to silence",
        "Final audio level too high ({level}dB)",
        threshold=-40,  # Maximum dB
    ),
]

ENDING_SUGGESTIONS = [
    ("has_fadeout", "Add 2-3 second fadeout to final audio"),
    ("has_outro", "Ensure outro module has clear conclusion"),
    ("not_abrupt", "Extend audio tail to prevent abrupt ending"),
]


# =============================================================================
# DURATION TEMPLATES
# =============================================================================

DURATION_REASONING_TEMPLATES = {
    "high": "Duration {actual}min matches target {target}min ({deviation}).",
    "medium": "Duration {actual}min is {deviation_note} target {target}min.",
    "low": "Duration {actual}min differs significantly from target {target}min.",
}

DURATION_STRENGTH_WEAKNESS_CHECKS = [
    StrengthWeaknessCheck(
        "within_tolerance",
        "Duration within acceptable range",
        "Duration {deviation}% outside target",
        threshold=15,  # Percentage tolerance
    ),
    StrengthWeaknessCheck(
        "close_to_target",
        "Very close to target duration",
        "Noticeable duration deviation",
        threshold=5,  # Percentage for "close"
    ),
]

DURATION_SUGGESTIONS = [
    ("too_long", "Consider tightening script or increasing narration pace"),
    ("too_short", "Consider expanding content or adding more detail"),
]


# =============================================================================
# TEMPLATE HELPERS
# =============================================================================

def get_score_tier(score: int) -> str:
    """Get tier (high/medium/low) based on score."""
    if score >= 80:
        return "high"
    elif score >= 60:
        return "medium"
    return "low"


def format_template(template: str, **kwargs) -> str:
    """
    Safely format a template string with provided values.

    Missing keys are replaced with empty strings.
    """
    # Create a default dict that returns empty string for missing keys
    class SafeDict(dict):
        def __missing__(self, key):
            return ""

    return template.format_map(SafeDict(**kwargs))


def build_script_reasoning(metrics: Dict[str, Any]) -> Tuple[str, List[str], List[str]]:
    """
    Build reasoning, strengths, and weaknesses for script dimension.

    Args:
        metrics: Raw script metrics dictionary

    Returns:
        Tuple of (reasoning, strengths, weaknesses)
    """
    score = metrics.get("score", 0)
    tier = get_score_tier(score)

    strengths = []
    weaknesses = []

    # Hook assessment
    hook_score = metrics.get("hook_score", 0)
    if hook_score >= 8:
        hook_assessment = SCRIPT_HOOK_ASSESSMENTS["excellent"].format(
            hook_type="attention-grabbing question" if metrics.get("has_question") else "strong opening"
        )
        strengths.append("Attention-grabbing hook")
    elif hook_score >= 5:
        hook_assessment = SCRIPT_HOOK_ASSESSMENTS["good"].format(
            hook_quality="engages the listener"
        )
    else:
        hook_issue = metrics.get("hook_issue", "lacks engagement")
        hook_assessment = SCRIPT_HOOK_ASSESSMENTS["weak"].format(hook_issue=hook_issue)
        weaknesses.append("Hook lacks engagement trigger")

    # Emotional arc assessment
    emotion_count = metrics.get("emotion_count", 0)
    arc_score = metrics.get("emotional_arc", 0)
    if arc_score >= 8:
        arc_assessment = SCRIPT_ARC_ASSESSMENTS["excellent"]
        strengths.append("Clear emotional arc with variety")
    elif arc_score >= 5:
        arc_assessment = SCRIPT_ARC_ASSESSMENTS["good"].format(emotion_count=emotion_count)
        if emotion_count >= 3:
            strengths.append(f"Good emotion variety ({emotion_count} types)")
    else:
        arc_assessment = SCRIPT_ARC_ASSESSMENTS["flat"].format(tone="monotone")
        weaknesses.append("Limited emotional variety")

    # Flow note
    flow_score = metrics.get("narrative_flow", 0)
    balance_score = metrics.get("module_balance", 0)
    if flow_score >= 8 and balance_score >= 7:
        flow_note = SCRIPT_FLOW_NOTES["smooth"]
        strengths.append("Smooth transitions between modules")
    elif flow_score >= 5:
        issue_area = "outro transition" if balance_score < 7 else "some transitions"
        flow_note = SCRIPT_FLOW_NOTES["minor_issues"].format(issue_area=issue_area)
        weaknesses.append(f"Minor weakness in {issue_area}")
    else:
        flow_note = SCRIPT_FLOW_NOTES["choppy"].format(issue_type="abrupt")
        weaknesses.append("Transitions feel choppy")

    template = SCRIPT_REASONING_TEMPLATES[tier]
    reasoning = format_template(
        template,
        hook_assessment=hook_assessment,
        arc_assessment=arc_assessment,
        flow_note=flow_note
    )

    return reasoning, strengths, weaknesses


def build_voice_reasoning(metrics: Dict[str, Any]) -> Tuple[str, List[str], List[str]]:
    """Build reasoning, strengths, and weaknesses for voice dimension."""
    score = metrics.get("score", 0)
    tier = get_score_tier(score)

    strengths = []
    weaknesses = []

    success_rate = metrics.get("success_rate", 100)
    failed_count = metrics.get("failed_count", 0)
    total_count = metrics.get("sentence_count", 0)

    if success_rate >= 95:
        strengths.append("Reliable voice generation")
        variation_note = " with natural variation"
    else:
        weaknesses.append(f"{failed_count} voice segments failed")
        variation_note = ""

    emotion_coverage = metrics.get("emotion_coverage", 0)
    if emotion_coverage >= 80:
        strengths.append("Good emotion expression in delivery")
    elif emotion_coverage < 50:
        weaknesses.append("Limited emotion variety in voice")

    speed_variation = metrics.get("speed_variation", 0)
    if speed_variation >= 0.1:
        strengths.append("Natural pacing variation")
    else:
        weaknesses.append("Monotonous delivery speed")

    template = VOICE_REASONING_TEMPLATES[tier]
    reasoning = format_template(
        template,
        success_rate=int(success_rate),
        variation_note=variation_note,
        issue_note=f" - {failed_count} segments failed" if failed_count > 0 else "",
        failure_note=f" - {failed_count}/{total_count} failed" if failed_count > 0 else ""
    )

    return reasoning, strengths, weaknesses


def build_pacing_reasoning(metrics: Dict[str, Any]) -> Tuple[str, List[str], List[str]]:
    """Build reasoning, strengths, and weaknesses for pacing dimension."""
    score = metrics.get("score", 0)
    tier = get_score_tier(score)

    strengths = []
    weaknesses = []

    pause_variation = metrics.get("pause_variation_pct", 0)
    uniform_detected = metrics.get("uniform_pause_detected", False)
    emotion_alignment = metrics.get("emotion_alignment", 0)

    if not uniform_detected and pause_variation >= 10:
        strengths.append("Natural pause variation between sentences")
        variation_note = "varied pause durations"
    else:
        weaknesses.append("Uniform pauses create robotic feel")
        variation_note = "uniform pauses"

    if emotion_alignment >= 5:
        strengths.append("Pauses match emotional context")
        alignment_note = " and emotion-aligned timing"
    else:
        weaknesses.append("Pause durations don't match content emotion")
        alignment_note = ""

    template = PACING_REASONING_TEMPLATES[tier]
    reasoning = format_template(
        template,
        variation_note=variation_note,
        alignment_note=alignment_note,
        issue_type="robotic" if uniform_detected else "uneven"
    )

    return reasoning, strengths, weaknesses


def build_bgm_reasoning(metrics: Dict[str, Any]) -> Tuple[str, List[str], List[str]]:
    """Build reasoning, strengths, and weaknesses for BGM dimension."""
    score = metrics.get("score", 0)
    tier = get_score_tier(score)

    strengths = []
    weaknesses = []

    ducking = metrics.get("ducking_detected", False)
    volume_range = metrics.get("volume_range_db", 0)
    emotion_alignment = metrics.get("emotion_alignment", 0)
    avg_volume = metrics.get("avg_volume_db", -18)

    if ducking:
        strengths.append("Music ducks appropriately under voice")
        ducking_status = "ducks well under voice"
    else:
        weaknesses.append("Music may compete with voice")
        ducking_status = "needs ducking adjustment"

    if volume_range >= 3:
        strengths.append("Dynamic volume variation")
        volume_note = " with dynamic variation"
    else:
        weaknesses.append("Flat background music volume")
        volume_note = ""

    if emotion_alignment >= 6:
        strengths.append("BGM mood matches content emotion")
        emotion_note = " and matches content mood"
    else:
        emotion_note = ""

    # Volume level check
    if avg_volume > -10:
        weaknesses.append("BGM volume too loud")
    elif avg_volume < -25:
        weaknesses.append("BGM volume too quiet")
    else:
        strengths.append("Appropriate background volume level")

    template = BGM_REASONING_TEMPLATES[tier]
    reasoning = format_template(
        template,
        ducking_status=ducking_status,
        volume_note=volume_note,
        emotion_note=emotion_note,
        issue_note=" - volume or ducking issues"
    )

    return reasoning, strengths, weaknesses


def build_audio_mix_reasoning(metrics: Dict[str, Any]) -> Tuple[str, List[str], List[str]]:
    """Build reasoning, strengths, and weaknesses for audio mix dimension."""
    score = metrics.get("score", 0)
    tier = get_score_tier(score)

    strengths = []
    weaknesses = []

    clipping = metrics.get("clipping_detected", False)
    ratio = metrics.get("voice_bgm_ratio_db", 0)
    lufs = metrics.get("loudness_lufs", -16)

    if not clipping:
        strengths.append("Clean audio without distortion")
    else:
        weaknesses.append("Audio clipping detected")

    if 12 <= ratio <= 18:
        strengths.append(f"Good voice-to-BGM ratio ({ratio:.0f}dB)")
        ratio_note = f"good {ratio:.0f}dB voice-BGM ratio"
    else:
        weaknesses.append("Voice-to-BGM ratio outside ideal range")
        ratio_note = "voice-BGM ratio needs adjustment"

    if -16 <= lufs <= -14:
        strengths.append("Loudness meets broadcast standards")
        loudness_note = " and proper loudness"
    else:
        weaknesses.append(f"Loudness ({lufs:.1f} LUFS) outside target range")
        loudness_note = ""

    template = AUDIO_MIX_REASONING_TEMPLATES[tier]
    reasoning = format_template(
        template,
        ratio_note=ratio_note,
        loudness_note=loudness_note,
        issue_note=" - clipping or level issues" if clipping else ""
    )

    return reasoning, strengths, weaknesses


def build_video_reasoning(metrics: Dict[str, Any]) -> Tuple[str, List[str], List[str]]:
    """Build reasoning, strengths, and weaknesses for video dimension."""
    score = metrics.get("score", 0)
    tier = get_score_tier(score)

    strengths = []
    weaknesses = []

    resolution_ok = metrics.get("resolution_ok", True)
    image_count = metrics.get("image_count", 0)
    avg_duration = metrics.get("avg_image_duration_sec", 0)
    transition_quality = metrics.get("transition_quality", 0)

    if resolution_ok:
        strengths.append("Standard resolution (1080p/720p)")
        quality_assessment = "good"
    else:
        weaknesses.append("Non-standard resolution")
        quality_assessment = "acceptable"

    if 3 <= avg_duration <= 15:
        strengths.append("Good image-to-audio timing")
        timing_note = " with good visual pacing"
    elif avg_duration < 3:
        weaknesses.append("Image durations too short")
        timing_note = " but images change too quickly"
    else:
        weaknesses.append("Image durations too long")
        timing_note = " but images linger too long"

    if transition_quality >= 5:
        strengths.append("Smooth image transitions")
    else:
        weaknesses.append("Abrupt image changes")

    if image_count >= 3:
        strengths.append("Sufficient visual variety")
    else:
        weaknesses.append("Limited number of images")

    template = VIDEO_REASONING_TEMPLATES[tier]
    reasoning = format_template(
        template,
        quality_assessment=quality_assessment,
        timing_note=timing_note,
        issue_type="resolution or timing issues",
        issue_note=""
    )

    return reasoning, strengths, weaknesses


def build_ending_reasoning(metrics: Dict[str, Any]) -> Tuple[str, List[str], List[str]]:
    """Build reasoning, strengths, and weaknesses for ending dimension."""
    score = metrics.get("score", 0)
    tier = get_score_tier(score)

    strengths = []
    weaknesses = []

    has_fadeout = metrics.get("fadeout_present", False)
    has_outro = metrics.get("has_outro", False)
    is_abrupt = metrics.get("is_abrupt", False)
    final_level = metrics.get("final_level_db", 0)

    if has_fadeout:
        strengths.append("Proper audio fadeout")
        fadeout_note = "proper fadeout"
    else:
        weaknesses.append("Missing fadeout - ends abruptly")
        fadeout_note = "no fadeout"

    if has_outro:
        strengths.append("Dedicated outro section")
        outro_note = " and clear conclusion"
    else:
        weaknesses.append("No clear conclusion/outro")
        outro_note = ""

    if not is_abrupt:
        strengths.append("Smooth ending transition")
    else:
        weaknesses.append("Abrupt audio cutoff detected")

    if final_level < -40:
        strengths.append("Clean fade to silence")
    else:
        weaknesses.append(f"Final audio level too high ({final_level:.0f}dB)")

    template = ENDING_REASONING_TEMPLATES[tier]
    reasoning = format_template(
        template,
        fadeout_note=fadeout_note,
        outro_note=outro_note,
        issue_note=" - abrupt ending detected" if is_abrupt else ""
    )

    return reasoning, strengths, weaknesses


def build_duration_reasoning(metrics: Dict[str, Any]) -> Tuple[str, List[str], List[str]]:
    """Build reasoning, strengths, and weaknesses for duration dimension."""
    score = metrics.get("score", 0)
    tier = get_score_tier(score)

    strengths = []
    weaknesses = []

    target = metrics.get("target_minutes", 0)
    actual = metrics.get("actual_minutes", 0)
    deviation = metrics.get("difference_percent", 0)
    within_tolerance = metrics.get("is_within_tolerance", True)

    if within_tolerance:
        if abs(deviation) <= 5:
            strengths.append("Very close to target duration")
            deviation_text = "on target"
        else:
            strengths.append("Duration within acceptable range")
            deviation_text = f"{deviation:+.0f}% from target"
    else:
        weaknesses.append(f"Duration {deviation:+.0f}% outside target")
        deviation_text = f"{deviation:+.0f}% deviation"

    template = DURATION_REASONING_TEMPLATES[tier]
    reasoning = format_template(
        template,
        actual=f"{actual:.1f}",
        target=f"{target:.1f}",
        deviation=deviation_text,
        deviation_note="slightly" if abs(deviation) < 10 else "noticeably"
    )

    return reasoning, strengths, weaknesses


# Mapping of dimensions to their reasoning builders
REASONING_BUILDERS = {
    "script": build_script_reasoning,
    "voice": build_voice_reasoning,
    "pacing": build_pacing_reasoning,
    "bgm": build_bgm_reasoning,
    "audio_mix": build_audio_mix_reasoning,
    "video": build_video_reasoning,
    "ending": build_ending_reasoning,
    "duration": build_duration_reasoning,
}


def build_reasoning(dimension: str, metrics: Dict[str, Any]) -> Tuple[str, List[str], List[str]]:
    """
    Build reasoning, strengths, and weaknesses for any dimension.

    Args:
        dimension: Quality dimension name
        metrics: Raw metrics dictionary for the dimension

    Returns:
        Tuple of (reasoning, strengths, weaknesses)
    """
    builder = REASONING_BUILDERS.get(dimension)
    if builder:
        return builder(metrics)
    return "Analysis complete.", [], []


__all__ = [
    'REASONING_BUILDERS',
    'build_reasoning',
    'build_script_reasoning',
    'build_voice_reasoning',
    'build_pacing_reasoning',
    'build_bgm_reasoning',
    'build_audio_mix_reasoning',
    'build_video_reasoning',
    'build_ending_reasoning',
    'build_duration_reasoning',
    'get_score_tier',
    'format_template',
]
