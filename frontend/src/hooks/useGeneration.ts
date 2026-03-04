/**
 * React hook for managing podcast generation state.
 *
 * Provides a complete state management solution for the generation
 * workflow including API calls, WebSocket connection, and error handling.
 */

import { useState, useCallback, useRef, useEffect } from 'react'
import { startGeneration, cancelJob, getJobResult, getJob, getJobStatus } from '@/lib/api'
import { ProgressWebSocket, createProgressConnection } from '@/lib/websocket'
import { STORAGE_KEYS } from '@/lib/constants'
import type {
  GenerationRequest,
  JobStatus,
  ProgressResponse,
  ResultResponse,
  TrailerData,
} from '@/types'

/**
 * Return type for the useGeneration hook.
 */
interface UseGenerationReturn {
  /** Current job status */
  status: JobStatus | null
  /** Current progress data */
  progress: ProgressResponse | null
  /** Final result data */
  result: ResultResponse | null
  /** Error message if any */
  error: string | null
  /** Current job ID */
  jobId: string | null
  /** Whether a job is currently running */
  isLoading: boolean
  /** Trailer preview data (available before full result) */
  trailer: TrailerData | null
  /** Start a new generation */
  startGeneration: (request: GenerationRequest) => Promise<void>
  /** Cancel the current job */
  cancelGeneration: () => Promise<void>
  /** Reset all state */
  reset: () => void
}

/**
 * Hook for managing podcast generation state.
 *
 * Handles the complete lifecycle of a generation job including:
 * - Starting new generations
 * - Real-time progress tracking via WebSocket
 * - Job cancellation
 * - Error handling
 * - Result fetching
 *
 * @returns Generation state and control functions
 *
 * @example
 * ```tsx
 * const { status, progress, result, startGeneration, cancelGeneration } = useGeneration()
 *
 * const handleGenerate = async () => {
 *   await startGeneration({ prompt: 'History of AI', mode: 'normal' })
 * }
 * ```
 */
export function useGeneration(): UseGenerationReturn {
  const [status, setStatus] = useState<JobStatus | null>(null)
  const [progress, setProgress] = useState<ProgressResponse | null>(null)
  const [result, setResult] = useState<ResultResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [jobId, setJobId] = useState<string | null>(null)
  const [trailer, setTrailer] = useState<TrailerData | null>(null)

  // WebSocket connection ref
  const wsRef = useRef<ProgressWebSocket | null>(null)

  // On mount: recover active job from localStorage
  useEffect(() => {
    const savedJobId = localStorage.getItem(STORAGE_KEYS.ACTIVE_JOB_ID)
    if (savedJobId) {
      // Check if job is still running
      getJob(savedJobId)
        .then((job) => {
          if (job.status === 'running' || job.status === 'pending') {
            setJobId(savedJobId)
            setStatus(job.status)
          } else if (job.status === 'completed') {
            setJobId(savedJobId)
            setStatus('completed')
            getJobResult(savedJobId).then(setResult).catch(() => {})
            localStorage.removeItem(STORAGE_KEYS.ACTIVE_JOB_ID)
          } else {
            localStorage.removeItem(STORAGE_KEYS.ACTIVE_JOB_ID)
          }
        })
        .catch(() => {
          localStorage.removeItem(STORAGE_KEYS.ACTIVE_JOB_ID)
        })
    }
  }, [])

  // Track if we should connect (avoid connecting for terminal states from localStorage recovery)
  const shouldConnectRef = useRef(false)

  // Update shouldConnect when status changes (for localStorage recovery case)
  useEffect(() => {
    shouldConnectRef.current = status === 'pending' || status === 'running'
  }, [status])

  // WebSocket lifecycle: connect when jobId is set, cleanup on change/unmount
  // NOTE: status is NOT a dependency - we don't want to reconnect when status changes
  useEffect(() => {
    // Don't connect if no job
    if (!jobId) return

    // Don't connect if status is terminal (e.g., recovered completed job from localStorage)
    // We check the ref which is updated by the previous effect
    if (!shouldConnectRef.current && (status === 'completed' || status === 'failed' || status === 'cancelled')) {
      return
    }

    const ws = createProgressConnection(jobId, {
      onProgress: (progressData) => {
        setProgress(progressData)
        if (progressData.phase === 'complete') {
          setStatus('completed')
        } else if (progressData.phase === 'error') {
          setStatus('failed')
        } else {
          setStatus('running')
        }
      },
      onComplete: async (data) => {
        setStatus('completed')
        localStorage.removeItem(STORAGE_KEYS.ACTIVE_JOB_ID)
        try {
          const fullResult = await getJobResult(jobId)
          setResult(fullResult)
        } catch {
          setResult({
            job_id: jobId,
            success: data.success,
            video_url: data.video_url,
            output_path: data.output_path,
            duration_seconds: data.duration_seconds,
          })
        }
      },
      onError: (errorMsg) => {
        setStatus('failed')
        setError(errorMsg)
        localStorage.removeItem(STORAGE_KEYS.ACTIVE_JOB_ID)
      },
      onStateChange: (state) => {
        if (state === 'error') {
          setError('Connection lost. Attempting to reconnect...')
        } else if (state === 'connected') {
          setError(null)
        }
      },
      onTrailerReady: (trailerData) => {
        // Trailer preview is ready - show it to user while full podcast generates
        setTrailer(trailerData)
      },
    })
    wsRef.current = ws

    return () => {
      ws.disconnect()
      wsRef.current = null
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [jobId]) // Only reconnect when jobId changes, NOT when status changes

  /**
   * Start a new generation job.
   */
  const handleStartGeneration = useCallback(async (request: GenerationRequest) => {
    // Reset state
    setError(null)
    setResult(null)
    setProgress(null)
    setTrailer(null)

    try {
      // Create job via API
      const job = await startGeneration(request)

      // Persist job ID for recovery across page refresh
      localStorage.setItem(STORAGE_KEYS.ACTIVE_JOB_ID, job.id)

      // Set status first so the useEffect sees 'pending'/'running' (not a terminal state)
      setStatus(job.status)
      // Setting jobId triggers the useEffect that connects the WebSocket
      setJobId(job.id)
    } catch (e) {
      setStatus('failed')
      setError(e instanceof Error ? e.message : 'Failed to start generation')
    }
  }, [])

  /**
   * Cancel the current job.
   */
  const handleCancelGeneration = useCallback(async () => {
    if (!jobId) return

    try {
      // Disconnect WebSocket first
      if (wsRef.current) {
        wsRef.current.disconnect()
        wsRef.current = null
      }

      // Cancel via API
      await cancelJob(jobId)
      setStatus('cancelled')
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to cancel job')
    }
  }, [jobId])

  /**
   * Reset all state.
   */
  const handleReset = useCallback(() => {
    // Disconnect WebSocket
    if (wsRef.current) {
      wsRef.current.disconnect()
      wsRef.current = null
    }

    // Clear persisted job
    localStorage.removeItem(STORAGE_KEYS.ACTIVE_JOB_ID)

    // Reset all state
    setStatus(null)
    setProgress(null)
    setResult(null)
    setError(null)
    setJobId(null)
    setTrailer(null)
  }, [])

  return {
    status,
    progress,
    result,
    error,
    jobId,
    isLoading: status === 'pending' || status === 'running',
    trailer,
    startGeneration: handleStartGeneration,
    cancelGeneration: handleCancelGeneration,
    reset: handleReset,
  }
}
