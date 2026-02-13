"""
Director Agent
Author: Sarath

Reviews enhanced scripts and provides feedback or approval.
Acts as quality control to ensure the script meets engagement standards.

Features:
- Script quality evaluation against strict criteria
- Approval/rejection with detailed feedback
- Can orchestrate other agents in a review loop
"""

from typing import Dict, Any, Optional, List
from agents.base_agent import BaseAgent


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


class DirectorAgent(BaseAgent):
    """
    Agent for reviewing and approving enhanced scripts.

    Features:
    - Quality evaluation against engagement criteria
    - Approval/rejection with actionable feedback
    - Orchestration capabilities for review loops
    """

    def __init__(self, model: str = "claude-opus-4-5-20250514"):
        """
        Initialize the Director Agent.

        Args:
            model: LLM model to use (default: claude-opus-4-5-20250514)
        """
        super().__init__(
            name="Director",
            output_category="",  # Root Output directory
            model=model
        )

    def review(self, enhanced_script: Dict[str, Any]) -> Dict[str, Any]:
        """
        Review an enhanced script and provide feedback or approval.

        Args:
            enhanced_script: The enhanced script dictionary

        Returns:
            Review result with approval status and feedback
        """
        import json
        prompt = REVIEW_PROMPT.format(
            script=json.dumps(enhanced_script, indent=2)
        )

        self.log("Reviewing script...")
        response_text = self.call_llm(prompt, max_tokens=4096)

        try:
            review_result = self.parse_json_response(response_text)
            status = "APPROVED" if review_result.get("approved") else "NEEDS REVISION"
            self.log(f"Review complete: {status} (score: {review_result.get('score', 'N/A')})")
            return review_result
        except ValueError as e:
            self.log(f"Failed to parse review: {e}", level="error")
            # If parsing fails, be conservative and request revision
            return {
                "approved": False,
                "score": 0,
                "feedback": f"Review parsing failed: {e}. Please revise the script structure.",
                "raw_response": response_text
            }

    def process(self, enhanced_script: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main processing method - alias for review().

        Args:
            enhanced_script: The enhanced script dictionary

        Returns:
            Review result dictionary
        """
        return self.review(enhanced_script)

    def orchestrate_enhancement(
        self,
        script_designer: 'ScriptDesignerAgent',
        transcript: str,
        max_rounds: int = 3
    ) -> Dict[str, Any]:
        """
        Orchestrate the script enhancement process with review loop.

        Coordinates with ScriptDesignerAgent to iteratively improve
        the script until it meets quality standards.

        Args:
            script_designer: ScriptDesignerAgent instance
            transcript: Raw transcript to enhance
            max_rounds: Maximum number of revision rounds

        Returns:
            Final enhanced script with review history
        """
        self.log(f"Starting enhancement orchestration (max {max_rounds} rounds)")

        review_history = []
        current_script = None
        feedback = None

        for round_num in range(1, max_rounds + 1):
            self.log(f"=== Round {round_num}/{max_rounds} ===")

            # Generate/revise script
            current_script = script_designer.enhance(transcript, feedback)

            if "error" in current_script:
                self.log(f"Script generation failed: {current_script['error']}", level="error")
                break

            # Review the script
            review_result = self.review(current_script)
            review_history.append({
                "round": round_num,
                "review": review_result
            })

            if review_result.get("approved", False):
                self.log(f"Script APPROVED in round {round_num}")
                break

            # Extract feedback for next round
            feedback = review_result.get("feedback", "Please improve the overall quality.")
            self.log(f"Round {round_num} feedback: {feedback[:100]}...")

        # Add review history to final script
        if current_script and "error" not in current_script:
            current_script["review_history"] = review_history
            current_script["final_status"] = {
                "approved": review_history[-1]["review"].get("approved", False) if review_history else False,
                "total_rounds": len(review_history),
                "final_score": review_history[-1]["review"].get("score", 0) if review_history else 0
            }

        return current_script

    def coordinate_agents(
        self,
        agents: Dict[str, BaseAgent],
        task: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Coordinate multiple agents for a complex task.

        This method enables the Director to act as an orchestrator,
        delegating work to specialized agents.

        Args:
            agents: Dictionary of agent name -> agent instance
            task: Task description
            context: Context dictionary with input data

        Returns:
            Combined results from all agents
        """
        self.log(f"Coordinating {len(agents)} agents for task: {task}")
        results = {}

        for agent_name, agent in agents.items():
            self.log(f"Delegating to {agent_name}...")
            try:
                result = agent.process(**context)
                results[agent_name] = {
                    "status": "success",
                    "result": result
                }
            except Exception as e:
                self.log(f"{agent_name} failed: {e}", level="error")
                results[agent_name] = {
                    "status": "error",
                    "error": str(e)
                }

        return results


if __name__ == "__main__":
    import json

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

    director = DirectorAgent()
    result = director.review(sample_script)
    print(json.dumps(result, indent=2))
