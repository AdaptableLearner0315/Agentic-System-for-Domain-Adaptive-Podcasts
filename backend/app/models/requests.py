"""
Pydantic request models for the Nell API.

These models define the structure of incoming API requests,
with validation rules and documentation.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator


class GenerationRequest(BaseModel):
    """
    Request to start a podcast generation job.

    Supports three input modes:
    1. Generation: prompt only -> generate original content
    2. Enhancement: file_ids only -> enhance existing content
    3. Hybrid: prompt + file_ids -> generate with reference content

    Attributes:
        prompt: Topic or prompt for content generation
        file_ids: List of uploaded file IDs to use as input
        guidance: Additional instructions for generation
        mode: Pipeline mode (normal or pro)
        target_duration_minutes: Target podcast duration in minutes (1-30)
        config: Pro mode configuration overrides
    """
    prompt: Optional[str] = Field(
        None,
        description="Topic or prompt for content generation",
        example="The history of electronic music"
    )
    file_ids: Optional[List[str]] = Field(
        None,
        description="List of uploaded file IDs to use as input"
    )
    guidance: Optional[str] = Field(
        None,
        description="Additional instructions for generation style",
        example="Make it engaging for beginners"
    )
    mode: str = Field(
        "normal",
        description="Pipeline mode: 'normal' (fast), 'pro' (balanced), or 'ultra' (premium)"
    )
    target_duration_minutes: Optional[int] = Field(
        None,
        ge=1,
        le=30,
        description="Target podcast duration in minutes. If not specified, extracted from prompt or defaults to 10."
    )
    conversational_style: bool = Field(
        False,
        description="Enable conversational style with cliffhangers, suspense, and dramatic reveals (for co-hosts format)"
    )
    config: Optional[Dict[str, Any]] = Field(
        None,
        description="Pro mode configuration overrides"
    )

    @validator("mode")
    def validate_mode(cls, v: str) -> str:
        """Validate that mode is 'normal', 'pro', or 'ultra'."""
        if v.lower() not in ("normal", "pro", "ultra"):
            raise ValueError("mode must be 'normal', 'pro', or 'ultra'")
        return v.lower()

    @validator("prompt", "file_ids")
    def validate_has_input(cls, v, values):
        """Ensure at least prompt or file_ids is provided."""
        # This is checked at the route level for better error messages
        return v

    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "examples": [
                {
                    "prompt": "The history of electronic music",
                    "mode": "normal"
                },
                {
                    "file_ids": ["abc123"],
                    "mode": "pro",
                    "config": {"director_review": True}
                },
                {
                    "prompt": "Key insights from this research",
                    "file_ids": ["def456"],
                    "guidance": "For a general audience",
                    "mode": "pro"
                }
            ]
        }


class ProConfigRequest(BaseModel):
    """
    Pro mode configuration options.

    All fields are optional - only include fields you want to override
    from the defaults.

    Attributes:
        director_review: Enable Director agent review loop
        max_review_rounds: Maximum review iterations
        approval_threshold: Minimum score for approval
        voice_preset: Voice preset name
        apply_voice_styles: Enable module-specific voice styles
        music_genre: Background music genre
        bgm_segments: Number of BGM segments
        daisy_chain: Enable daisy-chain BGM conditioning
        image_count: Number of images to generate
        image_style: Image generation style
        speaker_format: Multi-speaker format
        emotion_voice_sync: Sync voice to emotions
        emotion_image_alignment: Align images to emotions
    """
    director_review: Optional[bool] = None
    max_review_rounds: Optional[int] = Field(None, ge=1, le=5)
    approval_threshold: Optional[int] = Field(None, ge=1, le=10)
    voice_preset: Optional[str] = None
    apply_voice_styles: Optional[bool] = None
    custom_pronunciations: Optional[Dict[str, str]] = None
    music_genre: Optional[str] = None
    bgm_segments: Optional[int] = Field(None, ge=1, le=9)
    daisy_chain: Optional[bool] = None
    image_count: Optional[int] = Field(None, ge=1, le=20)
    image_style: Optional[str] = None
    speaker_format: Optional[str] = None
    manual_speakers: Optional[Dict[str, str]] = None
    emotion_voice_sync: Optional[bool] = None
    emotion_image_alignment: Optional[bool] = None
    emotion_validation: Optional[bool] = None


class FileUploadMetadata(BaseModel):
    """
    Metadata for a file upload.

    Attributes:
        filename: Original filename
        content_type: MIME type of the file
        description: Optional description
    """
    filename: str = Field(..., description="Original filename")
    content_type: Optional[str] = Field(None, description="MIME type")
    description: Optional[str] = Field(None, description="Optional description")


class URLExtractionRequest(BaseModel):
    """
    Request to extract content from a URL.

    Attributes:
        url: Web URL to extract content from
        description: Optional description for the extracted content
    """
    url: str = Field(..., description="Web URL to extract content from")
    description: Optional[str] = Field(None, description="Optional description")

    @validator("url")
    def validate_url(cls, v: str) -> str:
        """Validate URL format."""
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return v


class ConfigUpdateRequest(BaseModel):
    """
    Request to update user configuration.

    Attributes:
        default_mode: Default pipeline mode
        default_voice: Default voice preset
        save_history: Whether to save generation history
    """
    default_mode: Optional[str] = None
    default_voice: Optional[str] = None
    save_history: Optional[bool] = None
    custom_settings: Optional[Dict[str, Any]] = None
