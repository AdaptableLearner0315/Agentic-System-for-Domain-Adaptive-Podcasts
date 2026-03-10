"""
Script Designer Agent
Author: Sarath

Transforms raw podcast transcripts into engaging, structured content with:
- Emotion mapping for each segment
- Dynamic module structure based on target duration
- Compelling opening hook (8% of total)
- Keywords, visual cues, and audio cues for each chunk

Inherits from BaseAgent for common LLM and output functionality.
"""

from typing import Dict, Any, Optional, Tuple
from agents.base_agent import BaseAgent
from config.llm import MODEL_OPTIONS


# Words per minute for podcast narration
WORDS_PER_MINUTE = 150

# Duration-to-module mapping
DURATION_MODULE_MAP = {
    (1, 3): 2,    # 1-3 min -> 2 modules
    (4, 7): 3,    # 4-7 min -> 3 modules
    (8, 12): 4,   # 8-12 min -> 4 modules
    (13, 18): 5,  # 13-18 min -> 5 modules
    (19, 30): 6,  # 19+ min -> 6 modules
}


def calculate_script_structure(duration_minutes: int) -> Dict[str, Any]:
    """
    Calculate script structure based on target duration.

    Args:
        duration_minutes: Target podcast duration in minutes

    Returns:
        Dictionary with:
        - num_modules: Number of content modules
        - total_words: Total word target
        - hook_words: Word target for hook (8% of total)
        - words_per_module: Word target per module
        - hook_seconds: Duration estimate for hook
    """
    # Clamp duration to valid range
    duration_minutes = max(1, min(30, duration_minutes))

    # Determine number of modules
    num_modules = 4  # Default
    for (low, high), modules in DURATION_MODULE_MAP.items():
        if low <= duration_minutes <= high:
            num_modules = modules
            break

    # Calculate word targets
    total_words = duration_minutes * WORDS_PER_MINUTE
    hook_words = int(total_words * 0.08)  # 8% for hook
    content_words = total_words - hook_words
    words_per_module = content_words // num_modules

    # Calculate hook duration in seconds
    hook_seconds = int((hook_words / WORDS_PER_MINUTE) * 60)

    return {
        "num_modules": num_modules,
        "total_words": total_words,
        "hook_words": hook_words,
        "words_per_module": words_per_module,
        "hook_seconds": hook_seconds,
        "duration_minutes": duration_minutes,
    }


CONVERSATIONAL_STYLE_GUIDELINES = """
## Conversational Drama Guidelines

Create an engaging two-person dialogue with these elements:

**Cliffhangers & Suspense:**
- End each module with an unresolved question or teaser
- Host 1 hints at information Host 2 (and the audience) doesn't know yet
- Use phrases like "But here's where it gets interesting..." or "Wait, you haven't heard the best part"

**Mystery & Reveals:**
- Structure information as a gradual reveal across modules
- Plant questions early, answer them later
- Create "aha moments" where pieces click together

**Pacing & Tension:**
- Alternate between rapid-fire exchanges (tension) and longer explanations (breathing room)
- Build tension_level from 1→5 across each module, reset at module boundaries
- Use interruptions and reactions: "Wait, are you serious?" / "Hold on, let me get this straight..."

**Speaker Dynamics:**
- Host 1 (host_1): The knowledgeable one who controls the reveals
- Host 2 (host_2): The curious one who asks the questions the audience is thinking
- Natural back-and-forth, not scripted Q&A

**Emotional Arc per Module:**
- Opening: Intrigue hook
- Middle: Building tension with new information
- End: Cliffhanger or partial reveal that demands continuation

**IMPORTANT:** Use "host_1" and "host_2" as speaker values in every chunk. Alternate speakers naturally for engaging dialogue.
"""


def build_enhancement_prompt(
    transcript: str,
    structure: Dict[str, Any],
    feedback: Optional[str] = None,
    conversational_style: bool = False
) -> str:
    """
    Build the enhancement prompt with dynamic duration targets.

    Args:
        transcript: Raw transcript text
        structure: Output from calculate_script_structure()
        feedback: Optional feedback from director

    Returns:
        Formatted enhancement prompt
    """
    num_modules = structure["num_modules"]
    total_words = structure["total_words"]
    hook_words = structure["hook_words"]
    words_per_module = structure["words_per_module"]
    hook_seconds = structure["hook_seconds"]
    duration_minutes = structure["duration_minutes"]

    # Calculate chunks per module (scale with duration)
    chunks_per_module = 2 if duration_minutes <= 3 else (3 if duration_minutes <= 10 else 4)

    feedback_section = ""
    if feedback:
        feedback_section = f"""
## Director Feedback (Address these issues):
{feedback}

Please revise the script to address the feedback above while maintaining engagement.
"""

    # Add conversational style guidelines if enabled
    conversational_section = ""
    if conversational_style:
        conversational_section = CONVERSATIONAL_STYLE_GUIDELINES

    return f"""You are an expert podcast script enhancer. Your job is to transform a raw transcript into an engaging, emotionally compelling podcast script.

## CRITICAL DURATION REQUIREMENTS:
- **Total script duration target: {duration_minutes} minutes** (approximately {total_words} words total)
- **Hook: ~{hook_seconds} seconds** (~{hook_words} words)
- **Each Module: ~{words_per_module} words**
- **{num_modules} Modules total**
- **Each module should have {chunks_per_module}-{chunks_per_module + 1} chunks** for varied pacing

## Your Tasks:

1. **Create a Hook (~{hook_seconds} seconds / ~{hook_words} words)**: Write a compelling opening that immediately captures attention. This should create intrigue, mystery, or emotional connection. Make it substantial enough to set the scene.

2. **Structure into EXACTLY {num_modules} Modules (~{words_per_module} words each)**: Divide the content into distinct emotional modules that create a "roller-coaster" experience:
   - Each module should have a clear emotional identity
   - Each module MUST have {chunks_per_module}-{chunks_per_module + 1} chunks
   - Arrange modules for maximum engagement (don't follow chronological order if suspense is better)
   - Create tension peaks and valleys
   - IMPORTANT: Use ALL the content from the transcript, don't summarize too much

3. **Emotion Mapping**: Tag each chunk with:
   - Primary emotion: wonder, curiosity, tension, triumph, melancholy, intrigue, excitement, reflection, liberation, mastery
   - Tension level: 1-5 (1=calm reflection, 5=peak tension/excitement)

4. **Extract Metadata**: For each chunk, identify:
   - Keywords: 3-5 words for sound/visual design (e.g., "volcano", "Iceland", "childhood")
   - Visual cues: What images would enhance this? (e.g., "misty volcanic landscape", "small girl at piano")
   - Audio cues: What sounds would enhance this? (e.g., "ambient wind", "soft piano", "crowd cheering")

## Output Format (JSON):
```json
{{{{
  "title": "Episode title",
  "target_duration_minutes": {duration_minutes},
  "hook": {{{{
    "text": "The compelling opening text...",
    "emotion": "intrigue",
    "duration_estimate_seconds": {hook_seconds},
    "speaker": "narrator",
    "visual_cues": ["visual description for hook"]
  }}}},
  "modules": [
    {{{{
      "id": 1,
      "title": "Module Title",
      "emotion_arc": "curiosity -> wonder",
      "chunks": [
        {{{{
          "text": "The actual content text...",
          "emotion": "wonder",
          "tension_level": 3,
          "keywords": ["keyword1", "keyword2"],
          "visual_cues": ["visual description 1"],
          "audio_cues": ["audio description 1"],
          "speaker": "narrator"
        }}}}
      ]
    }}}}
  ]
}}}}
```

## Speaker Assignment:
- For single-narrator podcasts, use "narrator" as the speaker
- For interview format, use "host" and "guest"
- For co-host format, use "host_1" and "host_2"
- For narrative with characters, use "narrator" and "character"

## Guidelines:
- **PRESERVE CONTENT**: Use ALL the information from the transcript, don't over-summarize
- Rewrite for better flow and engagement, but preserve factual accuracy
- Build suspense - don't reveal everything immediately
- End each module with a "pull" that makes listeners want to continue
- The hook should pose a question or mystery that the episode answers
- Vary tension levels across modules (don't stay at one level)
- **WORD COUNT CHECK**: Hook ~{hook_words} words, each module ~{words_per_module} words, total ~{total_words} words
{conversational_section}
{feedback_section}

## Raw Transcript to Enhance:
{transcript}

Return ONLY valid JSON, no additional text."""


# Legacy prompt for backwards compatibility (uses 8-minute default)
ENHANCEMENT_PROMPT = build_enhancement_prompt(
    transcript="{transcript}",
    structure=calculate_script_structure(8),
    feedback="{feedback_section}"
)


class ScriptDesignerAgent(BaseAgent):
    """
    Agent for transforming raw transcripts into engaging podcast scripts.

    Features:
    - Automatic emotion mapping
    - Dynamic module structure based on target duration
    - Hook generation for immediate engagement
    - Metadata extraction for audio/visual design
    - Speaker assignment for multi-speaker formats
    """

    # Default duration if not specified
    DEFAULT_DURATION_MINUTES = 10

    def __init__(
        self,
        model: str = None,
        speaker_format: Optional[str] = None
    ):
        """
        Initialize the Script Designer Agent.

        Args:
            model: LLM model to use (default: opus from config)
            speaker_format: Speaker format hint (single, interview, co_hosts, narrator_characters)
        """
        if model is None:
            model = MODEL_OPTIONS["opus"]
        super().__init__(
            name="ScriptDesigner",
            output_category="",  # Root Output directory
            model=model
        )
        self.speaker_format = speaker_format or "single"

    def enhance(
        self,
        transcript: str,
        feedback: Optional[str] = None,
        target_duration_minutes: Optional[int] = None,
        conversational_style: bool = False
    ) -> Dict[str, Any]:
        """
        Enhance a raw transcript into a structured, engaging script.

        Args:
            transcript: Raw transcript text
            feedback: Optional feedback from director for revision
            target_duration_minutes: Target podcast duration (defaults to 10 minutes)
            conversational_style: Enable conversational style with cliffhangers,
                                  suspense, and dramatic reveals (co-hosts format)

        Returns:
            Enhanced script as dictionary with modules, emotions, and metadata
        """
        # Use default duration if not specified
        duration = target_duration_minutes or self.DEFAULT_DURATION_MINUTES

        # Calculate script structure based on duration
        structure = calculate_script_structure(duration)
        self.log(f"Target duration: {duration} min -> {structure['num_modules']} modules, {structure['total_words']} words")
        if conversational_style:
            self.log("Conversational style enabled: using co-hosts format with dramatic pacing")

        # Build the dynamic prompt
        prompt = build_enhancement_prompt(
            transcript=transcript,
            structure=structure,
            feedback=feedback,
            conversational_style=conversational_style
        )

        self.log("Enhancing transcript...")
        response_text = self.call_llm(prompt, max_tokens=8192)

        try:
            enhanced_script = self.parse_json_response(response_text)
            # Store target duration in script for downstream use
            enhanced_script["target_duration_minutes"] = duration
            enhanced_script["script_structure"] = structure
            enhanced_script["conversational_style"] = conversational_style
            self.log("Script enhancement complete")
            return enhanced_script
        except ValueError as e:
            self.log(f"Failed to parse enhanced script: {e}", level="error")
            return {
                "error": str(e),
                "raw_response": response_text
            }

    def process(
        self,
        transcript: str,
        feedback: Optional[str] = None,
        target_duration_minutes: Optional[int] = None,
        conversational_style: bool = False
    ) -> Dict[str, Any]:
        """
        Main processing method - alias for enhance().

        Args:
            transcript: Raw transcript text
            feedback: Optional feedback from director
            target_duration_minutes: Target podcast duration
            conversational_style: Enable conversational style

        Returns:
            Enhanced script dictionary
        """
        return self.enhance(transcript, feedback, target_duration_minutes, conversational_style)

    def save_enhanced_script(self, script: Dict[str, Any], filename: str = "enhanced_script") -> str:
        """
        Save the enhanced script to the output directory.

        Args:
            script: Enhanced script dictionary
            filename: Output filename (without extension)

        Returns:
            Path to saved file
        """
        output_path = self.save_json(script, filename)
        return str(output_path)


if __name__ == "__main__":
    # Test with sample transcript
    sample = """
    Welcome to Electronic Voices where we explore the lives and legacies of electronic music's key creators.
    Today, Bjork. On the fringe of Reykjavik, in a country where volcanoes met glaciers,
    a little girl with extraordinary vocal cords was growing up in a bohemian commune.
    """

    agent = ScriptDesignerAgent()
    result = agent.enhance(sample)

    import json
    print(json.dumps(result, indent=2))
