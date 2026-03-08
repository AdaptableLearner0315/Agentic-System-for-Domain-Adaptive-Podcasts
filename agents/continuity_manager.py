"""
Continuity Manager Agent
Author: Sarath

Tracks narrative state across episodes including:
- Characters and entities
- Plot points (active, resolved)
- Revealed information (prevents repetition)
- Pending revelations (ensures payoff)
- Callbacks (planted, referenced, resolved)

Generates "Previously on..." narration and provides context
for episode generation to maintain series coherence.
"""

from typing import Dict, Any, List, Optional
import json
from datetime import datetime

from agents.base_agent import BaseAgent
from config.cliffhanger_prompts import get_previously_on_prompt, PREVIOUSLY_ON_STYLES


class ContinuityManager(BaseAgent):
    """
    Manages continuity state across a podcast series.

    Ensures narrative coherence, tracks callbacks, and generates
    "Previously on" recaps that rebuild emotional engagement.
    """

    PREVIOUSLY_ON_SYSTEM = """You are a master podcast editor creating "Previously on..." segments.
Your recaps don't just summarize plot - they rebuild EMOTIONAL STAKES.

A great "Previously on" segment:
1. Reminds listeners WHY they should care (emotional investment)
2. Rebuilds tension from where we left off (especially cliffhangers)
3. References key details that matter for THIS episode
4. Creates immediate engagement and anticipation
5. Is 15-25 seconds when spoken aloud (approximately 40-60 words)

You do NOT give dry plot summaries. You rebuild the emotional state."""

    PREVIOUSLY_ON_PROMPT = """Create a "Previously on..." segment for Episode {episode_number}.

SERIES: {series_title}

PREVIOUS EPISODE ENDED WITH:
{cliffhanger}

KEY PLOT POINTS TO REFERENCE:
{plot_points}

EPISODE {episode_number} WILL COVER:
{upcoming_premise}

{style_instruction}

Write a "Previously on..." narration that:
1. Is 40-60 words (15-25 seconds when spoken)
2. Rebuilds emotional stakes, not just plot
3. References the cliffhanger tension
4. Sets up anticipation for this episode

Write ONLY the narration text, no preamble or formatting."""

    CONTEXT_PROMPT = """Based on the series continuity state below, provide guidance for generating Episode {episode_number}.

SERIES TITLE: {series_title}
EPISODE: {episode_number} of {total_episodes}
EPISODE PREMISE: {premise}

CONTINUITY STATE:
- Characters introduced: {characters}
- Active plot points: {active_plots}
- Information revealed so far: {revealed_info}
- Callbacks to resolve this episode: {callbacks_to_resolve}
- Callbacks to plant this episode: {callbacks_to_plant}

Generate guidance that ensures:
1. No repetition of already-revealed information
2. Callbacks planted earlier get referenced naturally
3. New callbacks are set up for future payoff
4. Character references are consistent
5. Tension builds appropriately

Return guidance as a JSON object:
{{
    "must_include": ["specific things to include"],
    "must_avoid": ["things already covered"],
    "callbacks_to_weave_in": ["natural mentions"],
    "character_reminders": ["who to reference and how"],
    "tension_level": "description of where tension should be"
}}"""

    def __init__(self, model: str = None):
        """Initialize the ContinuityManager."""
        super().__init__(
            name="ContinuityManager",
            output_category="series",
            model=model
        )

    def generate_previously_on(
        self,
        series_title: str,
        episode_number: int,
        continuity_state: Dict[str, Any],
        upcoming_premise: str,
        style: str = "tension"
    ) -> str:
        """
        Generate "Previously on..." narration for an episode.

        Args:
            series_title: Title of the series
            episode_number: Current episode number (must be > 1)
            continuity_state: Current ContinuityState dict
            upcoming_premise: Premise of the episode being generated
            style: Recap style (emotional, tension, callback)

        Returns:
            Narration text for "Previously on" segment
        """
        if episode_number <= 1:
            return None

        self.log(f"Generating 'Previously on' for episode {episode_number}")

        # Get the previous episode's cliffhanger
        summaries = continuity_state.get("episode_summaries", {})
        prev_summary = summaries.get(str(episode_number - 1), "")

        # Get active plot points
        plot_points = continuity_state.get("plot_points", [])
        active_plots = [p for p in plot_points if p.get("status") == "active"]
        plot_str = "\n".join([f"- {p.get('description', '')}" for p in active_plots[:5]])

        # Get style instruction
        style_instruction = PREVIOUSLY_ON_STYLES.get(style, PREVIOUSLY_ON_STYLES["tension"])

        # Build prompt
        prompt = self.PREVIOUSLY_ON_PROMPT.format(
            episode_number=episode_number,
            series_title=series_title,
            cliffhanger=prev_summary or "The story continues...",
            plot_points=plot_str or "The narrative is building...",
            upcoming_premise=upcoming_premise,
            style_instruction=style_instruction
        )

        try:
            response = self.call_llm(
                prompt,
                max_tokens=256,
                system_prompt=self.PREVIOUSLY_ON_SYSTEM
            )
            # Clean up response
            narration = response.strip().strip('"').strip("'")
            self.log(f"Generated previously on ({len(narration.split())} words)")
            return narration
        except Exception as e:
            self.log(f"Failed to generate previously on: {e}", level="error")
            return f"Previously on {series_title}..."

    def get_callbacks_for_episode(
        self,
        episode_number: int,
        outline: Dict[str, Any],
        continuity_state: Dict[str, Any]
    ) -> Dict[str, List[str]]:
        """
        Get callbacks to plant and resolve for an episode.

        Args:
            episode_number: Current episode number
            outline: Series outline
            continuity_state: Current ContinuityState

        Returns:
            Dict with "to_plant" and "to_resolve" lists
        """
        # Get callbacks from outline
        episodes = outline.get("episodes", [])
        episode_outline = None
        for ep in episodes:
            if ep.get("episode_number") == episode_number:
                episode_outline = ep
                break

        callbacks_to_plant = []
        callbacks_to_resolve = []

        if episode_outline:
            callbacks_to_plant = episode_outline.get("callbacks_to_plant", [])
            callbacks_to_resolve = episode_outline.get("callbacks_to_resolve", [])

        # Also check continuity state for planted callbacks due this episode
        tracked_callbacks = continuity_state.get("callbacks", [])
        for cb in tracked_callbacks:
            if cb.get("status") == "planted":
                payoff = cb.get("payoff", {})
                if payoff.get("planned_episode") == episode_number:
                    callbacks_to_resolve.append(cb.get("seed", {}).get("text", ""))

        return {
            "to_plant": callbacks_to_plant,
            "to_resolve": callbacks_to_resolve
        }

    def get_context_for_generation(
        self,
        series_title: str,
        episode_number: int,
        total_episodes: int,
        premise: str,
        outline: Dict[str, Any],
        continuity_state: Dict[str, Any]
    ) -> str:
        """
        Generate guidance context for episode content generation.

        Args:
            series_title: Title of the series
            episode_number: Current episode number
            total_episodes: Total episodes in series
            premise: Episode premise
            outline: Series outline
            continuity_state: Current ContinuityState

        Returns:
            Formatted guidance string for content generation
        """
        # Get callbacks for this episode
        callbacks = self.get_callbacks_for_episode(episode_number, outline, continuity_state)

        # Format characters
        characters = continuity_state.get("characters", [])
        char_str = ", ".join([c.get("name", "") for c in characters[:10]]) or "None yet"

        # Format plot points
        plot_points = continuity_state.get("plot_points", [])
        active_plots = [p.get("description", "") for p in plot_points if p.get("status") == "active"]
        plots_str = "; ".join(active_plots[:5]) or "Story beginning"

        # Format revealed info
        revealed = continuity_state.get("revealed_info", [])
        revealed_str = "; ".join(revealed[-10:]) or "Nothing yet"

        # Build context guidance
        guidance_parts = [
            f"SERIES CONTINUITY FOR EPISODE {episode_number}/{total_episodes}",
            f"Series: {series_title}",
            f"Episode premise: {premise}",
            "",
            "WHAT'S BEEN ESTABLISHED:",
            f"- Characters: {char_str}",
            f"- Active plot points: {plots_str}",
            f"- Already revealed: {revealed_str}",
            "",
            "CALLBACKS:",
            f"- To plant (mention for later): {', '.join(callbacks['to_plant']) or 'None'}",
            f"- To resolve (from earlier): {', '.join(callbacks['to_resolve']) or 'None'}",
            "",
            "INSTRUCTIONS:",
            "- Do NOT repeat already-revealed information",
            "- Reference established characters consistently",
            "- Plant callbacks naturally in the narrative",
            "- Maintain consistent tone and terminology"
        ]

        return "\n".join(guidance_parts)

    def update_state(
        self,
        continuity_state: Dict[str, Any],
        episode_number: int,
        script: Dict[str, Any],
        cliffhanger: Optional[str] = None,
        callbacks_planted: List[str] = None,
        callbacks_resolved: List[str] = None
    ) -> Dict[str, Any]:
        """
        Update continuity state after episode generation.

        Args:
            continuity_state: Current state dict
            episode_number: Episode that was just generated
            script: Generated episode script
            cliffhanger: Episode cliffhanger text
            callbacks_planted: Callbacks planted in this episode
            callbacks_resolved: Callbacks resolved in this episode

        Returns:
            Updated continuity state
        """
        state = continuity_state.copy()

        # Store episode summary (including cliffhanger)
        summaries = state.get("episode_summaries", {})
        summary = cliffhanger or self._extract_summary(script)
        summaries[str(episode_number)] = summary
        state["episode_summaries"] = summaries

        # Update callbacks status
        if callbacks_resolved:
            callbacks = state.get("callbacks", [])
            for cb in callbacks:
                if cb.get("seed", {}).get("text") in callbacks_resolved:
                    cb["status"] = "resolved"
            state["callbacks"] = callbacks

        # Add newly planted callbacks
        if callbacks_planted:
            callbacks = state.get("callbacks", [])
            for text in callbacks_planted:
                callbacks.append({
                    "id": f"cb_{episode_number}_{len(callbacks)}",
                    "seed": {
                        "episode": episode_number,
                        "type": "planted",
                        "text": text,
                        "context": ""
                    },
                    "payoff": {
                        "planned_episode": episode_number + 2,  # Default to 2 episodes later
                        "revelation": "",
                        "impact": ""
                    },
                    "status": "planted"
                })
            state["callbacks"] = callbacks

        # Extract and add any new characters/entities from script
        # (simplified - in production would use NER)
        if script:
            title = script.get("title", "")
            if title:
                revealed = state.get("revealed_info", [])
                revealed.append(f"Episode {episode_number}: {title}")
                state["revealed_info"] = revealed

        return state

    def _extract_summary(self, script: Dict[str, Any]) -> str:
        """Extract a brief summary from a script."""
        if not script:
            return "Episode continues..."

        # Try to get hook text as summary
        hook = script.get("hook", {})
        if isinstance(hook, dict):
            return hook.get("text", "")[:200]
        elif isinstance(hook, str):
            return hook[:200]

        return "Episode continues..."

    def process(self, *args, **kwargs) -> Any:
        """Main entry point - delegates based on operation."""
        raise NotImplementedError("Use specific methods: generate_previously_on, get_context_for_generation, update_state")


# Convenience functions
def create_initial_state() -> Dict[str, Any]:
    """Create an empty continuity state for a new series."""
    return {
        "characters": [],
        "plot_points": [],
        "revealed_info": [],
        "pending_revelations": [],
        "callbacks": [],
        "themes": [],
        "episode_summaries": {}
    }
