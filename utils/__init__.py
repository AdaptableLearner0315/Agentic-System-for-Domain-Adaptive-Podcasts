"""
Utilities Module
Author: Sarath

Shared utilities for the podcast enhancement system.
"""

from utils.fal_api import (
    call_fal_api,
    extract_url_from_response,
    download_media,
    generate_audio,
    generate_image,
    generate_speech,
)

from utils.text_processing import (
    preprocess_text_for_tts,
    get_intensity_for_sentence,
    split_into_sentences,
)

from utils.input_router import (
    InputRouter,
    ExtractedContent,
    extract_content,
)

from utils.parallel_executor import (
    ParallelExecutor,
    TTSParallelExecutor,
    BGMParallelExecutor,
    ImageParallelExecutor,
    TaskResult,
    run_parallel_generation,
)

from utils.progress_stream import (
    GenerationPhase,
    ProgressUpdate,
    ProgressStream,
    stream_generation,
    print_progress,
)

__all__ = [
    # FAL API
    'call_fal_api',
    'extract_url_from_response',
    'download_media',
    'generate_audio',
    'generate_image',
    'generate_speech',
    # Text processing
    'preprocess_text_for_tts',
    'get_intensity_for_sentence',
    'split_into_sentences',
    # Input routing
    'InputRouter',
    'ExtractedContent',
    'extract_content',
    # Parallel execution
    'ParallelExecutor',
    'TTSParallelExecutor',
    'BGMParallelExecutor',
    'ImageParallelExecutor',
    'TaskResult',
    'run_parallel_generation',
    # Progress streaming
    'GenerationPhase',
    'ProgressUpdate',
    'ProgressStream',
    'stream_generation',
    'print_progress',
]
