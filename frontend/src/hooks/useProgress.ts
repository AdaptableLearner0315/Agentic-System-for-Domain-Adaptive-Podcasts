/**
 * React hook for WebSocket progress subscription.
 *
 * A lower-level hook for subscribing to job progress updates.
 * Use useGeneration for the full workflow management.
 */

import { useState, useEffect, useCallback, useRef } from 'react'
import {
  ProgressWebSocket,
  ConnectionState,
} from '@/lib/websocket'
import type { ProgressResponse } from '@/types'

/**
 * Return type for the useProgress hook.
 */
interface UseProgressReturn {
  /** Current progress data */
  progress: ProgressResponse | null
  /** WebSocket connection state */
  connectionState: ConnectionState
  /** Whether job is complete */
  isComplete: boolean
  /** Completion data if complete */
  completionData: {
    success: boolean
    videoUrl?: string
    outputPath?: string
    durationSeconds?: number
  } | null
  /** Error message if any */
  error: string | null
  /** Manually disconnect */
  disconnect: () => void
  /** Request job cancellation */
  requestCancel: () => void
}

/**
 * Hook for subscribing to job progress via WebSocket.
 *
 * @param jobId - Job identifier to subscribe to (null to not connect)
 * @returns Progress state and control functions
 *
 * @example
 * ```tsx
 * const { progress, connectionState, isComplete } = useProgress(jobId)
 *
 * if (isComplete) {
 *   // Handle completion
 * }
 * ```
 */
export function useProgress(jobId: string | null): UseProgressReturn {
  const [progress, setProgress] = useState<ProgressResponse | null>(null)
  const [connectionState, setConnectionState] = useState<ConnectionState>('disconnected')
  const [isComplete, setIsComplete] = useState(false)
  const [completionData, setCompletionData] = useState<{
    success: boolean
    videoUrl?: string
    outputPath?: string
    durationSeconds?: number
  } | null>(null)
  const [error, setError] = useState<string | null>(null)

  const wsRef = useRef<ProgressWebSocket | null>(null)

  // Connect/disconnect based on jobId
  useEffect(() => {
    // Disconnect existing connection
    if (wsRef.current) {
      wsRef.current.disconnect()
      wsRef.current = null
    }

    // Reset state
    setProgress(null)
    setIsComplete(false)
    setCompletionData(null)
    setError(null)

    // Don't connect if no jobId
    if (!jobId) {
      setConnectionState('disconnected')
      return
    }

    // Create new connection
    const ws = new ProgressWebSocket(jobId)

    ws.setProgressCallback((data) => {
      setProgress(data)
    })

    ws.setCompleteCallback((data) => {
      setIsComplete(true)
      setCompletionData({
        success: data.success,
        videoUrl: data.video_url,
        outputPath: data.output_path,
        durationSeconds: data.duration_seconds,
      })
    })

    ws.setErrorCallback((errorMsg) => {
      setError(errorMsg)
    })

    ws.setStateCallback((state) => {
      setConnectionState(state)
    })

    ws.connect()
    wsRef.current = ws

    // Cleanup on unmount or jobId change
    return () => {
      if (wsRef.current) {
        wsRef.current.disconnect()
        wsRef.current = null
      }
    }
  }, [jobId])

  /**
   * Manually disconnect from WebSocket.
   */
  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.disconnect()
    }
  }, [])

  /**
   * Request job cancellation via WebSocket.
   */
  const requestCancel = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.requestCancel()
    }
  }, [])

  return {
    progress,
    connectionState,
    isComplete,
    completionData,
    error,
    disconnect,
    requestCancel,
  }
}
