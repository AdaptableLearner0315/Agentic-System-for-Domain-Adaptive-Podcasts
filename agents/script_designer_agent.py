"""
Script Designer Agent
Author: Sarath

Transforms raw podcast transcripts into engaging, structured content with:
- Emotion mapping for each segment
- 4-5 module structure with roller-coaster emotional arc
- Compelling 30-second opening hook
- Keywords, visual cues, and audio cues for each chunk

Inherits from BaseAgent for common LLM and output functionality.
"""

from typing import Dict, Any, Optional
from agents.base_agent import BaseAgent


ENHANCEMENT_PROMPT = """You are an expert podcast script enhancer. Your job is to transform a raw transcript into an engaging, emotionally compelling podcast script.

## CRITICAL DURATION REQUIREMENTS:
- **Total script duration target: 8-9 minutes** (approximately 1400-1600 words total)
- **Hook: 30-45 seconds** (100-150 words)
- **Each Module: 2-2.5 minutes** (300-375 words per module)
- **4 Modules total** (not 5)
- **Each module should have 3-4 chunks** for varied pacing

## Your Tasks:

1. **Create a Hook (30-45 seconds / 100-150 words)**: Write a compelling opening that immediately captures attention. This should create intrigue, mystery, or emotional connection. Make it substantial enough to set the scene.

2. **Structure into EXACTLY 4 Modules (2-2.5 minutes each / 300-375 words each)**: Divide the content into distinct emotional modules that create a "roller-coaster" experience:
   - Each module should have a clear emotional identity
   - Each module MUST have 3-4 chunks (not just 2)
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
{{
  "title": "Episode title",
  "hook": {{
    "text": "The compelling opening text...",
    "emotion": "intrigue",
    "duration_estimate_seconds": 30,
    "speaker": "narrator",
    "visual_cues": ["visual description for hook"]
  }},
  "modules": [
    {{
      "id": 1,
      "title": "Module Title",
      "emotion_arc": "curiosity -> wonder",
      "chunks": [
        {{
          "text": "The actual content text...",
          "emotion": "wonder",
          "tension_level": 3,
          "keywords": ["keyword1", "keyword2"],
          "visual_cues": ["visual description 1"],
          "audio_cues": ["audio description 1"],
          "speaker": "narrator"
        }}
      ]
    }}
  ]
}}
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
- **WORD COUNT CHECK**: Hook ~100-150 words, each module ~300-375 words, total ~1400-1600 words

{feedback_section}

## Raw Transcript to Enhance:
{transcript}

Return ONLY valid JSON, no additional text."""


class ScriptDesignerAgent(BaseAgent):
    """
    Agent for transforming raw transcripts into engaging podcast scripts.

    Features:
    - Automatic emotion mapping
    - Module structure with roller-coaster pacing
    - Hook generation for immediate engagement
    - Metadata extraction for audio/visual design
    - Speaker assignment for multi-speaker formats
    """

    def __init__(
        self,
        model: str = "claude-opus-4-5-20250514",
        speaker_format: Optional[str] = None
    ):
        """
        Initialize the Script Designer Agent.

        Args:
            model: LLM model to use (default: claude-opus-4-5-20250514)
            speaker_format: Speaker format hint (single, interview, co_hosts, narrator_characters)
        """
        super().__init__(
            name="ScriptDesigner",
            output_category="",  # Root Output directory
            model=model
        )
        self.speaker_format = speaker_format or "single"

    def enhance(self, transcript: str, feedback: Optional[str] = None) -> Dict[str, Any]:
        """
        Enhance a raw transcript into a structured, engaging script.

        Args:
            transcript: Raw transcript text
            feedback: Optional feedback from director for revision

        Returns:
            Enhanced script as dictionary with modules, emotions, and metadata
        """
        feedback_section = ""
        if feedback:
            feedback_section = f"""
## Director Feedback (Address these issues):
{feedback}

Please revise the script to address the feedback above while maintaining engagement.
"""

        prompt = ENHANCEMENT_PROMPT.format(
            transcript=transcript,
            feedback_section=feedback_section
        )

        self.log("Enhancing transcript...")
        response_text = self.call_llm(prompt, max_tokens=8192)

        try:
            enhanced_script = self.parse_json_response(response_text)
            self.log("Script enhancement complete")
            return enhanced_script
        except ValueError as e:
            self.log(f"Failed to parse enhanced script: {e}", level="error")
            return {
                "error": str(e),
                "raw_response": response_text
            }

    def process(self, transcript: str, feedback: Optional[str] = None) -> Dict[str, Any]:
        """
        Main processing method - alias for enhance().

        Args:
            transcript: Raw transcript text
            feedback: Optional feedback from director

        Returns:
            Enhanced script dictionary
        """
        return self.enhance(transcript, feedback)

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
