'use client'

import { useRef, useEffect, useState, useCallback } from 'react'
import { ChatMessage } from './ChatMessage'
import { ChatInput } from './ChatInput'
import { useInteractiveChat } from '@/hooks/useInteractiveChat'
import { VoiceExperience, MemoryConsentModal, useMemoryConsent } from '@/components/voice'
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

  // Voice mode state
  const [voiceMode, setVoiceMode] = useState(false)
  const [isAiSpeaking, setIsAiSpeaking] = useState(false)

  // Memory consent
  const { showModal, setShowModal, handleConsent } = useMemoryConsent()

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
      setIsAiSpeaking(false)
      return
    }

    // Create new audio element
    const audio = new Audio(url)
    audioRef.current = audio

    audio.onplay = () => {
      setPlayingMessageId(messageId)
      setIsAiSpeaking(true)
    }
    audio.onended = () => {
      setPlayingMessageId(null)
      setIsAiSpeaking(false)
    }
    audio.onerror = () => {
      setPlayingMessageId(null)
      setIsAiSpeaking(false)
    }

    audio.play().catch(() => {
      setPlayingMessageId(null)
      setIsAiSpeaking(false)
    })
  }, [playingMessageId])

  /**
   * Handle closing the panel.
   */
  const handleClose = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause()
    }
    onClose?.()
  }, [onClose])

  /**
   * Stop audio playback.
   */
  const handleStopAudio = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause()
      audioRef.current = null
    }
    setPlayingMessageId(null)
    setIsAiSpeaking(false)
  }, [])

  /**
   * Toggle voice mode.
   */
  const toggleVoiceMode = useCallback(() => {
    setVoiceMode((prev) => !prev)
  }, [])

  if (!isVisible) return null

  // Combine regular messages with streaming message for display
  const allMessages: (ChatMessageType | StreamingMessage)[] = [...messages]

  return (
    <div className="flex flex-col h-full bg-background">
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
        <div className="flex items-center gap-2">
          {/* Voice mode toggle */}
          {enableVoice && (
            <button
              className={`p-1.5 rounded transition-colors ${
                voiceMode
                  ? 'bg-primary/20 text-primary'
                  : 'hover:bg-secondary text-muted-foreground hover:text-foreground'
              }`}
              onClick={toggleVoiceMode}
              aria-label={voiceMode ? 'Switch to text mode' : 'Switch to voice mode'}
              title={voiceMode ? 'Text mode' : 'Voice mode'}
            >
              <svg
                className="w-5 h-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"
                />
              </svg>
            </button>
          )}
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
      {voiceMode && enableVoice ? (
        <div className="p-3 border-t border-border bg-background">
          <VoiceExperience
            jobId={jobId}
            onSend={handleSend}
            onInteraction={onInteraction}
            disabled={!isConnected || isLoading}
            isConnecting={!isConnected}
            aiResponseText={streamingMessage?.content}
            isAiProcessing={isLoading}
            isAiSpeaking={isAiSpeaking}
            onStopAudio={handleStopAudio}
            layout="compact"
          />
        </div>
      ) : (
        <ChatInput
          onSend={handleSend}
          disabled={!isConnected || isLoading}
          isConnecting={!isConnected}
          showVoiceInput={enableVoice && !voiceMode}
          jobId={jobId}
          onInteraction={onInteraction}
          placeholder={
            !isConnected
              ? 'Connecting...'
              : isLoading
              ? 'Waiting for response...'
              : enableVoice
              ? 'Type or tap mic to speak...'
              : 'Ask about the podcast...'
          }
        />
      )}

      {/* Memory Consent Modal */}
      <MemoryConsentModal
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        onConsent={handleConsent}
      />
    </div>
  )
}
