"""
Shared enums for the Nell API.

These enums define the possible states and modes used throughout the system,
ensuring consistency between the API, services, and frontend.
"""

from enum import Enum


class JobStatus(str, Enum):
    """
    Status of a generation job.

    The job lifecycle follows: PENDING -> RUNNING -> (COMPLETED | FAILED | CANCELLED)

    Attributes:
        PENDING: Job is queued but not yet started
        RUNNING: Job is currently being processed
        COMPLETED: Job finished successfully
        FAILED: Job encountered an error
        CANCELLED: Job was cancelled by user
    """
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PipelineMode(str, Enum):
    """
    Pipeline execution mode.

    Attributes:
        NORMAL: Fast generation (~2 minutes), suitable for quick previews
        PRO: High-quality generation (~6 minutes), full features enabled
    """
    NORMAL = "normal"
    PRO = "pro"


class GenerationPhase(str, Enum):
    """
    Current phase of the generation process.

    Normal mode phases execute in order:
        INITIALIZING -> ANALYZING -> SCRIPTING -> GENERATING_ASSETS ->
        MIXING_AUDIO -> ASSEMBLING_VIDEO -> COMPLETE

    Pro mode phases execute in order:
        INITIALIZING -> ANALYZING -> SCRIPTING ->
        GENERATING_TTS -> GENERATING_BGM -> GENERATING_IMAGES ->
        MIXING_AUDIO -> ASSEMBLING_VIDEO -> COMPLETE

    ERROR can occur at any point and terminates the job.

    Attributes:
        INITIALIZING: Setting up the pipeline
        ANALYZING: Analyzing input content
        SCRIPTING: Enhancing script with emotional arcs
        GENERATING_TTS: Creating text-to-speech audio (Pro mode)
        GENERATING_BGM: Creating background music (Pro mode)
        GENERATING_IMAGES: Creating narrative images (Pro mode)
        GENERATING_ASSETS: Parallel TTS + BGM + image generation (Normal mode).
            Replaces the three separate phases with a single unified phase
            that tracks sub-progress for each component via details.parallel_status.
        MIXING_AUDIO: Combining TTS and BGM
        ASSEMBLING_VIDEO: Creating final video
        COMPLETE: Generation finished successfully
        ERROR: An error occurred
    """
    INITIALIZING = "initializing"
    ANALYZING = "analyzing"
    SCRIPTING = "scripting"
    GENERATING_TTS = "generating_tts"
    GENERATING_BGM = "generating_bgm"
    GENERATING_IMAGES = "generating_images"
    GENERATING_ASSETS = "generating_assets"
    MIXING_AUDIO = "mixing_audio"
    ASSEMBLING_VIDEO = "assembling_video"
    COMPLETE = "complete"
    ERROR = "error"


class SpeakerFormat(str, Enum):
    """
    Speaker format for multi-speaker podcasts (Pro mode only).

    Attributes:
        AUTO: Automatically detect from content
        SINGLE: Single narrator
        INTERVIEW: Host and guest format
        CO_HOSTS: Two co-hosts format
        NARRATOR_CHARACTERS: Narrator with character voices
    """
    AUTO = "auto"
    SINGLE = "single"
    INTERVIEW = "interview"
    CO_HOSTS = "co_hosts"
    NARRATOR_CHARACTERS = "narrator_characters"


class InputSourceType(str, Enum):
    """
    Type of input source for content extraction.

    Attributes:
        TEXT: Plain text or markdown file
        PDF: PDF document
        WORD: Word document (.docx)
        AUDIO: Audio file (mp3, wav, m4a)
        VIDEO: Video file (mp4, mov, avi, mkv)
        URL: Web URL
        GENERATED: Content generated from prompt
    """
    TEXT = "text"
    PDF = "pdf"
    WORD = "word"
    AUDIO = "audio"
    VIDEO = "video"
    URL = "url"
    GENERATED = "generated"
