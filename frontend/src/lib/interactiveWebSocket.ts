/**
 * WebSocket client for interactive podcast conversations.
 *
 * Provides real-time bidirectional communication for chat streaming,
 * with automatic reconnection and message handling.
 */

import type {
  StreamMessage,
  StreamEventType,
  ClientMessage,
  ChatMessage,
} from '@/types'

// WebSocket base URL from environment
const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000'

/**
 * WebSocket connection state.
 */
export type InteractiveConnectionState =
  | 'connecting'
  | 'connected'
  | 'disconnected'
  | 'error'

/**
 * Callback type for session started event.
 */
export type SessionStartCallback = (sessionId: string) => void

/**
 * Callback type for assistant response starting.
 */
export type AssistantStartCallback = (messageId: string) => void

/**
 * Callback type for streaming text chunks.
 */
export type ChunkCallback = (messageId: string, chunk: string) => void

/**
 * Callback type for assistant response complete.
 */
export type AssistantEndCallback = (messageId: string, fullContent: string) => void

/**
 * Callback type for audio ready.
 */
export type AudioReadyCallback = (messageId: string, audioUrl: string) => void

/**
 * Callback type for errors.
 */
export type InteractiveErrorCallback = (error: string) => void

/**
 * Callback type for connection state changes.
 */
export type InteractiveStateCallback = (state: InteractiveConnectionState) => void

/**
 * Callback type for session ended.
 */
export type SessionEndCallback = () => void

/**
 * WebSocket connection manager for interactive chat.
 *
 * Handles connection lifecycle, message streaming, and reconnection.
 */
export class InteractiveWebSocket {
  private socket: WebSocket | null = null
  private sessionId: string
  private onSessionStart?: SessionStartCallback
  private onAssistantStart?: AssistantStartCallback
  private onChunk?: ChunkCallback
  private onAssistantEnd?: AssistantEndCallback
  private onAudioReady?: AudioReadyCallback
  private onError?: InteractiveErrorCallback
  private onStateChange?: InteractiveStateCallback
  private onSessionEnd?: SessionEndCallback
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 1000
  private pingInterval?: NodeJS.Timeout
  private shouldReconnect = true

  /**
   * Create a new interactive WebSocket connection manager.
   *
   * @param sessionId - Session identifier to connect to
   */
  constructor(sessionId: string) {
    this.sessionId = sessionId
  }

  /**
   * Set session start callback.
   */
  setSessionStartCallback(callback: SessionStartCallback): this {
    this.onSessionStart = callback
    return this
  }

  /**
   * Set assistant start callback.
   */
  setAssistantStartCallback(callback: AssistantStartCallback): this {
    this.onAssistantStart = callback
    return this
  }

  /**
   * Set chunk callback for streaming text.
   */
  setChunkCallback(callback: ChunkCallback): this {
    this.onChunk = callback
    return this
  }

  /**
   * Set assistant end callback.
   */
  setAssistantEndCallback(callback: AssistantEndCallback): this {
    this.onAssistantEnd = callback
    return this
  }

  /**
   * Set audio ready callback.
   */
  setAudioReadyCallback(callback: AudioReadyCallback): this {
    this.onAudioReady = callback
    return this
  }

  /**
   * Set error callback.
   */
  setErrorCallback(callback: InteractiveErrorCallback): this {
    this.onError = callback
    return this
  }

  /**
   * Set state change callback.
   */
  setStateCallback(callback: InteractiveStateCallback): this {
    this.onStateChange = callback
    return this
  }

  /**
   * Set session end callback.
   */
  setSessionEndCallback(callback: SessionEndCallback): this {
    this.onSessionEnd = callback
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

    const url = `${WS_URL}/api/ws/interactive/${this.sessionId}`
    this.socket = new WebSocket(url)

    this.socket.onopen = () => {
      this.reconnectAttempts = 0
      this.updateState('connected')
      this.startPing()
    }

    this.socket.onmessage = (event) => {
      this.handleMessage(event.data)
    }

    this.socket.onclose = () => {
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
   * Send a chat message.
   *
   * @param content - Message text
   * @param generateAudio - Whether to generate TTS audio
   */
  sendMessage(content: string, generateAudio: boolean = true): void {
    const message: ClientMessage = {
      type: 'message',
      content,
      generate_audio: generateAudio,
    }
    this.send(message)
  }

  /**
   * Request session end.
   */
  endSession(): void {
    const message: ClientMessage = {
      type: 'end_session',
    }
    this.send(message)
  }

  /**
   * Send a message to the server.
   */
  private send(message: ClientMessage): void {
    if (this.socket?.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify(message))
    }
  }

  /**
   * Handle incoming WebSocket message.
   */
  private handleMessage(data: string): void {
    try {
      const message: StreamMessage = JSON.parse(data)

      switch (message.type) {
        case 'session_started':
          if (this.onSessionStart) {
            this.onSessionStart(message.session_id)
          }
          break

        case 'assistant_start':
          if (this.onAssistantStart && message.message_id) {
            this.onAssistantStart(message.message_id)
          }
          break

        case 'assistant_chunk':
          if (this.onChunk && message.message_id && message.content) {
            this.onChunk(message.message_id, message.content)
          }
          break

        case 'assistant_end':
          if (this.onAssistantEnd && message.message_id) {
            this.onAssistantEnd(message.message_id, message.content || '')
          }
          break

        case 'audio_ready':
          if (this.onAudioReady && message.message_id && message.audio_url) {
            this.onAudioReady(message.message_id, message.audio_url)
          }
          break

        case 'error':
          if (this.onError) {
            this.onError(message.error || 'Unknown error')
          }
          break

        case 'session_ended':
          if (this.onSessionEnd) {
            this.onSessionEnd()
          }
          this.disconnect()
          break

        case 'heartbeat':
        case 'pong':
          // Keep-alive messages, no action needed
          break

        default:
          console.warn('Unknown interactive WebSocket message type:', message.type)
      }
    } catch (e) {
      console.error('Failed to parse interactive WebSocket message:', e)
    }
  }

  /**
   * Update connection state and notify callback.
   */
  private updateState(state: InteractiveConnectionState): void {
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
      if (this.socket?.readyState === WebSocket.OPEN) {
        this.socket.send(JSON.stringify({ type: 'ping' }))
      }
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

  /**
   * Get current connection state.
   */
  isConnected(): boolean {
    return this.socket?.readyState === WebSocket.OPEN
  }
}

/**
 * Callbacks for interactive WebSocket connection.
 */
export interface InteractiveWebSocketCallbacks {
  onSessionStart?: SessionStartCallback
  onAssistantStart?: AssistantStartCallback
  onChunk?: ChunkCallback
  onAssistantEnd?: AssistantEndCallback
  onAudioReady?: AudioReadyCallback
  onError?: InteractiveErrorCallback
  onStateChange?: InteractiveStateCallback
  onSessionEnd?: SessionEndCallback
}

/**
 * Create an interactive WebSocket connection.
 *
 * Convenience function for creating and connecting a WebSocket.
 *
 * @param sessionId - Session identifier
 * @param callbacks - Event callbacks
 * @returns InteractiveWebSocket instance
 */
export function createInteractiveConnection(
  sessionId: string,
  callbacks: InteractiveWebSocketCallbacks
): InteractiveWebSocket {
  const ws = new InteractiveWebSocket(sessionId)

  if (callbacks.onSessionStart) ws.setSessionStartCallback(callbacks.onSessionStart)
  if (callbacks.onAssistantStart) ws.setAssistantStartCallback(callbacks.onAssistantStart)
  if (callbacks.onChunk) ws.setChunkCallback(callbacks.onChunk)
  if (callbacks.onAssistantEnd) ws.setAssistantEndCallback(callbacks.onAssistantEnd)
  if (callbacks.onAudioReady) ws.setAudioReadyCallback(callbacks.onAudioReady)
  if (callbacks.onError) ws.setErrorCallback(callbacks.onError)
  if (callbacks.onStateChange) ws.setStateCallback(callbacks.onStateChange)
  if (callbacks.onSessionEnd) ws.setSessionEndCallback(callbacks.onSessionEnd)

  ws.connect()
  return ws
}
