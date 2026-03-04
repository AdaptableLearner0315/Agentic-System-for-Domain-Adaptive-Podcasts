"""
Smart Input Handler
Author: Sarath

Intelligently routes inputs based on what user provides (prompt, files, or both).

Supports three input modes:
1. Generation Mode: Prompt only → generate content from scratch
2. Enhancement Mode: Files only → extract and enhance (existing behavior)
3. Hybrid Mode: Prompt + files → generate content informed by reference files

The handler produces an ExtractedContent object that can be passed unchanged
to the downstream pipeline (ScriptDesignerAgent → Director → TTS → BGM → Video).

Duration Handling:
- Extracts duration from prompt (e.g., "5 minute podcast about AI")
- Can accept explicit target_duration_minutes parameter
- Defaults to 10 minutes if not specified
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from pathlib import Path

from utils.input_router import InputRouter, ExtractedContent
from utils.duration_parser import (
    extract_duration_minutes,
    remove_duration_from_prompt,
    get_default_duration,
)


@dataclass
class SmartInput:
    """
    Container for smart input parameters.

    Attributes:
        prompt: Natural language prompt/topic (triggers generation mode)
        files: List of file paths (PDF, audio, video, text, URL)
        guidance: Style/focus guidance for generation or enhancement
        target_duration_minutes: Explicit target duration (overrides prompt extraction)
    """
    prompt: Optional[str] = None
    files: List[str] = field(default_factory=list)
    guidance: Optional[str] = None
    target_duration_minutes: Optional[int] = None

    # For backward compatibility with --input flag
    @classmethod
    def from_legacy_input(cls, input_path: str, prompt: Optional[str] = None) -> "SmartInput":
        """
        Create SmartInput from legacy --input argument.

        Args:
            input_path: Single input file path
            prompt: Optional prompt (used as guidance)

        Returns:
            SmartInput with file in files list
        """
        return cls(
            prompt=None,  # No generation, just enhancement
            files=[input_path] if input_path else [],
            guidance=prompt,  # Use prompt as guidance for enhancement
        )


class SmartInputHandler:
    """
    Intelligently routes inputs to appropriate processing mode.

    Modes:
    1. GENERATION MODE (prompt only):
       - Uses ContentGeneratorAgent to generate content from scratch
       - Good for: "Create a podcast about X"

    2. ENHANCEMENT MODE (files only):
       - Uses InputRouter to extract content from files (existing behavior)
       - Good for: Processing existing transcripts, PDFs, audio files

    3. HYBRID MODE (prompt + files):
       - Extracts content from files as reference material
       - Uses ContentGeneratorAgent to generate content informed by files
       - Good for: "Create a podcast about X using this research paper as reference"
    """

    def __init__(self):
        """Initialize the SmartInputHandler."""
        self.input_router = InputRouter()
        self._content_generator = None

    @property
    def content_generator(self):
        """Lazy-load the ContentGeneratorAgent."""
        if self._content_generator is None:
            from agents.content_generator_agent import ContentGeneratorAgent
            self._content_generator = ContentGeneratorAgent()
        return self._content_generator

    def detect_mode(self, smart_input: SmartInput) -> str:
        """
        Detect the appropriate processing mode based on inputs.

        Args:
            smart_input: SmartInput container

        Returns:
            Mode string: "generation", "enhancement", or "hybrid"
        """
        has_prompt = bool(smart_input.prompt and smart_input.prompt.strip())
        has_files = bool(smart_input.files)

        if has_prompt and not has_files:
            return "generation"
        elif has_files and not has_prompt:
            return "enhancement"
        elif has_prompt and has_files:
            return "hybrid"
        else:
            raise ValueError("Must provide either --prompt or --files/--input")

    def process(
        self,
        smart_input: SmartInput,
        length: str = "standard",
        target_duration_minutes: Optional[int] = None
    ) -> ExtractedContent:
        """
        Process inputs and return unified ExtractedContent.

        The returned ExtractedContent can be passed directly to the pipeline,
        regardless of which mode was used.

        Duration Resolution Priority:
        1. Explicit target_duration_minutes parameter
        2. smart_input.target_duration_minutes
        3. Duration extracted from prompt
        4. Default (10 minutes)

        Args:
            smart_input: SmartInput container with prompt/files/guidance
            length: Target length for generation ("short", "standard", "long")
                    Ignored if duration is specified.
            target_duration_minutes: Override duration (highest priority)

        Returns:
            ExtractedContent object (same format as InputRouter.extract())
        """
        mode = self.detect_mode(smart_input)
        print(f"[SmartInputHandler] Detected mode: {mode.upper()}")

        # Resolve duration with priority chain
        duration = self._resolve_duration(
            explicit_duration=target_duration_minutes,
            input_duration=smart_input.target_duration_minutes,
            prompt=smart_input.prompt
        )

        # Clean prompt (remove duration specification if extracted from it)
        clean_prompt = smart_input.prompt
        if smart_input.prompt and not target_duration_minutes and not smart_input.target_duration_minutes:
            extracted = extract_duration_minutes(smart_input.prompt)
            if extracted:
                clean_prompt = remove_duration_from_prompt(smart_input.prompt)
                print(f"[SmartInputHandler] Cleaned prompt: '{clean_prompt[:50]}...'")

        print(f"[SmartInputHandler] Target duration: {duration} minutes")

        if mode == "generation":
            return self._generate_content(
                topic=clean_prompt,
                guidance=smart_input.guidance,
                length=length,
                target_duration_minutes=duration,
            )

        elif mode == "enhancement":
            content = self._extract_and_combine(
                files=smart_input.files,
                guidance=smart_input.guidance,
            )
            # Store duration in metadata for downstream use
            content.metadata["target_duration_minutes"] = duration
            return content

        elif mode == "hybrid":
            # Extract file content as reference
            file_content = self._extract_and_combine(
                files=smart_input.files,
                guidance=None,  # Don't apply guidance to extraction
            )
            # Generate content informed by files
            return self._generate_with_context(
                topic=clean_prompt,
                reference_content=file_content.text,
                guidance=smart_input.guidance,
                length=length,
                target_duration_minutes=duration,
            )

        else:
            raise ValueError(f"Unknown mode: {mode}")

    def _resolve_duration(
        self,
        explicit_duration: Optional[int],
        input_duration: Optional[int],
        prompt: Optional[str]
    ) -> int:
        """
        Resolve target duration with priority chain.

        Args:
            explicit_duration: Duration passed directly to process()
            input_duration: Duration from SmartInput
            prompt: Prompt text to extract duration from

        Returns:
            Resolved duration in minutes
        """
        # Priority 1: Explicit parameter
        if explicit_duration is not None:
            return explicit_duration

        # Priority 2: SmartInput duration
        if input_duration is not None:
            return input_duration

        # Priority 3: Extract from prompt
        if prompt:
            extracted = extract_duration_minutes(prompt)
            if extracted:
                print(f"[SmartInputHandler] Extracted duration from prompt: {extracted} minutes")
                return extracted

        # Priority 4: Default
        return get_default_duration()

    async def process_async(
        self,
        smart_input: SmartInput,
        length: str = "standard",
        target_duration_minutes: Optional[int] = None
    ) -> ExtractedContent:
        """
        Async version of process for pipeline integration.

        Args:
            smart_input: SmartInput container
            length: Target length for generation
            target_duration_minutes: Override duration

        Returns:
            ExtractedContent object
        """
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.process(smart_input, length, target_duration_minutes)
        )

    def _generate_content(
        self,
        topic: str,
        guidance: Optional[str] = None,
        length: str = "standard",
        target_duration_minutes: Optional[int] = None,
    ) -> ExtractedContent:
        """
        Generate content from topic only (pure generation mode).

        Args:
            topic: Topic/prompt for generation
            guidance: Optional style/focus guidance
            length: Target length (ignored if target_duration_minutes is set)
            target_duration_minutes: Target podcast duration in minutes

        Returns:
            ExtractedContent with generated text
        """
        print(f"[SmartInputHandler] Generating content for: {topic[:50]}...")

        transcript = self.content_generator.generate(
            topic=topic,
            guidance=guidance,
            length=length,
            target_duration_minutes=target_duration_minutes,
        )

        return ExtractedContent(
            text=transcript,
            source_type="generated",
            source_path=f"prompt:{topic[:50]}",
            title=topic[:100] if len(topic) < 100 else f"{topic[:97]}...",
            metadata={
                "generation_mode": "pure",
                "prompt": topic,
                "guidance": guidance,
                "length": length,
                "target_duration_minutes": target_duration_minutes,
            },
            user_prompt=guidance,
        )

    def _extract_and_combine(
        self,
        files: List[str],
        guidance: Optional[str] = None,
    ) -> ExtractedContent:
        """
        Extract content from files and combine (enhancement mode).

        Args:
            files: List of file paths
            guidance: Optional guidance (stored but not applied to extraction)

        Returns:
            ExtractedContent with combined text from all files
        """
        if not files:
            raise ValueError("No files provided for enhancement mode")

        print(f"[SmartInputHandler] Extracting content from {len(files)} file(s)...")

        if len(files) == 1:
            # Single file - use InputRouter directly
            content = self.input_router.extract(files[0], guidance)
            return content

        # Multiple files - extract and combine
        all_texts = []
        source_types = []
        titles = []

        for file_path in files:
            print(f"  Extracting: {Path(file_path).name}")
            content = self.input_router.extract(file_path)
            all_texts.append(content.text)
            source_types.append(content.source_type)
            if content.title:
                titles.append(content.title)

        # Combine texts with clear separators
        combined_text = "\n\n---\n\n".join(all_texts)

        return ExtractedContent(
            text=combined_text,
            source_type=f"combined:{'+'.join(set(source_types))}",
            source_path=", ".join(files),
            title=" | ".join(titles) if titles else None,
            metadata={
                "file_count": len(files),
                "source_types": source_types,
                "files": files,
            },
            user_prompt=guidance,
        )

    def _generate_with_context(
        self,
        topic: str,
        reference_content: str,
        guidance: Optional[str] = None,
        length: str = "standard",
        target_duration_minutes: Optional[int] = None,
    ) -> ExtractedContent:
        """
        Generate content informed by reference material (hybrid mode).

        Args:
            topic: Topic/prompt for generation
            reference_content: Content from reference files
            guidance: Optional style/focus guidance
            length: Target length (ignored if target_duration_minutes is set)
            target_duration_minutes: Target podcast duration in minutes

        Returns:
            ExtractedContent with generated text
        """
        print(f"[SmartInputHandler] Generating content with reference context...")
        print(f"  Topic: {topic[:50]}...")
        print(f"  Reference length: {len(reference_content)} characters")

        transcript = self.content_generator.generate(
            topic=topic,
            reference_content=reference_content,
            guidance=guidance,
            length=length,
            target_duration_minutes=target_duration_minutes,
        )

        return ExtractedContent(
            text=transcript,
            source_type="generated:hybrid",
            source_path=f"prompt:{topic[:50]}",
            title=topic[:100] if len(topic) < 100 else f"{topic[:97]}...",
            metadata={
                "generation_mode": "hybrid",
                "prompt": topic,
                "guidance": guidance,
                "length": length,
                "target_duration_minutes": target_duration_minutes,
                "reference_length": len(reference_content),
            },
            user_prompt=guidance,
        )


def process_smart_input(
    prompt: Optional[str] = None,
    files: Optional[List[str]] = None,
    guidance: Optional[str] = None,
    length: str = "standard",
    target_duration_minutes: Optional[int] = None,
) -> ExtractedContent:
    """
    Convenience function to process smart input.

    Args:
        prompt: Topic/prompt for generation
        files: List of input files
        guidance: Style/focus guidance
        length: Target length ("short", "standard", "long")
        target_duration_minutes: Target podcast duration in minutes

    Returns:
        ExtractedContent object
    """
    handler = SmartInputHandler()
    smart_input = SmartInput(
        prompt=prompt,
        files=files or [],
        guidance=guidance,
        target_duration_minutes=target_duration_minutes,
    )
    return handler.process(smart_input, length, target_duration_minutes)


__all__ = [
    'SmartInput',
    'SmartInputHandler',
    'process_smart_input',
]
