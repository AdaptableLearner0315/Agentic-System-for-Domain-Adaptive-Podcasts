/**
 * React hook for managing podcast generation state.
 *
 * Provides a complete state management solution for the generation
 * workflow including API calls, WebSocket connection, and error handling.
 */

import { useState, useCallback, useRef, useEffect } from 'react'
import { startGeneration, cancelJob, getJobResult, getJob } from '@/lib/api'
import { ProgressWebSocket, createProgressConnection } from '@/lib/websocket'
import type {
  GenerationRequest,
  JobStatus,
  ProgressResponse,
  ResultResponse,
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

  // WebSocket connection ref
  const wsRef = useRef<ProgressWebSocket | null>(null)

  // Cleanup WebSocket on unmount
  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.disconnect()
      }
    }
  }, [])

  /**
   * Start a new generation job.
   */
  const handleStartGeneration = useCallback(async (request: GenerationRequest) => {
    // Reset state
    setError(null)
    setResult(null)
    setProgress(null)

    try {
      // Create job via API
      const job = await startGeneration(request)
      setJobId(job.id)
      setStatus(job.status)

      // Connect to WebSocket for progress updates
      wsRef.current = createProgressConnection(job.id, {
        onProgress: (progressData) => {
          setProgress(progressData)
          // Update status based on phase
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
          // Fetch full result
          try {
            const fullResult = await getJobResult(job.id)
            setResult(fullResult)
          } catch (e) {
            // Use partial result from WebSocket
            setResult({
              job_id: job.id,
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
        },
        onStateChange: (state) => {
          if (state === 'error') {
            setError('Connection lost. Attempting to reconnect...')
          } else if (state === 'connected') {
            setError(null)
          }
        },
      })
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

    // Reset all state
    setStatus(null)
    setProgress(null)
    setResult(null)
    setError(null)
    setJobId(null)
  }, [])

  return {
    status,
    progress,
    result,
    error,
    jobId,
    isLoading: status === 'pending' || status === 'running',
    startGeneration: handleStartGeneration,
    cancelGeneration: handleCancelGeneration,
    reset: handleReset,
  }
}
