"""
Script Enhancer Agent

Transforms raw podcast transcripts into engaging, structured content with:
- Emotion mapping for each segment
- 4-5 module structure with roller-coaster emotional arc
- Compelling 30-second opening hook
- Keywords, visual cues, and audio cues for each chunk
"""

import json
from anthropic import Anthropic

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
    "duration_estimate_seconds": 30
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
          "audio_cues": ["audio description 1"]
        }}
      ]
    }}
  ]
}}
```

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


class ScriptEnhancer:
    def __init__(self, model: str = "claude-sonnet-4-5-20250514"):
        self.client = Anthropic()
        self.model = model

    def enhance(self, transcript: str, feedback: str = None) -> dict:
        """
        Enhance a raw transcript into a structured, engaging script.

        Args:
            transcript: Raw transcript text
            feedback: Optional feedback from director for revision

        Returns:
            Enhanced script as dictionary
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

        response = self.client.messages.create(
            model=self.model,
            max_tokens=8192,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        # Extract JSON from response
        response_text = response.content[0].text

        # Try to parse JSON, handling potential markdown code blocks
        try:
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                json_str = response_text.split("```")[1].split("```")[0]
            else:
                json_str = response_text

            return json.loads(json_str.strip())
        except json.JSONDecodeError as e:
            # Return raw response if JSON parsing fails
            return {
                "error": f"JSON parsing failed: {e}",
                "raw_response": response_text
            }


if __name__ == "__main__":
    # Test with sample transcript
    sample = """
    Welcome to Electronic Voices where we explore the lives and legacies of electronic music's key creators.
    Today, Björk. On the fringe of Reykjavik, in a country where volcanoes met glaciers,
    a little girl with extraordinary vocal cords was growing up in a bohemian commune.
    """

    enhancer = ScriptEnhancer()
    result = enhancer.enhance(sample)
    print(json.dumps(result, indent=2))
