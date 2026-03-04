'use client'

import { useRef, useEffect, useState, useCallback } from 'react'
import { ChatMessage } from './ChatMessage'
import { ChatInput } from './ChatInput'
import { useInteractiveChat } from '@/hooks/useInteractiveChat'
import type { ChatMessage as ChatMessageType, StreamingMessage } from '@/types'

interface ChatPanelProps {
  /** Podcast job ID to chat about */
  jobId: string
  /** Whether the panel is visible */
  isVisible?: boolean
  /** Callback to close the panel */
  onClose?: () => void
  /** Whether to show voice input */
  enableVoice?: boolean
  /** Callback when user starts interacting (e.g., to pause video) */
  onInteraction?: () => void
}

/**
 * Interactive chat panel for podcast conversations.
 *
 * Provides a chat interface for users to ask questions about
 * the podcast content and receive AI responses.
 *
 * @param jobId - The podcast job ID for context
 * @param isVisible - Whether the panel is displayed
 * @param onClose - Callback to close the panel
 * @param enableVoice - Whether to enable voice input
 * @param onInteraction - Callback when user interacts
 */
export function ChatPanel({
  jobId,
  isVisible = true,
  onClose,
  enableVoice = false,
  onInteraction,
}: ChatPanelProps) {
  const {
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
  } = useInteractiveChat()

  const messagesEndRef = useRef<HTMLDivElement>(null)
  const [playingMessageId, setPlayingMessageId] = useState<string | null>(null)
  const audioRef = useRef<HTMLAudioElement | null>(null)

  // Start session when panel becomes visible
  useEffect(() => {
    if (isVisible && jobId && !sessionId) {
      startSession(jobId)
    }
  }, [isVisible, jobId, sessionId, startSession])

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, streamingMessage])

  // Cleanup audio on unmount
  useEffect(() => {
    return () => {
      if (audioRef.current) {
        audioRef.current.pause()
        audioRef.current = null
      }
    }
  }, [])

  /**
   * Handle sending a message.
   */
  const handleSend = useCallback(
    (text: string) => {
      onInteraction?.()
      sendMessage(text)
    },
    [sendMessage, onInteraction]
  )

  /**
   * Handle audio playback.
   */
  const handlePlayAudio = useCallback((url: string, messageId: string) => {
    // Stop current audio if playing
    if (audioRef.current) {
      audioRef.current.pause()
    }

    // If clicking the same message that's playing, stop it
    if (playingMessageId === messageId) {
      setPlayingMessageId(null)
      return
    }

    // Create new audio element
    const audio = new Audio(url)
    audioRef.current = audio

    audio.onplay = () => setPlayingMessageId(messageId)
    audio.onended = () => setPlayingMessageId(null)
    audio.onerror = () => setPlayingMessageId(null)

    audio.play().catch(() => setPlayingMessageId(null))
  }, [playingMessageId])

  /**
   * Handle closing the panel.
   */
  const handleClose = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause()
    }
    endSession()
    onClose?.()
  }, [endSession, onClose])

  if (!isVisible) return null

  // Combine regular messages with streaming message for display
  const allMessages: (ChatMessageType | StreamingMessage)[] = [...messages]

  return (
    <div className="flex flex-col h-full bg-background border-l border-border">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-border">
        <div className="flex items-center gap-2">
          <div
            className={`w-2 h-2 rounded-full ${
              isConnected ? 'bg-success' : 'bg-muted'
            }`}
          />
          <h3 className="font-medium text-sm">Chat with Podcast</h3>
        </div>
        <button
          className="p-1 rounded hover:bg-secondary transition-colors"
          onClick={handleClose}
          aria-label="Close chat"
        >
          <svg
            className="w-5 h-5 text-muted-foreground"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </button>
      </div>

      {/* Error banner */}
      {error && (
        <div className="px-4 py-2 bg-destructive/10 border-b border-destructive/20 flex items-center justify-between">
          <p className="text-xs text-destructive">{error}</p>
          <button
            className="text-xs text-destructive hover:underline"
            onClick={clearError}
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-4">
        {messages.length === 0 && !streamingMessage && (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <svg
              className="w-12 h-12 text-muted-foreground/50 mb-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
              />
            </svg>
            <p className="text-sm text-muted-foreground">
              {isLoading ? 'Starting conversation...' : 'Ask anything about the podcast'}
            </p>
          </div>
        )}

        {messages.map((message) => (
          <ChatMessage
            key={message.id}
            message={message}
            onPlayAudio={(url) => handlePlayAudio(url, message.id)}
            isPlaying={playingMessageId === message.id}
          />
        ))}

        {/* Streaming message */}
        {streamingMessage && (
          <ChatMessage
            message={{
              id: streamingMessage.id,
              role: 'assistant',
              content: streamingMessage.content,
              timestamp: new Date().toISOString(),
            }}
            isStreaming={!streamingMessage.isComplete}
          />
        )}

        {/* Loading indicator when waiting for response */}
        {isLoading && !streamingMessage && messages.length > 0 && (
          <div className="flex justify-start mb-4">
            <div className="bg-secondary rounded-2xl rounded-bl-md px-4 py-3">
              <div className="flex gap-1">
                <span className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce" />
                <span
                  className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce"
                  style={{ animationDelay: '0.1s' }}
                />
                <span
                  className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce"
                  style={{ animationDelay: '0.2s' }}
                />
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <ChatInput
        onSend={handleSend}
        disabled={!isConnected || isLoading}
        showVoiceInput={enableVoice}
        placeholder={
          !isConnected
            ? 'Connecting...'
            : isLoading
            ? 'Waiting for response...'
            : 'Ask about the podcast...'
        }
      />
    </div>
  )
}
