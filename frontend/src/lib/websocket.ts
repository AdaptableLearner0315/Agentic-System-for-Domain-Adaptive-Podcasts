/**
 * WebSocket client for real-time progress updates.
 *
 * Provides a connection manager with automatic reconnection
 * and message handling.
 */

import type { WebSocketMessage, ProgressResponse } from '@/types'

// WebSocket base URL from environment
const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000'

/**
 * WebSocket connection state.
 */
export type ConnectionState = 'connecting' | 'connected' | 'disconnected' | 'error'

/**
 * Callback type for progress updates.
 */
export type ProgressCallback = (progress: ProgressResponse) => void

/**
 * Callback type for completion.
 */
export type CompleteCallback = (data: {
  success: boolean
  output_path?: string
  video_url?: string
  duration_seconds?: number
}) => void

/**
 * Callback type for errors.
 */
export type ErrorCallback = (error: string) => void

/**
 * Callback type for connection state changes.
 */
export type StateCallback = (state: ConnectionState) => void

/**
 * WebSocket connection manager for job progress.
 *
 * Handles connection lifecycle, message parsing, and reconnection.
 */
export class ProgressWebSocket {
  private socket: WebSocket | null = null
  private jobId: string
  private onProgress?: ProgressCallback
  private onComplete?: CompleteCallback
  private onError?: ErrorCallback
  private onStateChange?: StateCallback
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 1000
  private pingInterval?: NodeJS.Timeout
  private shouldReconnect = true

  /**
   * Create a new WebSocket connection manager.
   *
   * @param jobId - Job identifier to subscribe to
   */
  constructor(jobId: string) {
    this.jobId = jobId
  }

  /**
   * Set progress update callback.
   */
  setProgressCallback(callback: ProgressCallback): this {
    this.onProgress = callback
    return this
  }

  /**
   * Set completion callback.
   */
  setCompleteCallback(callback: CompleteCallback): this {
    this.onComplete = callback
    return this
  }

  /**
   * Set error callback.
   */
  setErrorCallback(callback: ErrorCallback): this {
    this.onError = callback
    return this
  }

  /**
   * Set state change callback.
   */
  setStateCallback(callback: StateCallback): this {
    this.onStateChange = callback
    return this
  }

  /**
   * Connect to the WebSocket server.
   */
  connect(): void {
    if (this.socket?.readyState === WebSocket.OPEN) {
      return
    }

    this.shouldReconnect = true
    this.updateState('connecting')

    const url = `${WS_URL}/api/ws/${this.jobId}/progress`
    this.socket = new WebSocket(url)

    this.socket.onopen = () => {
      this.reconnectAttempts = 0
      this.updateState('connected')
      this.startPing()
    }

    this.socket.onmessage = (event) => {
      this.handleMessage(event.data)
    }

    this.socket.onclose = (event) => {
      this.stopPing()
      this.updateState('disconnected')

      // Attempt reconnection if not intentionally closed
      if (this.shouldReconnect && this.reconnectAttempts < this.maxReconnectAttempts) {
        this.reconnectAttempts++
        const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1)
        setTimeout(() => this.connect(), delay)
      }
    }

    this.socket.onerror = () => {
      this.updateState('error')
    }
  }

  /**
   * Disconnect from the WebSocket server.
   */
  disconnect(): void {
    this.shouldReconnect = false
    this.stopPing()

    if (this.socket) {
      this.socket.close()
      this.socket = null
    }
  }

  /**
   * Send a message to the server.
   */
  send(message: object): void {
    if (this.socket?.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify(message))
    }
  }

  /**
   * Request job cancellation.
   */
  requestCancel(): void {
    this.send({ type: 'cancel' })
  }

  /**
   * Handle incoming WebSocket message.
   */
  private handleMessage(data: string): void {
    try {
      const message: WebSocketMessage = JSON.parse(data)

      switch (message.type) {
        case 'progress':
          if (this.onProgress && message.job_id) {
            this.onProgress({
              job_id: message.job_id,
              phase: message.phase || 'initializing',
              message: message.message || '',
              progress_percent: message.progress_percent || 0,
              current_step: message.current_step || 0,
              total_steps: message.total_steps || 0,
              eta_seconds: message.eta_seconds,
              preview: message.preview,
              elapsed_seconds: message.elapsed_seconds || 0,
              details: message.details,
            })
          }
          break

        case 'complete':
          if (this.onComplete) {
            this.onComplete({
              success: message.success || false,
              output_path: message.output_path,
              video_url: message.video_url,
              duration_seconds: message.duration_seconds,
            })
          }
          this.disconnect()
          break

        case 'error':
          if (this.onError) {
            this.onError(message.error || 'Unknown error')
          }
          this.disconnect()
          break

        case 'cancelled':
          if (this.onError) {
            this.onError('Job was cancelled')
          }
          this.disconnect()
          break

        case 'heartbeat':
        case 'pong':
          // Keep-alive messages, no action needed
          break

        default:
          // Unknown message type
          console.warn('Unknown WebSocket message type:', message.type)
      }
    } catch (e) {
      console.error('Failed to parse WebSocket message:', e)
    }
  }

  /**
   * Update connection state and notify callback.
   */
  private updateState(state: ConnectionState): void {
    if (this.onStateChange) {
      this.onStateChange(state)
    }
  }

  /**
   * Start sending periodic ping messages.
   */
  private startPing(): void {
    this.stopPing()
    this.pingInterval = setInterval(() => {
      this.send({ type: 'ping' })
    }, 25000) // Send ping every 25 seconds
  }

  /**
   * Stop sending ping messages.
   */
  private stopPing(): void {
    if (this.pingInterval) {
      clearInterval(this.pingInterval)
      this.pingInterval = undefined
    }
  }
}

/**
 * Create a WebSocket connection for a job.
 *
 * Convenience function for creating and connecting a WebSocket.
 *
 * @param jobId - Job identifier
 * @param callbacks - Event callbacks
 * @returns ProgressWebSocket instance
 */
export function createProgressConnection(
  jobId: string,
  callbacks: {
    onProgress?: ProgressCallback
    onComplete?: CompleteCallback
    onError?: ErrorCallback
    onStateChange?: StateCallback
  }
): ProgressWebSocket {
  const ws = new ProgressWebSocket(jobId)

  if (callbacks.onProgress) ws.setProgressCallback(callbacks.onProgress)
  if (callbacks.onComplete) ws.setCompleteCallback(callbacks.onComplete)
  if (callbacks.onError) ws.setErrorCallback(callbacks.onError)
  if (callbacks.onStateChange) ws.setStateCallback(callbacks.onStateChange)

  ws.connect()
  return ws
}
