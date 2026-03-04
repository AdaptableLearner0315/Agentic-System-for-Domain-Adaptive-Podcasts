"""
Parallel Executor
Author: Sarath

Manages concurrent API calls with rate limiting for fast generation.
Provides async batch execution for TTS, BGM, and image generation.
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, List, Dict, Optional, TypeVar
from dataclasses import dataclass
import time


T = TypeVar('T')


@dataclass
class TaskResult:
    """Result of an executed task."""
    task_id: str
    success: bool
    result: Any
    error: Optional[str] = None
    duration_ms: int = 0


class ParallelExecutor:
    """
    Manages concurrent API calls with rate limiting.

    Features:
    - Semaphore-based concurrency control
    - Automatic retry with exponential backoff
    - Progress tracking
    - Thread pool for blocking I/O operations
    """

    def __init__(
        self,
        max_concurrent: int = 10,
        retry_attempts: int = 3,
        retry_delay_base: float = 1.0
    ):
        """
        Initialize the ParallelExecutor.

        Args:
            max_concurrent: Maximum concurrent tasks
            retry_attempts: Number of retry attempts on failure
            retry_delay_base: Base delay for exponential backoff
        """
        self.max_concurrent = max_concurrent
        self.retry_attempts = retry_attempts
        self.retry_delay_base = retry_delay_base
        self._executor = ThreadPoolExecutor(max_workers=max_concurrent)
        self._progress_callback: Optional[Callable[[int, int], None]] = None

    def set_progress_callback(self, callback: Callable[[int, int], None]):
        """Set a callback for progress updates (completed, total)."""
        self._progress_callback = callback

    async def execute_async(
        self,
        func: Callable[..., T],
        *args,
        **kwargs
    ) -> T:
        """
        Execute a synchronous function in a thread pool.

        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Function result
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._executor,
            lambda: func(*args, **kwargs)
        )

    async def batch_execute(
        self,
        tasks: List[Dict[str, Any]],
        task_func: Callable[..., Any]
    ) -> List[TaskResult]:
        """
        Execute multiple tasks in parallel with concurrency limit.

        Args:
            tasks: List of task dictionaries with 'id' and 'args'
            task_func: Function to execute for each task

        Returns:
            List of TaskResult objects
        """
        semaphore = asyncio.Semaphore(self.max_concurrent)
        results: List[TaskResult] = []
        completed = 0
        total = len(tasks)

        async def limited_task(task_dict: Dict[str, Any]) -> TaskResult:
            nonlocal completed
            async with semaphore:
                task_id = task_dict.get('id', str(len(results)))
                args = task_dict.get('args', {})

                start_time = time.time()
                try:
                    # Execute with retry logic
                    result = await self._execute_with_retry(
                        task_func,
                        **args
                    )
                    duration_ms = int((time.time() - start_time) * 1000)
                    completed += 1
                    if self._progress_callback:
                        self._progress_callback(completed, total)
                    return TaskResult(
                        task_id=task_id,
                        success=True,
                        result=result,
                        duration_ms=duration_ms
                    )
                except Exception as e:
                    duration_ms = int((time.time() - start_time) * 1000)
                    completed += 1
                    if self._progress_callback:
                        self._progress_callback(completed, total)
                    return TaskResult(
                        task_id=task_id,
                        success=False,
                        result=None,
                        error=str(e),
                        duration_ms=duration_ms
                    )

        results = await asyncio.gather(*[limited_task(t) for t in tasks])
        return results

    async def _execute_with_retry(
        self,
        func: Callable[..., T],
        **kwargs
    ) -> T:
        """
        Execute function with exponential backoff retry.

        Args:
            func: Function to execute
            **kwargs: Function arguments

        Returns:
            Function result

        Raises:
            Exception: If all retries fail
        """
        last_error = None
        for attempt in range(self.retry_attempts):
            try:
                return await self.execute_async(func, **kwargs)
            except Exception as e:
                last_error = e
                if attempt < self.retry_attempts - 1:
                    delay = self.retry_delay_base * (2 ** attempt)
                    await asyncio.sleep(delay)
        raise last_error

    def shutdown(self):
        """Shutdown the thread pool executor."""
        self._executor.shutdown(wait=True)


class TTSParallelExecutor(ParallelExecutor):
    """Specialized executor for TTS generation."""

    def __init__(self, max_concurrent: int = 10):
        super().__init__(max_concurrent=max_concurrent)

    async def generate_batch(
        self,
        chunks: List[Dict[str, Any]],
        tts_func: Callable[[str, str], Optional[str]]
    ) -> List[Dict[str, Any]]:
        """
        Generate TTS for multiple chunks in parallel.

        Args:
            chunks: List of chunks with 'text', 'filename', etc.
            tts_func: TTS generation function (text, filename) -> path

        Returns:
            List of results with paths and metadata
        """
        tasks = [
            {
                'id': f"tts_{i}",
                'args': {
                    'text': chunk['text'],
                    'filename': chunk['filename']
                }
            }
            for i, chunk in enumerate(chunks)
        ]

        results = await self.batch_execute(tasks, tts_func)

        # Merge results back with original chunk metadata
        output = []
        for chunk, result in zip(chunks, results):
            if result.success:
                output.append({
                    **chunk,
                    'path': result.result,
                    'duration_ms': result.duration_ms
                })
            else:
                output.append({
                    **chunk,
                    'path': None,
                    'error': result.error
                })

        return output


class BGMParallelExecutor(ParallelExecutor):
    """Specialized executor for BGM generation."""

    def __init__(self, max_concurrent: int = 3):
        # Lower concurrency for BGM (longer operations)
        super().__init__(max_concurrent=max_concurrent)

    async def generate_batch(
        self,
        segments: List[Dict[str, Any]],
        bgm_func: Callable[[str, str, int], Optional[str]]
    ) -> List[Dict[str, Any]]:
        """
        Generate BGM segments in parallel.

        Args:
            segments: List of segments with 'prompt', 'filename', 'duration'.
                      Can also include 'use_stems' and 'emotions' for stem mixing.
            bgm_func: BGM generation function (emotion, filename, duration, **kwargs) -> path

        Returns:
            List of results with paths
        """
        tasks = []
        for i, seg in enumerate(segments):
            args = {
                'emotion': seg.get('emotion', 'neutral'),
                'output_filename': seg['filename'],
                'duration': seg.get('duration', 30)
            }
            # Pass extra kwargs for stem mixing if present
            if seg.get('use_stems'):
                args['use_stems'] = True
                args['emotions'] = seg.get('emotions', [])

            tasks.append({
                'id': f"bgm_{seg.get('segment_id', i)}",
                'args': args
            })

        results = await self.batch_execute(tasks, bgm_func)

        output = []
        for seg, result in zip(segments, results):
            if result.success:
                output.append({
                    **seg,
                    'path': result.result,
                    'duration_ms': result.duration_ms
                })
            else:
                output.append({
                    **seg,
                    'path': None,
                    'error': result.error
                })

        return output


class ImageParallelExecutor(ParallelExecutor):
    """Specialized executor for image generation."""

    def __init__(self, max_concurrent: int = 4):
        super().__init__(max_concurrent=max_concurrent)

    async def generate_batch(
        self,
        prompts: List[Dict[str, Any]],
        image_func: Callable[[str, str], Optional[str]]
    ) -> List[Dict[str, Any]]:
        """
        Generate images in parallel.

        Args:
            prompts: List of prompts with 'prompt', 'filename'
            image_func: Image generation function (prompt, filename) -> path

        Returns:
            List of results with paths
        """
        tasks = [
            {
                'id': f"img_{i}",
                'args': {
                    'prompt': p['prompt'],
                    'filename': p['filename']
                }
            }
            for i, p in enumerate(prompts)
        ]

        results = await self.batch_execute(tasks, image_func)

        output = []
        for prompt, result in zip(prompts, results):
            if result.success:
                output.append({
                    **prompt,
                    'path': result.result,
                    'duration_ms': result.duration_ms
                })
            else:
                output.append({
                    **prompt,
                    'path': None,
                    'error': result.error
                })

        return output


async def run_parallel_generation(
    tts_tasks: List[Dict[str, Any]],
    bgm_tasks: List[Dict[str, Any]],
    image_tasks: List[Dict[str, Any]],
    tts_func: Callable,
    bgm_func: Callable,
    image_func: Callable,
    tts_workers: int = 10,
    bgm_workers: int = 3,
    image_workers: int = 4,
    progress_callback: Optional[Callable[[str, int, int], None]] = None
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Run TTS, BGM, and image generation in parallel.

    Args:
        tts_tasks: TTS generation tasks
        bgm_tasks: BGM generation tasks
        image_tasks: Image generation tasks
        tts_func: TTS generation function
        bgm_func: BGM generation function
        image_func: Image generation function
        tts_workers: TTS concurrency
        bgm_workers: BGM concurrency
        image_workers: Image concurrency
        progress_callback: Optional callback (type, completed, total)

    Returns:
        Dictionary with 'tts', 'bgm', 'images' results
    """
    tts_executor = TTSParallelExecutor(max_concurrent=tts_workers)
    bgm_executor = BGMParallelExecutor(max_concurrent=bgm_workers)
    image_executor = ImageParallelExecutor(max_concurrent=image_workers)

    if progress_callback:
        tts_executor.set_progress_callback(
            lambda c, t: progress_callback('tts', c, t)
        )
        bgm_executor.set_progress_callback(
            lambda c, t: progress_callback('bgm', c, t)
        )
        image_executor.set_progress_callback(
            lambda c, t: progress_callback('images', c, t)
        )

    # Run all three in parallel
    tts_task = tts_executor.generate_batch(tts_tasks, tts_func)
    bgm_task = bgm_executor.generate_batch(bgm_tasks, bgm_func)
    image_task = image_executor.generate_batch(image_tasks, image_func)

    tts_results, bgm_results, image_results = await asyncio.gather(
        tts_task, bgm_task, image_task
    )

    # Cleanup
    tts_executor.shutdown()
    bgm_executor.shutdown()
    image_executor.shutdown()

    return {
        'tts': tts_results,
        'bgm': bgm_results,
        'images': image_results
    }


__all__ = [
    'ParallelExecutor',
    'TTSParallelExecutor',
    'BGMParallelExecutor',
    'ImageParallelExecutor',
    'TaskResult',
    'run_parallel_generation',
]
