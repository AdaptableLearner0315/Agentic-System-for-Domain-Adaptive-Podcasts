/**
 * React hook for managing interactive podcast conversations.
 *
 * Provides complete state management for chat sessions including:
 * - Session lifecycle (start, end)
 * - Real-time message streaming via WebSocket
 * - Audio playback for TTS responses
 * - Error handling
 */

import { useState, useCallback, useRef, useEffect } from 'react'
import {
  startInteractiveSession,
  endInteractiveSession,
  getInteractiveHistory,
  getInteractiveSessionInfo,
} from '@/lib/api'
import {
  InteractiveWebSocket,
  createInteractiveConnection,
  type InteractiveConnectionState,
} from '@/lib/interactiveWebSocket'
import type {
  ChatMessage,
  StreamingMessage,
  UseInteractiveChatReturn,
} from '@/types'

/**
 * Hook for managing interactive podcast conversations.
 *
 * Handles the complete lifecycle of a chat session including:
 * - Starting new sessions
 * - Real-time message streaming via WebSocket
 * - Message history management
 * - Session cleanup
 *
 * @returns Chat state and control functions
 *
 * @example
 * ```tsx
 * const { messages, sendMessage, startSession, isLoading } = useInteractiveChat()
 *
 * const handleStart = async () => {
 *   await startSession(jobId)
 * }
 *
 * const handleSend = async () => {
 *   await sendMessage('What was the main topic?')
 * }
 * ```
 */
export function useInteractiveChat(): UseInteractiveChatReturn {
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [isConnected, setIsConnected] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [streamingMessage, setStreamingMessage] = useState<StreamingMessage | null>(null)
  const [error, setError] = useState<string | null>(null)

  // Track current job ID for session management
  const jobIdRef = useRef<string | null>(null)

  // WebSocket connection ref
  const wsRef = useRef<InteractiveWebSocket | null>(null)

  // Cleanup WebSocket on unmount
  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.disconnect()
        wsRef.current = null
      }
    }
  }, [])

  /**
   * Connect to WebSocket for a session.
   */
  const connectWebSocket = useCallback((sessionIdToConnect: string) => {
    // Disconnect existing connection
    if (wsRef.current) {
      wsRef.current.disconnect()
      wsRef.current = null
    }

    const ws = createInteractiveConnection(sessionIdToConnect, {
      onSessionStart: () => {
        setIsConnected(true)
        setError(null)
      },
      onAssistantStart: (messageId) => {
        setIsLoading(true)
        setStreamingMessage({
          id: messageId,
          content: '',
          isComplete: false,
        })
      },
      onChunk: (messageId, chunk) => {
        setStreamingMessage((prev) => {
          if (prev && prev.id === messageId) {
            return {
              ...prev,
              content: prev.content + chunk,
            }
          }
          return prev
        })
      },
      onAssistantEnd: (messageId, fullContent) => {
        // Create the complete message
        const newMessage: ChatMessage = {
          id: messageId,
          role: 'assistant',
          content: fullContent,
          timestamp: new Date().toISOString(),
        }

        setMessages((prev) => [...prev, newMessage])
        setStreamingMessage(null)
        setIsLoading(false)
      },
      onAudioReady: (messageId, audioUrl) => {
        // Update the message with audio URL
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === messageId ? { ...msg, audio_url: audioUrl } : msg
          )
        )
      },
      onError: (errorMsg) => {
        setError(errorMsg)
        setIsLoading(false)
        setStreamingMessage(null)
      },
      onStateChange: (state: InteractiveConnectionState) => {
        setIsConnected(state === 'connected')
        if (state === 'error') {
          setError('Connection lost. Attempting to reconnect...')
        } else if (state === 'connected') {
          setError(null)
        }
      },
      onSessionEnd: () => {
        setIsConnected(false)
        setSessionId(null)
      },
    })

    wsRef.current = ws
  }, [])

  /**
   * Start a new interactive session.
   */
  const startSession = useCallback(async (jobId: string) => {
    setError(null)
    setIsLoading(true)

    try {
      // Check for existing session
      const existingSession = await getInteractiveSessionInfo(jobId)
      if (existingSession?.is_active) {
        // Reconnect to existing session
        setSessionId(existingSession.session_id)
        jobIdRef.current = jobId

        // Load history
        try {
          const history = await getInteractiveHistory(jobId)
          setMessages(history.messages)
        } catch {
          // History load failed, start fresh
          setMessages([])
        }

        connectWebSocket(existingSession.session_id)
        setIsLoading(false)
        return
      }

      // Start new session
      const response = await startInteractiveSession(jobId)
      setSessionId(response.session_id)
      jobIdRef.current = jobId

      // Add welcome message
      setMessages([response.welcome_message])

      // Connect WebSocket
      connectWebSocket(response.session_id)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to start session')
    } finally {
      setIsLoading(false)
    }
  }, [connectWebSocket])

  /**
   * Send a text message.
   */
  const sendMessage = useCallback(async (text: string) => {
    if (!sessionId || !wsRef.current || !text.trim()) return

    setError(null)

    // Add user message to state immediately
    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: text.trim(),
      timestamp: new Date().toISOString(),
    }
    setMessages((prev) => [...prev, userMessage])

    // Send via WebSocket
    wsRef.current.sendMessage(text.trim(), true)
  }, [sessionId])

  /**
   * End the current session.
   */
  const endSession = useCallback(async () => {
    if (!jobIdRef.current) return

    try {
      // Disconnect WebSocket
      if (wsRef.current) {
        wsRef.current.disconnect()
        wsRef.current = null
      }

      // End session via API
      await endInteractiveSession(jobIdRef.current)
    } catch {
      // Ignore errors on cleanup
    } finally {
      setSessionId(null)
      setMessages([])
      setIsConnected(false)
      setStreamingMessage(null)
      jobIdRef.current = null
    }
  }, [])

  /**
   * Clear error state.
   */
  const clearError = useCallback(() => {
    setError(null)
  }, [])

  return {
    sessionId,
    messages,
    isConnected,
    isLoading,
    streamingMessage,
    error,
    startSession,
    sendMessage,
    endSession,
    clearError,
  }
}
