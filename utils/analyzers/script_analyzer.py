"""
Script Analyzer
Author: Sarath

Analyzes script quality including hook strength, emotional arc,
narrative flow, and module balance.
"""

from typing import Dict, Any, List, Set
from utils.quality_evaluator import ScriptMetrics


# Supported emotions for validation
VALID_EMOTIONS = {
    "wonder", "curiosity", "tension", "triumph", "melancholy",
    "intrigue", "excitement", "reflection", "restlessness",
    "explosive_energy", "rebellion", "liberation", "experimentation",
    "mastery", "intensity", "neutral"
}


class ScriptAnalyzer:
    """Analyzes script quality metrics."""

    def analyze(self, script: Dict[str, Any]) -> ScriptMetrics:
        """
        Analyze script quality.

        Args:
            script: Enhanced script dictionary

        Returns:
            ScriptMetrics with analysis results
        """
        metrics = ScriptMetrics()
        issues = []

        # Count words and structure
        hook = script.get("hook", {})
        modules = script.get("modules", [])

        # Count hook words
        hook_text = hook.get("text", "") if isinstance(hook, dict) else str(hook)
        hook_words = len(hook_text.split())

        # Count module words
        total_words = hook_words
        chunk_count = 0
        module_word_counts = []

        for module in modules:
            module_words = 0
            for chunk in module.get("chunks", []):
                text = chunk.get("text", "")
                module_words += len(text.split())
                chunk_count += 1
            module_word_counts.append(module_words)
            total_words += module_words

        metrics.word_count = total_words
        metrics.module_count = len(modules)
        metrics.chunk_count = chunk_count

        # Analyze hook strength (0-10)
        metrics.hook_score = self._analyze_hook(hook, issues)

        # Analyze emotional arc (0-10)
        metrics.emotional_arc = self._analyze_emotional_arc(script, issues)

        # Analyze narrative flow (0-10)
        metrics.narrative_flow = self._analyze_narrative_flow(modules, issues)

        # Analyze module balance (0-10)
        metrics.module_balance = self._analyze_module_balance(
            module_word_counts, issues
        )

        metrics.issues = issues
        return metrics

    def _analyze_hook(
        self,
        hook: Dict[str, Any],
        issues: List[str]
    ) -> float:
        """Analyze hook quality (0-10 score)."""
        if not hook:
            issues.append("Missing hook section")
            return 0.0

        hook_text = hook.get("text", "") if isinstance(hook, dict) else str(hook)
        hook_words = len(hook_text.split())

        score = 5.0  # Base score

        # Check hook length (ideal: 30-80 words)
        if hook_words < 20:
            issues.append(f"Hook too short ({hook_words} words, ideal: 30-80)")
            score -= 2
        elif hook_words > 100:
            issues.append(f"Hook too long ({hook_words} words, ideal: 30-80)")
            score -= 1
        elif 30 <= hook_words <= 80:
            score += 2

        # Check for hook emotion
        hook_emotion = hook.get("emotion", "") if isinstance(hook, dict) else ""
        if hook_emotion:
            if hook_emotion in {"intrigue", "curiosity", "wonder", "tension"}:
                score += 2  # Good hook emotions
            elif hook_emotion in VALID_EMOTIONS:
                score += 1
        else:
            issues.append("Hook missing emotion tag")

        # Check for attention-grabbing elements
        hook_lower = hook_text.lower()
        attention_markers = [
            "?",           # Questions
            "imagine",     # Engagement
            "what if",     # Curiosity
            "discover",    # Promise
            "secret",      # Intrigue
            "never",       # Contrast
            "but",         # Tension
        ]
        attention_count = sum(1 for m in attention_markers if m in hook_lower)
        if attention_count >= 2:
            score += 1

        return max(0, min(10, score))

    def _analyze_emotional_arc(
        self,
        script: Dict[str, Any],
        issues: List[str]
    ) -> float:
        """Analyze emotional arc quality (0-10 score)."""
        modules = script.get("modules", [])
        if not modules:
            issues.append("No modules found for emotional arc analysis")
            return 0.0

        score = 5.0

        # Collect all emotions
        emotions_used: Set[str] = set()
        tension_levels: List[int] = []

        for module in modules:
            for chunk in module.get("chunks", []):
                emotion = chunk.get("emotion", "neutral")
                emotions_used.add(emotion)
                tension_levels.append(chunk.get("tension_level", 2))

        # Check emotion variety (ideal: 4+ different emotions)
        emotion_count = len(emotions_used)
        if emotion_count >= 5:
            score += 2
        elif emotion_count >= 3:
            score += 1
        elif emotion_count == 1:
            issues.append("Script uses only one emotion - lacks variety")
            score -= 2

        # Check tension variation
        if tension_levels:
            tension_range = max(tension_levels) - min(tension_levels)
            if tension_range >= 3:
                score += 2  # Good tension arc
            elif tension_range >= 2:
                score += 1
            elif tension_range == 0:
                issues.append("No tension variation - flat emotional arc")
                score -= 1

            # Check for peaks (tension 4 or 5)
            has_peak = any(t >= 4 for t in tension_levels)
            if has_peak:
                score += 1
            else:
                issues.append("No emotional peaks (tension 4-5) in script")

        return max(0, min(10, score))

    def _analyze_narrative_flow(
        self,
        modules: List[Dict[str, Any]],
        issues: List[str]
    ) -> float:
        """Analyze narrative flow quality (0-10 score)."""
        if not modules:
            return 0.0

        score = 6.0

        # Check module titles for coherent structure
        titles = [m.get("title", "") for m in modules]
        if all(titles):
            score += 1

        # Check chunk count per module (ideal: 2-4 chunks)
        for i, module in enumerate(modules, 1):
            chunk_count = len(module.get("chunks", []))
            if chunk_count < 2:
                issues.append(f"Module {i} has too few chunks ({chunk_count})")
                score -= 0.5
            elif chunk_count > 5:
                issues.append(f"Module {i} has too many chunks ({chunk_count})")
                score -= 0.5

        # Check for emotion arcs per module
        for i, module in enumerate(modules, 1):
            emotion_arc = module.get("emotion_arc", "")
            if emotion_arc and "->" in emotion_arc:
                score += 0.25  # Has defined progression

        return max(0, min(10, score))

    def _analyze_module_balance(
        self,
        word_counts: List[int],
        issues: List[str]
    ) -> float:
        """Analyze module word count balance (0-10 score)."""
        if not word_counts:
            return 0.0

        score = 7.0
        avg_words = sum(word_counts) / len(word_counts)

        # Check each module against average
        for i, count in enumerate(word_counts, 1):
            deviation_pct = abs(count - avg_words) / avg_words * 100 if avg_words > 0 else 0

            if deviation_pct > 50:
                issues.append(
                    f"Module {i} significantly imbalanced "
                    f"({count} words vs avg {avg_words:.0f})"
                )
                score -= 1.5
            elif deviation_pct > 30:
                score -= 0.5

        # Bonus for good balance
        if all(abs(c - avg_words) / avg_words < 0.2 for c in word_counts if avg_words > 0):
            score += 1

        return max(0, min(10, score))


__all__ = ['ScriptAnalyzer']
