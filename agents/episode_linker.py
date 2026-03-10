"""
Episode Linker Agent
Author: Sarath

Generates series-connecting elements for episodes:
- Cliffhangers by type (revelation, twist, question, countdown, promise)
- "Next time on..." teasers
- Finalizes episode scripts with series elements

Creates the "can't stop listening" hooks that make series binge-worthy.
"""

from typing import Dict, Any, List, Optional
import json

from agents.base_agent import BaseAgent
from config.cliffhanger_prompts import (
    get_cliffhanger_type,
    get_cliffhanger_prompt,
    CLIFFHANGER_TYPES,
)


class EpisodeLinker(BaseAgent):
    """
    Generates cliffhangers, teasers, and linking elements for series episodes.

    Specializes in creating hooks that compel listeners to continue
    to the next episode.
    """

    CLIFFHANGER_SYSTEM = """You are a master of podcast cliffhangers and hooks.
You understand the psychology of why people can't stop listening to serialized content.

Your cliffhangers:
1. Create genuine curiosity that MUST be satisfied
2. Use specific techniques (revelation, twist, question, countdown, promise)
3. Are concise and punchy - usually 2-3 sentences maximum
4. End at the perfect moment - not too early, not too late
5. Match the tone and genre of the content

You know when to use each type:
- REVELATION: Stop mid-disclosure, leave them desperate to know more
- TWIST: Recontextualize everything, then SILENCE
- QUESTION: Pose a specific, nearly-answerable question
- COUNTDOWN: Create urgency with time pressure
- PROMISE: Use narrator authority to promise something amazing

Your cliffhangers make listeners feel like they NEED the next episode."""

    TEASER_SYSTEM = """You are creating "Next time on..." teasers for podcast episodes.

Great teasers:
1. Hint at what's coming without spoiling
2. Create anticipation and excitement
3. Are brief - 10-15 seconds when spoken (20-35 words)
4. Use evocative language that builds mystery
5. Reference specific but vague elements

Examples of good teasers:
- "Next time: The letter that changed everything. The meeting no one was supposed to know about. And a decision that would echo for decades."
- "Next time: We finally learn what happened that night in Studio 54. And why three people agreed to never speak of it again."
"""

    TEASER_PROMPT = """Create a "Next time on..." teaser for the upcoming episode.

CURRENT EPISODE: {current_episode}
CURRENT EPISODE ENDED WITH: {cliffhanger}

NEXT EPISODE TITLE: {next_title}
NEXT EPISODE PREMISE: {next_premise}

Create a teaser that:
1. Builds on the cliffhanger energy
2. Hints at next episode without spoiling
3. Is 20-35 words (10-15 seconds spoken)
4. Uses evocative, mysterious language

Write ONLY the teaser text, starting with "Next time:" or similar."""

    def __init__(self, model: str = None):
        """Initialize the EpisodeLinker."""
        super().__init__(
            name="EpisodeLinker",
            output_category="series",
            model=model
        )

    def generate_cliffhanger(
        self,
        script: Dict[str, Any],
        cliffhanger_type: str,
        episode_number: int,
        total_episodes: int,
        series_context: Optional[str] = None
    ) -> str:
        """
        Generate a cliffhanger for an episode ending.

        Args:
            script: The episode's enhanced script
            cliffhanger_type: Type of cliffhanger (revelation, twist, etc.)
            episode_number: Current episode number
            total_episodes: Total episodes in series
            series_context: Optional additional context

        Returns:
            Cliffhanger text to end the episode
        """
        # Finale doesn't need a cliffhanger
        if episode_number >= total_episodes:
            self.log(f"Episode {episode_number} is finale - no cliffhanger needed")
            return None

        self.log(f"Generating {cliffhanger_type} cliffhanger for episode {episode_number}")

        # Extract content from script for context
        content = self._extract_script_content(script)

        # Get the cliffhanger prompt template
        prompt = get_cliffhanger_prompt(cliffhanger_type, content)

        # Add series context if provided
        if series_context:
            prompt = f"{series_context}\n\n{prompt}"

        try:
            response = self.call_llm(
                prompt,
                max_tokens=256,
                system_prompt=self.CLIFFHANGER_SYSTEM
            )
            # Clean up response
            cliffhanger = response.strip().strip('"').strip("'")
            self.log(f"Generated {cliffhanger_type} cliffhanger ({len(cliffhanger.split())} words)")
            return cliffhanger
        except Exception as e:
            self.log(f"Failed to generate cliffhanger: {e}", level="error")
            # Return a generic cliffhanger based on type
            return self._fallback_cliffhanger(cliffhanger_type)

    def generate_teaser(
        self,
        current_episode: int,
        cliffhanger: str,
        next_episode_outline: Dict[str, Any]
    ) -> str:
        """
        Generate a "Next time on..." teaser.

        Args:
            current_episode: Current episode number
            cliffhanger: The cliffhanger that ended current episode
            next_episode_outline: Outline for the next episode

        Returns:
            Teaser text for next episode preview
        """
        self.log(f"Generating teaser for episode {current_episode + 1}")

        prompt = self.TEASER_PROMPT.format(
            current_episode=current_episode,
            cliffhanger=cliffhanger or "The story continues...",
            next_title=next_episode_outline.get("title", f"Episode {current_episode + 1}"),
            next_premise=next_episode_outline.get("premise", "The story continues...")
        )

        try:
            response = self.call_llm(
                prompt,
                max_tokens=128,
                system_prompt=self.TEASER_SYSTEM
            )
            teaser = response.strip().strip('"').strip("'")
            self.log(f"Generated teaser ({len(teaser.split())} words)")
            return teaser
        except Exception as e:
            self.log(f"Failed to generate teaser: {e}", level="error")
            return "Next time: The story continues..."

    def finalize_episode_script(
        self,
        script: Dict[str, Any],
        previously_on: Optional[str],
        cliffhanger: Optional[str],
        teaser: Optional[str],
        episode_number: int,
        series_title: str
    ) -> Dict[str, Any]:
        """
        Finalize an episode script with series elements.

        Adds previously_on, cliffhanger, and teaser to the script structure
        in the appropriate positions.

        Args:
            script: Base enhanced script
            previously_on: "Previously on" narration (None for ep 1)
            cliffhanger: Episode cliffhanger text
            teaser: "Next time" teaser text
            episode_number: Episode number
            series_title: Series title

        Returns:
            Finalized script with all series elements
        """
        finalized = script.copy()

        # Add series metadata
        finalized["series_info"] = {
            "series_title": series_title,
            "episode_number": episode_number
        }

        # Add previously_on if present (episodes 2+)
        if previously_on and episode_number > 1:
            finalized["previously_on"] = {
                "text": previously_on,
                "duration_estimate_seconds": len(previously_on.split()) / 2.5  # ~2.5 words/sec
            }

        # Add cliffhanger
        if cliffhanger:
            finalized["cliffhanger"] = {
                "text": cliffhanger,
                "duration_estimate_seconds": len(cliffhanger.split()) / 2.5
            }

        # Add teaser
        if teaser:
            finalized["teaser"] = {
                "text": teaser,
                "duration_estimate_seconds": len(teaser.split()) / 2.5
            }

        return finalized

    def _extract_script_content(self, script: Dict[str, Any]) -> str:
        """Extract text content from script for cliffhanger generation."""
        parts = []

        # Get hook
        hook = script.get("hook", {})
        if isinstance(hook, dict):
            parts.append(hook.get("text", ""))
        elif isinstance(hook, str):
            parts.append(hook)

        # Get module content (last module is most relevant for cliffhanger)
        modules = script.get("modules", [])
        if modules:
            last_module = modules[-1]
            title = last_module.get("title", "")
            parts.append(f"[Section: {title}]")

            chunks = last_module.get("chunks", [])
            for chunk in chunks[-3:]:  # Last 3 chunks
                if isinstance(chunk, dict):
                    parts.append(chunk.get("text", ""))
                elif isinstance(chunk, str):
                    parts.append(chunk)

        return "\n\n".join(filter(None, parts))[-2000:]  # Last 2000 chars

    def _fallback_cliffhanger(self, cliffhanger_type: str) -> str:
        """Generate a simple fallback cliffhanger."""
        fallbacks = {
            "revelation": "But there was something else. Something no one had noticed...",
            "twist": "And that's when everything changed.",
            "question": "The question remained: what really happened?",
            "countdown": "Time was running out. And they were about to discover why.",
            "promise": "What happens next will change your understanding of everything."
        }
        return fallbacks.get(cliffhanger_type, "The story continues...")

    def process(self, *args, **kwargs) -> Any:
        """Main entry point - delegates based on operation."""
        raise NotImplementedError("Use specific methods: generate_cliffhanger, generate_teaser, finalize_episode_script")


# Convenience function
def create_episode_ending(
    script: Dict[str, Any],
    cliffhanger_type: str,
    episode_number: int,
    total_episodes: int
) -> Dict[str, Any]:
    """
    Create the ending elements for an episode.

    Returns dict with cliffhanger and optionally teaser.
    """
    linker = EpisodeLinker()

    result = {
        "cliffhanger": None,
        "teaser": None
    }

    if episode_number < total_episodes:
        result["cliffhanger"] = linker.generate_cliffhanger(
            script, cliffhanger_type, episode_number, total_episodes
        )

    return result
