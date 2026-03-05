"""
Parallel Executor
Author: Sarath

Manages concurrent API calls with rate limiting for fast generation.
Provides async batch execution for TTS, BGM, and image generation.

Features:
- Exponential backoff with jitter for rate limit handling
- Circuit breaker pattern to prevent cascade failures
- Graceful degradation on partial failures
"""

import asyncio
import random
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, List, Dict, Optional, TypeVar
from dataclasses import dataclass, field
import time


T = TypeVar('T')


# Rate limit error indicators (case-insensitive matching)
RATE_LIMIT_INDICATORS = [
    'rate limit',
    'rate_limit',
    'too many requests',
    '429',
    'throttl',
    'quota exceeded',
    'capacity',
]


def is_rate_limit_error(error: Exception) -> bool:
    """Check if an error is a rate limit error."""
    error_str = str(error).lower()
    return any(indicator in error_str for indicator in RATE_LIMIT_INDICATORS)


@dataclass
class TaskResult:
    """Result of an executed task."""
    task_id: str
    success: bool
    result: Any
    error: Optional[str] = None
    duration_ms: int = 0
    retries: int = 0


@dataclass
class CircuitBreakerState:
    """State for circuit breaker pattern."""
    failures: int = 0
    last_failure_time: float = 0.0
    is_open: bool = False
    consecutive_successes: int = 0

    # Configuration
    failure_threshold: int = 3  # Open circuit after N failures
    recovery_timeout: float = 10.0  # Seconds before trying again
    success_threshold: int = 2  # Successes needed to close circuit


class ParallelExecutor:
    """
    Manages concurrent API calls with rate limiting.

    Features:
    - Semaphore-based concurrency control
    - Automatic retry with exponential backoff + jitter
    - Circuit breaker to prevent cascade failures
    - Progress tracking
    - Thread pool for blocking I/O operations
    - Graceful degradation on partial failures
    """

    def __init__(
        self,
        max_concurrent: int = 10,
        retry_attempts: int = 3,
        retry_delay_base: float = 1.0,
        enable_circuit_breaker: bool = True
    ):
        """
        Initialize the ParallelExecutor.

        Args:
            max_concurrent: Maximum concurrent tasks
            retry_attempts: Number of retry attempts on failure
            retry_delay_base: Base delay for exponential backoff
            enable_circuit_breaker: Enable circuit breaker pattern
        """
        self.max_concurrent = max_concurrent
        self.retry_attempts = retry_attempts
        self.retry_delay_base = retry_delay_base
        self.enable_circuit_breaker = enable_circuit_breaker
        self._executor = ThreadPoolExecutor(max_workers=max_concurrent)
        self._progress_callback: Optional[Callable[[int, int], None]] = None
        self._circuit_breaker = CircuitBreakerState()

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

    async def _check_circuit_breaker(self) -> bool:
        """
        Check if circuit breaker allows request.

        Returns:
            True if request is allowed, False if circuit is open.
        """
        if not self.enable_circuit_breaker:
            return True

        cb = self._circuit_breaker

        if cb.is_open:
            # Check if recovery timeout has passed
            if time.time() - cb.last_failure_time >= cb.recovery_timeout:
                # Half-open state: allow one request through
                print("[CircuitBreaker] Half-open, allowing test request")
                return True
            return False
        return True

    def _record_success(self):
        """Record a successful request for circuit breaker."""
        if not self.enable_circuit_breaker:
            return

        cb = self._circuit_breaker
        cb.consecutive_successes += 1
        cb.failures = 0

        if cb.is_open and cb.consecutive_successes >= cb.success_threshold:
            cb.is_open = False
            cb.consecutive_successes = 0
            print("[CircuitBreaker] Circuit closed after successful requests")

    def _record_failure(self, is_rate_limit: bool = False):
        """Record a failed request for circuit breaker."""
        if not self.enable_circuit_breaker:
            return

        cb = self._circuit_breaker
        cb.failures += 1
        cb.last_failure_time = time.time()
        cb.consecutive_successes = 0

        # Rate limit errors should open circuit faster
        threshold = 2 if is_rate_limit else cb.failure_threshold

        if cb.failures >= threshold and not cb.is_open:
            cb.is_open = True
            # Longer recovery for rate limits
            cb.recovery_timeout = 15.0 if is_rate_limit else 10.0
            print(f"[CircuitBreaker] Circuit OPEN after {cb.failures} failures (rate_limit={is_rate_limit})")

    async def _execute_with_retry(
        self,
        func: Callable[..., T],
        **kwargs
    ) -> T:
        """
        Execute function with exponential backoff retry and circuit breaker.

        Args:
            func: Function to execute
            **kwargs: Function arguments

        Returns:
            Function result

        Raises:
            Exception: If all retries fail or circuit is open
        """
        last_error = None
        retries_used = 0

        for attempt in range(self.retry_attempts):
            # Check circuit breaker
            if not await self._check_circuit_breaker():
                # Wait for circuit to potentially close
                await asyncio.sleep(self._circuit_breaker.recovery_timeout / 2)
                if not await self._check_circuit_breaker():
                    raise Exception("Circuit breaker open - too many failures")

            try:
                result = await self.execute_async(func, **kwargs)
                self._record_success()
                return result
            except Exception as e:
                last_error = e
                retries_used = attempt + 1
                rate_limited = is_rate_limit_error(e)
                self._record_failure(is_rate_limit=rate_limited)

                if attempt < self.retry_attempts - 1:
                    # Exponential backoff with jitter
                    base_delay = self.retry_delay_base * (2 ** attempt)
                    # Add jitter (0-50% of base delay)
                    jitter = random.uniform(0, base_delay * 0.5)
                    delay = base_delay + jitter

                    # Longer delay for rate limits
                    if rate_limited:
                        delay = max(delay, 5.0) * 1.5
                        print(f"[Retry] Rate limit detected, waiting {delay:.1f}s (attempt {attempt + 1}/{self.retry_attempts})")
                    else:
                        print(f"[Retry] Error: {e}, waiting {delay:.1f}s (attempt {attempt + 1}/{self.retry_attempts})")

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
