"""
Series Planner Agent
Author: Sarath

Generates comprehensive series outlines with:
- Episode summaries and premises
- Narrative arc structure based on genre templates
- Cliffhanger assignments per episode
- Callback seeds to plant and resolve across episodes
- Thematic progression

Takes a topic + episode_count + StyleDNA and produces a SeriesOutline
ready for user approval.
"""

from typing import Dict, Any, List, Optional
import json

from agents.base_agent import BaseAgent
from config.genre_templates import (
    get_genre_template,
    get_arc_template,
)
from config.cliffhanger_prompts import (
    get_cliffhanger_strategy,
    get_episode_cliffhanger_type,
    CLIFFHANGER_TYPES,
)


class SeriesPlannerAgent(BaseAgent):
    """
    Plans comprehensive series outlines for episodic podcast generation.

    Uses genre templates and arc structures to create compelling multi-episode
    narratives with proper pacing, callbacks, and cliffhangers.
    """

    SYSTEM_PROMPT = """You are an expert podcast series showrunner and narrative architect.
Your specialty is creating binge-worthy, multi-episode podcast series that keep listeners
hooked from episode to episode.

You understand:
- Narrative arc structures (rise and fall, investigation, hero's journey)
- Cliffhanger techniques that create "can't stop listening" moments
- Callback/foreshadowing techniques that reward attentive listeners
- Pacing across episodes (when to reveal, when to withhold)
- Genre-specific storytelling conventions

When planning a series, you create outlines that:
1. Have a clear overall arc with satisfying progression
2. Give each episode a distinct purpose and mini-arc
3. Plant callbacks early that pay off later
4. End episodes with appropriate cliffhangers
5. Build toward a satisfying finale

Your outlines should be specific enough that another writer could execute them."""

    PLANNING_PROMPT = """Create a detailed series outline for a {episode_count}-episode podcast series.

TOPIC: {topic}

STYLE DNA:
- Genre: {genre}
- Era: {era}
- Tone: {tone}
- Arc Template: {arc_template}
- Key Themes: {themes}

EPISODE LENGTH: {episode_length} ({duration_description})

CLIFFHANGER ASSIGNMENTS (these are pre-determined, use them):
{cliffhanger_assignments}

Create a compelling series outline with:
1. A series title that captures the essence
2. A compelling series description/logline (2-3 sentences)
3. The overall arc description (how the story progresses)
4. For EACH episode (1 through {episode_count}):
   - Title (engaging, specific)
   - Premise (2-3 sentences describing what this episode covers)
   - Key points (3-5 bullet points of main content)
   - Callbacks to plant (things to mention that will pay off later)
   - Callbacks to resolve (if referencing earlier episodes)
   - Cliffhanger hint (what makes listeners want the next episode)

IMPORTANT:
- Episode 1 should hook listeners immediately and establish the central mystery/question
- Middle episodes should deepen engagement and plant seeds
- The penultimate episode should have maximum tension
- The final episode should resolve major threads while being satisfying

Return ONLY valid JSON in this format:
{{
    "title": "Series Title",
    "description": "Series logline/description",
    "overall_arc": "Description of the narrative progression",
    "themes": ["theme1", "theme2", "theme3"],
    "episodes": [
        {{
            "episode_number": 1,
            "title": "Episode Title",
            "premise": "What this episode covers",
            "key_points": ["point1", "point2", "point3"],
            "callbacks_to_plant": ["callback1", "callback2"],
            "callbacks_to_resolve": [],
            "cliffhanger_hint": "What makes them want more"
        }}
    ]
}}"""

    def __init__(self, model: str = None):
        """Initialize the SeriesPlannerAgent."""
        super().__init__(
            name="SeriesPlanner",
            output_category="series",
            model=model
        )

    def plan_series(
        self,
        topic: str,
        episode_count: int,
        style_dna: Dict[str, Any],
        episode_length: str = "short"
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive series outline.

        Args:
            topic: Series topic/premise
            episode_count: Number of episodes (3-20)
            style_dna: StyleDNA from IntentAnalyzer
            episode_length: "short" (5-10min) or "medium" (10-20min)

        Returns:
            SeriesOutline dictionary ready for user approval
        """
        self.log(f"Planning {episode_count}-episode series: {topic[:50]}...")

        # Get duration description
        duration_description = "5-10 minutes per episode" if episode_length == "short" else "10-20 minutes per episode"

        # Get cliffhanger assignments
        cliffhanger_assignments = self._get_cliffhanger_assignments(episode_count, style_dna.get("genre", "documentary"))

        # Format themes
        themes = style_dna.get("key_themes", [])
        themes_str = ", ".join(themes) if themes else "engaging narrative"

        # Build the planning prompt
        prompt = self.PLANNING_PROMPT.format(
            episode_count=episode_count,
            topic=topic,
            genre=style_dna.get("genre", "documentary"),
            era=style_dna.get("era", "modern"),
            tone=style_dna.get("tone", "engaging"),
            arc_template=style_dna.get("arc_template", "evolution"),
            themes=themes_str,
            episode_length=episode_length,
            duration_description=duration_description,
            cliffhanger_assignments=cliffhanger_assignments
        )

        # Generate outline via LLM
        try:
            response = self.call_llm(
                prompt,
                max_tokens=4096,
                system_prompt=self.SYSTEM_PROMPT
            )
            outline_data = self.parse_json_response(response)
        except Exception as e:
            self.log(f"LLM planning failed: {e}", level="error")
            raise ValueError(f"Failed to generate series outline: {e}")

        # Enhance outline with cliffhanger types
        outline = self._enhance_outline(
            outline_data,
            episode_count,
            episode_length,
            style_dna
        )

        self.log(f"Generated outline: '{outline['title']}' with {len(outline['episodes'])} episodes")

        return outline

    def _get_cliffhanger_assignments(self, episode_count: int, genre: str) -> str:
        """Get formatted cliffhanger assignments for the prompt."""
        assignments = []

        for ep in range(1, episode_count + 1):
            cliffhanger_type = get_episode_cliffhanger_type(ep, episode_count, genre)

            if cliffhanger_type:
                type_info = CLIFFHANGER_TYPES.get(cliffhanger_type, {})
                description = type_info.get("description", cliffhanger_type)
                assignments.append(f"- Episode {ep}: {cliffhanger_type.upper()} - {description}")
            else:
                assignments.append(f"- Episode {ep}: FINALE - Resolution and satisfaction")

        return "\n".join(assignments)

    def _enhance_outline(
        self,
        outline_data: Dict[str, Any],
        episode_count: int,
        episode_length: str,
        style_dna: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Enhance the LLM-generated outline with structured data.

        Adds cliffhanger types, validates episode count, etc.
        """
        genre = style_dna.get("genre", "documentary")
        episodes = outline_data.get("episodes", [])

        # Ensure we have the right number of episodes
        if len(episodes) < episode_count:
            self.log(f"LLM returned {len(episodes)} episodes, expected {episode_count}", level="warning")
            # Pad with placeholder episodes
            for i in range(len(episodes) + 1, episode_count + 1):
                episodes.append({
                    "episode_number": i,
                    "title": f"Episode {i}",
                    "premise": "To be determined",
                    "key_points": [],
                    "callbacks_to_plant": [],
                    "callbacks_to_resolve": [],
                    "cliffhanger_hint": ""
                })

        # Add cliffhanger types to each episode
        for i, episode in enumerate(episodes):
            ep_num = episode.get("episode_number", i + 1)
            cliffhanger_type = get_episode_cliffhanger_type(ep_num, episode_count, genre)
            episode["cliffhanger_type"] = cliffhanger_type

        # Build final outline structure
        outline = {
            "title": outline_data.get("title", "Untitled Series"),
            "description": outline_data.get("description", ""),
            "episode_count": episode_count,
            "episode_length": episode_length,
            "series_type": style_dna.get("genre", "documentary"),
            "overall_arc": outline_data.get("overall_arc", ""),
            "themes": outline_data.get("themes", style_dna.get("key_themes", [])),
            "episodes": [
                {
                    "episode_number": ep.get("episode_number", i + 1),
                    "title": ep.get("title", f"Episode {i + 1}"),
                    "premise": ep.get("premise", ""),
                    "key_points": ep.get("key_points", []),
                    "cliffhanger_hint": ep.get("cliffhanger_hint", ""),
                    "cliffhanger_type": ep.get("cliffhanger_type"),
                    "callbacks_to_plant": ep.get("callbacks_to_plant", []),
                    "callbacks_to_resolve": ep.get("callbacks_to_resolve", [])
                }
                for i, ep in enumerate(episodes[:episode_count])
            ],
            "style_dna": style_dna
        }

        return outline

    def modify_outline(
        self,
        outline: Dict[str, Any],
        modifications: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Apply user modifications to an outline.

        Args:
            outline: Current outline
            modifications: Dict of changes to apply

        Returns:
            Modified outline
        """
        modified = outline.copy()

        # Apply top-level modifications
        for key in ["title", "description", "overall_arc"]:
            if key in modifications:
                modified[key] = modifications[key]

        # Apply episode modifications
        if "episodes" in modifications:
            for ep_mod in modifications["episodes"]:
                ep_num = ep_mod.get("episode_number")
                if ep_num:
                    for i, ep in enumerate(modified["episodes"]):
                        if ep["episode_number"] == ep_num:
                            for key, value in ep_mod.items():
                                if key != "episode_number":
                                    modified["episodes"][i][key] = value
                            break

        return modified

    def process(
        self,
        topic: str,
        episode_count: int,
        style_dna: Dict[str, Any],
        episode_length: str = "short"
    ) -> Dict[str, Any]:
        """Main entry point - alias for plan_series()."""
        return self.plan_series(topic, episode_count, style_dna, episode_length)


# Convenience function
def plan_series(
    topic: str,
    episode_count: int,
    style_dna: Dict[str, Any],
    episode_length: str = "short"
) -> Dict[str, Any]:
    """
    Quick function to plan a series.

    Args:
        topic: Series topic/premise
        episode_count: Number of episodes
        style_dna: StyleDNA from IntentAnalyzer
        episode_length: "short" or "medium"

    Returns:
        SeriesOutline dictionary
    """
    planner = SeriesPlannerAgent()
    return planner.plan_series(topic, episode_count, style_dna, episode_length)
