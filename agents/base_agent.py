"""
Base Agent Class
Author: Sarath

Abstract base class for all agents in the podcast enhancement system.
Provides common functionality for LLM interaction, JSON parsing, and output management.
"""

import json
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Dict, Any
from anthropic import Anthropic, APITimeoutError, APIStatusError


class BaseAgent(ABC):
    """
    Abstract base class for podcast enhancement agents.

    Provides:
    - Anthropic client initialization
    - JSON response parsing with error handling
    - Output directory management
    - Common logging utilities
    """

    def __init__(
        self,
        name: str,
        output_category: str = "general",
        model: str = "claude-opus-4-5-20250514"
    ):
        """
        Initialize the base agent.

        Args:
            name: Agent name for logging
            output_category: Output subdirectory (e.g., "audio", "visuals", "scripts")
            model: LLM model to use (default: claude-opus-4-5-20250514)
        """
        self.name = name
        self.model = model
        self.client = Anthropic(timeout=120.0)

        # Set up output directory
        base_output = Path(__file__).parent.parent / "Output"
        if output_category:
            self.output_dir = base_output / output_category
        else:
            self.output_dir = base_output
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def log(self, message: str, level: str = "info"):
        """
        Log a message with agent context.

        Args:
            message: Message to log
            level: Log level (info, warning, error)
        """
        prefix = f"[{self.name}]"
        if level == "warning":
            print(f"{prefix} WARNING: {message}")
        elif level == "error":
            print(f"{prefix} ERROR: {message}")
        else:
            print(f"{prefix} {message}")

    def call_llm(
        self,
        prompt: str,
        max_tokens: int = 4096,
        system_prompt: Optional[str] = None,
        max_retries: int = 2
    ) -> str:
        """
        Call the LLM with the given prompt.

        Retries up to max_retries times with exponential backoff on
        timeout, rate limit (429), and server errors (500/503).

        Args:
            prompt: User prompt
            max_tokens: Maximum tokens in response
            system_prompt: Optional system prompt
            max_retries: Number of retry attempts (default 2)

        Returns:
            Raw response text from LLM
        """
        messages = [{"role": "user", "content": prompt}]

        kwargs = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": messages
        }

        if system_prompt:
            kwargs["system"] = system_prompt

        last_error = None
        for attempt in range(max_retries + 1):
            try:
                response = self.client.messages.create(**kwargs)
                return response.content[0].text
            except APITimeoutError as e:
                last_error = e
                if attempt < max_retries:
                    delay = 2 ** attempt
                    self.log(f"Timeout, retrying in {delay}s (attempt {attempt + 1}/{max_retries})", level="warning")
                    time.sleep(delay)
            except APIStatusError as e:
                last_error = e
                if e.status_code in (429, 500, 503) and attempt < max_retries:
                    delay = 2 ** (attempt + 1)
                    self.log(f"API error {e.status_code}, retrying in {delay}s (attempt {attempt + 1}/{max_retries})", level="warning")
                    time.sleep(delay)
                else:
                    raise

        raise last_error

    def parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse JSON from LLM response, handling markdown code blocks.

        Args:
            response_text: Raw response text from LLM

        Returns:
            Parsed JSON as dictionary

        Raises:
            ValueError: If JSON parsing fails
        """
        try:
            # Try to extract JSON from markdown code blocks
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                json_str = response_text.split("```")[1].split("```")[0]
            else:
                json_str = response_text

            return json.loads(json_str.strip())
        except json.JSONDecodeError as e:
            self.log(f"JSON parsing failed: {e}", level="error")
            raise ValueError(f"Failed to parse JSON response: {e}")

    def save_json(self, data: Dict[str, Any], filename: str) -> Path:
        """
        Save data as JSON file in output directory.

        Args:
            data: Dictionary to save
            filename: Output filename (without .json extension)

        Returns:
            Path to saved file
        """
        output_path = self.output_dir / f"{filename}.json"
        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)
        self.log(f"Saved: {output_path}")
        return output_path

    def load_json(self, filename: str) -> Optional[Dict[str, Any]]:
        """
        Load JSON file from output directory.

        Args:
            filename: Filename to load (with or without .json extension)

        Returns:
            Loaded dictionary or None if file not found
        """
        if not filename.endswith(".json"):
            filename = f"{filename}.json"

        filepath = self.output_dir / filename
        if not filepath.exists():
            self.log(f"File not found: {filepath}", level="warning")
            return None

        with open(filepath, "r") as f:
            return json.load(f)

    @abstractmethod
    def process(self, *args, **kwargs) -> Any:
        """
        Main processing method to be implemented by subclasses.

        This is the primary entry point for agent functionality.
        """
        pass
