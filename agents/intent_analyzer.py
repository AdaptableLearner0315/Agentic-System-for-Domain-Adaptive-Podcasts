"""
Intent Analyzer Agent
Author: Sarath

Automatic style detection from user prompts. Acts as the "Creative Director"
that understands user intent and generates StyleDNA for consistent series identity.

Detects:
- Genre (music history, true crime, biography, documentary, science, narrative)
- Era (1960s, 1970s, 1980s, 1990s, 2000s, retro, modern, futuristic)
- Geography (NYC, London, LA, etc.)
- Arc type (rise-and-fall, investigation, journey, etc.)
- Tone (nostalgic, urgent, celebratory, somber, hopeful)

Outputs StyleDNA that flows through ALL generation for consistent identity.
"""

from typing import Dict, Any, Optional
import json

from agents.base_agent import BaseAgent
from config.era_profiles import (
    ERA_PROFILES,
    get_era_profile,
    detect_era_from_text,
)
from config.genre_templates import (
    GENRE_TEMPLATES,
    get_genre_template,
    detect_genre_from_text,
    get_arc_template,
)


class IntentAnalyzer(BaseAgent):
    """
    Analyzes user prompts to detect creative intent and generate StyleDNA.

    The AI acts as Creative Director by default - automatically understanding
    user intent from the prompt and making all aesthetic decisions.
    """

    SYSTEM_PROMPT = """You are an expert podcast creative director with deep knowledge of:
- Music history across all eras and genres
- Documentary storytelling techniques
- True crime narrative structures
- Biography and profile writing
- Era-specific aesthetics (music, voice, visual styles)

Your job is to analyze a user's series prompt and detect:
1. GENRE: What type of content is this? (music_history, true_crime, biography, documentary, science, narrative_fiction)
2. ERA: What time period does this cover? (1960s, 1970s, 1980s, 1990s, 2000s, retro, modern, futuristic)
3. GEOGRAPHY: What location/culture is central? (e.g., NYC, London, LA, Tokyo, global)
4. ARC_TYPE: What narrative structure fits? (rise_and_fall, investigation, life_journey, discovery, evolution)
5. TONE: What emotional tone should dominate? (nostalgic, urgent, celebratory, somber, hopeful, curious, dramatic)
6. SUB_ERA: More specific time marker if applicable (e.g., "disco" for late 1970s, "grunge" for early 1990s)

Respond with a JSON object. Be specific and confident in your analysis."""

    ANALYSIS_PROMPT = """Analyze this podcast series prompt and determine its creative DNA:

PROMPT: "{prompt}"

{guidance_section}

Based on this prompt, determine:

1. genre: The primary genre (music_history, true_crime, biography, documentary, science, narrative_fiction)
2. era: The dominant time period (1960s, 1970s, 1980s, 1990s, 2000s, retro, modern, futuristic)
3. sub_era: More specific time/style marker (e.g., "disco", "punk", "grunge", "dot_com") or null
4. geography: Primary location/culture (e.g., "new_york", "london", "los_angeles", "global") or null
5. arc_type: Narrative structure (rise_and_fall, investigation, life_journey, discovery, evolution, mystery_reveal)
6. tone: Primary emotional tone (nostalgic, urgent, celebratory, somber, hopeful, curious, dramatic)
7. key_themes: List of 3-5 key themes for the series
8. music_mood: Brief description of ideal music mood
9. voice_style: Brief description of ideal narrator voice

Return ONLY valid JSON in this exact format:
{{
    "genre": "string",
    "era": "string",
    "sub_era": "string or null",
    "geography": "string or null",
    "arc_type": "string",
    "tone": "string",
    "key_themes": ["theme1", "theme2", "theme3"],
    "music_mood": "description",
    "voice_style": "description"
}}"""

    def __init__(self, model: str = None):
        """Initialize the IntentAnalyzer agent."""
        super().__init__(
            name="IntentAnalyzer",
            output_category="series",
            model=model
        )

    def analyze(self, prompt: str, guidance: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze a user prompt to generate StyleDNA.

        Args:
            prompt: User's series topic/premise
            guidance: Optional additional instructions

        Returns:
            Complete StyleDNA dictionary
        """
        self.log(f"Analyzing intent for: {prompt[:50]}...")

        # First, use keyword detection as baseline
        detected_era = detect_era_from_text(prompt)
        detected_genre = detect_genre_from_text(prompt)

        # Build guidance section
        guidance_section = ""
        if guidance:
            guidance_section = f"ADDITIONAL GUIDANCE: {guidance}\n"

        # Use LLM for more nuanced analysis
        analysis_prompt = self.ANALYSIS_PROMPT.format(
            prompt=prompt,
            guidance_section=guidance_section
        )

        try:
            response = self.call_llm(
                analysis_prompt,
                max_tokens=1024,
                system_prompt=self.SYSTEM_PROMPT
            )
            intent = self.parse_json_response(response)
        except Exception as e:
            self.log(f"LLM analysis failed, using keyword detection: {e}", level="warning")
            # Fallback to keyword detection
            intent = {
                "genre": detected_genre,
                "era": detected_era,
                "sub_era": None,
                "geography": None,
                "arc_type": "evolution",
                "tone": "engaging",
                "key_themes": [],
                "music_mood": "engaging and atmospheric",
                "voice_style": "natural NPR style"
            }

        # Build complete StyleDNA from intent + profiles
        style_dna = self._build_style_dna(intent, prompt)

        self.log(f"Detected: genre={style_dna['genre']}, era={style_dna['era']}, tone={style_dna['tone']}")

        return style_dna

    def _build_style_dna(self, intent: Dict[str, Any], prompt: str) -> Dict[str, Any]:
        """
        Build complete StyleDNA from analyzed intent.

        Merges LLM analysis with pre-defined era/genre profiles.
        """
        # Get era profile
        era = intent.get("era", "modern")
        era_profile = get_era_profile(era)

        # Get genre template
        genre = intent.get("genre", "documentary")
        genre_template = get_genre_template(genre)

        # Get arc template based on arc_type
        arc_type = intent.get("arc_type", "evolution")
        arc_template = get_arc_template(genre, arc_type)

        # Build music profile from era + intent
        music_profile = era_profile.get("music_profile", {}).copy()
        if intent.get("music_mood"):
            music_profile["mood"] = intent["music_mood"]

        # Build voice profile from era + intent
        voice_profile = era_profile.get("voice_profile", {}).copy()
        if intent.get("voice_style"):
            voice_profile["reference"] = intent["voice_style"]

        # Build visual profile from era
        visual_profile = era_profile.get("visual_profile", {}).copy()

        # Build language profile from era + genre
        language_profile = era_profile.get("language_profile", {}).copy()
        if intent.get("tone"):
            language_profile["tone"] = intent["tone"]

        # Get cliffhanger strategies from genre
        cliffhanger_strategies = genre_template.get("cliffhanger_strategies", ["question"])
        primary_cliffhanger = cliffhanger_strategies[0] if cliffhanger_strategies else "question"

        # Construct complete StyleDNA
        style_dna = {
            "era": era,
            "sub_era": intent.get("sub_era"),
            "geography": intent.get("geography"),
            "genre": genre,
            "arc_template": arc_type,
            "tone": intent.get("tone", "engaging"),

            "music_profile": music_profile,
            "voice_profile": voice_profile,
            "visual_profile": visual_profile,
            "language_profile": language_profile,

            "cliffhanger_strategy": primary_cliffhanger,
            "key_themes": intent.get("key_themes", []),

            # Original analysis for reference
            "_intent": intent
        }

        return style_dna

    def process(self, prompt: str, guidance: Optional[str] = None) -> Dict[str, Any]:
        """Main entry point - alias for analyze()."""
        return self.analyze(prompt, guidance)

    def get_era_description(self, era: str) -> str:
        """Get a human-readable description of an era's aesthetic."""
        profile = get_era_profile(era)
        return profile.get("description", f"{era} aesthetic")

    def get_genre_description(self, genre: str) -> str:
        """Get a human-readable description of a genre's approach."""
        template = get_genre_template(genre)
        return template.get("description", f"{genre} style content")


# Convenience function for quick analysis
def analyze_intent(prompt: str, guidance: Optional[str] = None) -> Dict[str, Any]:
    """
    Quick function to analyze intent from a prompt.

    Args:
        prompt: User's series topic/premise
        guidance: Optional additional instructions

    Returns:
        StyleDNA dictionary
    """
    analyzer = IntentAnalyzer()
    return analyzer.analyze(prompt, guidance)
