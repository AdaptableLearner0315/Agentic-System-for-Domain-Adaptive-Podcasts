"""
Director Agent

Reviews enhanced scripts and provides feedback or approval.
Acts as quality control to ensure the script meets engagement standards.
"""

import json
from anthropic import Anthropic

REVIEW_PROMPT = """You are a demanding podcast director reviewing an enhanced script. Your job is to evaluate the script against strict quality criteria and either APPROVE it or provide specific FEEDBACK for improvement.

## Review Criteria:

1. **Hook Quality** (Critical)
   - Does it immediately grab attention in the first sentence?
   - Does it create intrigue, mystery, or emotional connection?
   - Is it approximately 30 seconds when read aloud (75-100 words)?
   - Does it pose a question or mystery that makes listeners want to continue?

2. **Emotional Arc** (Critical)
   - Do the modules create a "roller-coaster" emotional experience?
   - Is there variety in tension levels (not flat)?
   - Are tension peaks and valleys strategically placed?
   - Does each module have a distinct emotional identity?

3. **Story Flow** (Important)
   - Is the narrative coherent and easy to follow?
   - Do transitions between modules feel natural?
   - Does each module end with a "pull" to continue?
   - Is chronology used strategically (not just linearly)?

4. **Metadata Quality** (Important)
   - Are keywords specific and evocative (not generic)?
   - Are visual cues cinematic and imaginable?
   - Are audio cues appropriate and varied?
   - Do cues enhance the emotional impact?

5. **Module Structure** (Important)
   - Are there 4-5 well-defined modules?
   - Does each module have a clear title that hints at content?
   - Is content appropriately distributed across modules?

## Your Response Format (JSON):
```json
{{
  "approved": true/false,
  "score": 1-10,
  "evaluation": {{
    "hook_quality": {{"score": 1-10, "notes": "..."}},
    "emotional_arc": {{"score": 1-10, "notes": "..."}},
    "story_flow": {{"score": 1-10, "notes": "..."}},
    "metadata_quality": {{"score": 1-10, "notes": "..."}},
    "module_structure": {{"score": 1-10, "notes": "..."}}
  }},
  "feedback": "Specific, actionable feedback if not approved. Be detailed about what needs to change."
}}
```

## Approval Threshold:
- APPROVE if overall score >= 7 AND no critical criteria (hook, emotional arc) score below 6
- Otherwise, provide detailed feedback

## Script to Review:
{script}

Return ONLY valid JSON, no additional text."""


class Director:
    def __init__(self, model: str = "claude-sonnet-4-5-20250514"):
        self.client = Anthropic()
        self.model = model

    def review(self, enhanced_script: dict) -> dict:
        """
        Review an enhanced script and provide feedback or approval.

        Args:
            enhanced_script: The enhanced script dictionary

        Returns:
            Review result with approval status and feedback
        """
        prompt = REVIEW_PROMPT.format(
            script=json.dumps(enhanced_script, indent=2)
        )

        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        response_text = response.content[0].text

        # Parse JSON response
        try:
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                json_str = response_text.split("```")[1].split("```")[0]
            else:
                json_str = response_text

            return json.loads(json_str.strip())
        except json.JSONDecodeError as e:
            # If parsing fails, be conservative and request revision
            return {
                "approved": False,
                "score": 0,
                "feedback": f"Review parsing failed: {e}. Please revise the script structure.",
                "raw_response": response_text
            }


if __name__ == "__main__":
    # Test with sample enhanced script
    sample_script = {
        "title": "Test Episode",
        "hook": {
            "text": "What if everything you knew about music was wrong?",
            "emotion": "intrigue",
            "duration_estimate_seconds": 5
        },
        "modules": []
    }

    director = Director()
    result = director.review(sample_script)
    print(json.dumps(result, indent=2))
