"""
Content Generator Agent
Author: Sarath

Generates original podcast content from topic prompts.
Optionally informed by reference files/content.

Supports three generation modes:
1. Pure Generation: Topic/prompt only → generate from scratch
2. Hybrid Generation: Topic + reference content → generate informed by files
3. Expansion Mode: Reference content + guidance → expand/enhance existing content
"""

from typing import Optional, Dict, Any
from agents.base_agent import BaseAgent
from config.llm import MODEL_OPTIONS


class ContentGeneratorAgent(BaseAgent):
    """
    Generates original podcast content from topic prompts.

    This agent uses Claude to research and generate podcast-ready content,
    optionally informed by reference material from uploaded files.

    Output: Raw transcript text (ready for ScriptDesignerAgent.enhance())
    """

    # Words per minute for podcast narration (standard speaking pace)
    WORDS_PER_MINUTE = 150

    # Length targets for different modes (legacy, kept for backwards compatibility)
    LENGTH_TARGETS = {
        "short": {
            "words": 600,
            "description": "90-120 second podcast (Normal mode)",
        },
        "standard": {
            "words": 1200,
            "description": "5-8 minute podcast (Pro mode)",
        },
        "long": {
            "words": 2000,
            "description": "10-12 minute podcast (Extended)",
        },
    }

    def __init__(self, model: str = None):
        """
        Initialize the Content Generator Agent.

        Args:
            model: LLM model to use for content generation (default: sonnet from config)
        """
        if model is None:
            model = MODEL_OPTIONS["sonnet"]
        super().__init__(
            name="ContentGenerator",
            output_category="",  # Root output directory
            model=model
        )

    def process(self, topic: str, **kwargs) -> str:
        """
        Main processing method (required by BaseAgent).

        Args:
            topic: Topic/prompt for generation
            **kwargs: Additional arguments (reference_content, guidance, length, target_duration_minutes)

        Returns:
            Generated transcript text
        """
        return self.generate(
            topic=topic,
            reference_content=kwargs.get("reference_content"),
            guidance=kwargs.get("guidance"),
            length=kwargs.get("length", "standard"),
            target_duration_minutes=kwargs.get("target_duration_minutes"),
            feedback=kwargs.get("feedback"),
        )

    def generate(
        self,
        topic: str,
        reference_content: Optional[str] = None,
        guidance: Optional[str] = None,
        length: str = "standard",
        target_duration_minutes: Optional[int] = None,
        feedback: Optional[str] = None,
    ) -> str:
        """
        Generate original content about a topic.

        Args:
            topic: Main topic/subject for the podcast
            reference_content: Optional content from reference files to inform generation
            guidance: Optional style/focus guidance (e.g., "for beginners", "technical deep-dive")
            length: Target length - "short" (600w), "standard" (1200w), "long" (2000w)
                    Ignored if target_duration_minutes is provided.
            target_duration_minutes: Target podcast duration in minutes (overrides length)
            feedback: Optional revision feedback from previous attempt

        Returns:
            Raw transcript text (ready for ScriptDesignerAgent.enhance())
        """
        self.log(f"Generating content about: {topic[:50]}...")

        # Determine target words - duration takes priority over length preset
        if target_duration_minutes is not None:
            target_words = target_duration_minutes * self.WORDS_PER_MINUTE
            length_description = f"{target_duration_minutes}-minute podcast"
            self.log(f"Using duration-based target: {target_duration_minutes} min = {target_words} words")
        else:
            # Fall back to length preset
            if length not in self.LENGTH_TARGETS:
                self.log(f"Unknown length '{length}', using 'standard'", level="warning")
                length = "standard"
            target_words = self.LENGTH_TARGETS[length]["words"]
            length_description = self.LENGTH_TARGETS[length]["description"]

        # Build the generation prompt
        prompt = self._build_generation_prompt(
            topic=topic,
            reference_content=reference_content,
            guidance=guidance,
            target_words=target_words,
            length_description=length_description,
            feedback=feedback,
        )

        # Generate content
        response = self.call_llm(prompt, max_tokens=4096, system_prompt=self._system_prompt())

        # Clean up the response
        transcript = self._clean_response(response)

        word_count = len(transcript.split())
        self.log(f"Generated {word_count} words (target: {target_words})")

        return transcript

    def generate_from_topic(self, topic: str, length: str = "standard") -> str:
        """
        Generate content from topic only (pure generation mode).

        Args:
            topic: Topic/subject for the podcast
            length: Target length

        Returns:
            Generated transcript text
        """
        return self.generate(topic=topic, length=length)

    def generate_with_context(
        self,
        topic: str,
        reference_content: str,
        guidance: Optional[str] = None,
        length: str = "standard",
    ) -> str:
        """
        Generate content informed by reference material (hybrid mode).

        Args:
            topic: Topic/subject for the podcast
            reference_content: Content from reference files
            guidance: Optional style/focus guidance
            length: Target length

        Returns:
            Generated transcript text
        """
        return self.generate(
            topic=topic,
            reference_content=reference_content,
            guidance=guidance,
            length=length,
        )

    def expand_content(
        self,
        content: str,
        guidance: Optional[str] = None,
        length: str = "standard",
    ) -> str:
        """
        Expand/enhance existing content with style guidance.

        Args:
            content: Existing content to expand
            guidance: Style/focus guidance
            length: Target length

        Returns:
            Expanded transcript text
        """
        # For expansion mode, the content IS the reference
        # and we derive the topic from it
        return self.generate(
            topic="Expand and enhance the following content",
            reference_content=content,
            guidance=guidance,
            length=length,
        )

    def _system_prompt(self) -> str:
        """System prompt for content generation."""
        return """You are an expert podcast content writer. Your task is to generate engaging,
well-researched content suitable for a podcast episode.

Your content should:
- Be conversational but informative
- Include interesting facts, anecdotes, and narrative hooks
- Create emotional moments (wonder, curiosity, tension, triumph)
- Flow naturally from one topic to the next
- Be suitable for audio narration (avoid visual references like "as you can see")

Output ONLY the raw transcript text. Do NOT include:
- Titles or headings
- Speaker labels
- Stage directions
- Markdown formatting
- Meta-commentary about the content

Write as if you are the narrator speaking directly to the audience."""

    def _build_generation_prompt(
        self,
        topic: str,
        reference_content: Optional[str],
        guidance: Optional[str],
        target_words: int,
        length_description: str,
        feedback: Optional[str],
    ) -> str:
        """Build the generation prompt based on inputs."""

        # Determine generation mode
        has_reference = bool(reference_content)
        is_expansion = topic.lower().startswith("expand")

        if has_reference and not is_expansion:
            # HYBRID MODE: Generate informed by reference material
            prompt = f"""Generate a comprehensive, engaging podcast transcript about the following topic.

TOPIC: {topic}

REFERENCE MATERIAL (use as a source, but expand with additional context and storytelling):
---
{reference_content[:8000]}
---

"""
        elif has_reference and is_expansion:
            # EXPANSION MODE: Enhance existing content
            prompt = f"""Expand and enhance the following content into a full podcast transcript.

EXISTING CONTENT TO EXPAND:
---
{reference_content[:8000]}
---

"""
        else:
            # PURE GENERATION MODE: Generate from scratch
            prompt = f"""Generate a comprehensive, engaging podcast transcript about the following topic.

TOPIC: {topic}

Research and include:
- Key facts and historical context
- Interesting anecdotes and stories
- Expert perspectives and insights
- Relevant examples and analogies

"""

        # Add guidance if provided
        if guidance:
            prompt += f"""
STYLE/FOCUS GUIDANCE:
{guidance}

"""

        # Add length target
        prompt += f"""
TARGET LENGTH: Approximately {target_words} words ({length_description})

"""

        # Add feedback for revision if provided
        if feedback:
            prompt += f"""
REVISION FEEDBACK (address these issues):
{feedback}

"""

        # Add final instruction
        prompt += """
Generate the podcast transcript now. Write in a natural, engaging voice suitable for audio narration.
Output ONLY the transcript text, no titles, headings, or formatting."""

        return prompt

    def _clean_response(self, response: str) -> str:
        """Clean up the LLM response to extract pure transcript text."""
        # Remove common unwanted prefixes
        prefixes_to_remove = [
            "Here is the podcast transcript:",
            "Here's the podcast transcript:",
            "Podcast Transcript:",
            "TRANSCRIPT:",
            "---",
        ]

        text = response.strip()

        for prefix in prefixes_to_remove:
            if text.lower().startswith(prefix.lower()):
                text = text[len(prefix):].strip()

        # Remove markdown formatting
        text = text.replace("**", "")
        text = text.replace("__", "")
        text = text.replace("# ", "")
        text = text.replace("## ", "")
        text = text.replace("### ", "")

        return text.strip()


__all__ = ['ContentGeneratorAgent']
