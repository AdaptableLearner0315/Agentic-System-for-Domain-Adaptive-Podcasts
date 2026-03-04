'use client'

import { useState } from 'react'
import type { ChatMessage as ChatMessageType } from '@/types'

interface ChatMessageProps {
  /** The message to display */
  message: ChatMessageType
  /** Whether this is a streaming message (incomplete) */
  isStreaming?: boolean
  /** Callback when audio play is requested */
  onPlayAudio?: (url: string) => void
  /** Whether audio is currently playing for this message */
  isPlaying?: boolean
}

/**
 * Individual chat message bubble.
 *
 * Displays user or assistant messages with appropriate styling,
 * optional audio playback controls, and timestamp.
 *
 * @param message - The message data
 * @param isStreaming - Whether the message is still being streamed
 * @param onPlayAudio - Callback for audio playback
 * @param isPlaying - Whether this message's audio is playing
 */
export function ChatMessage({
  message,
  isStreaming = false,
  onPlayAudio,
  isPlaying = false,
}: ChatMessageProps) {
  const [showTimestamp, setShowTimestamp] = useState(false)
  const isUser = message.role === 'user'
  const isAssistant = message.role === 'assistant'

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp)
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }

  return (
    <div
      className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}
      onClick={() => setShowTimestamp(!showTimestamp)}
    >
      <div
        className={`
          max-w-[85%] rounded-2xl px-4 py-3
          ${isUser
            ? 'bg-primary text-primary-foreground rounded-br-md'
            : 'bg-secondary text-foreground rounded-bl-md'
          }
          ${isStreaming ? 'animate-pulse' : ''}
        `}
      >
        {/* Message content */}
        <p className="text-sm whitespace-pre-wrap break-words">
          {message.content}
          {isStreaming && (
            <span className="inline-block w-2 h-4 ml-1 bg-current animate-pulse" />
          )}
        </p>

        {/* Audio playback button (for assistant messages with audio) */}
        {isAssistant && message.audio_url && !isStreaming && (
          <button
            className={`
              mt-2 flex items-center gap-2 text-xs
              ${isPlaying
                ? 'text-primary'
                : 'text-muted-foreground hover:text-foreground'
              }
              transition-colors
            `}
            onClick={(e) => {
              e.stopPropagation()
              onPlayAudio?.(message.audio_url!)
            }}
          >
            {isPlaying ? (
              <>
                <svg
                  className="w-4 h-4 animate-pulse"
                  fill="currentColor"
                  viewBox="0 0 24 24"
                >
                  <rect x="6" y="5" width="4" height="14" rx="1" />
                  <rect x="14" y="5" width="4" height="14" rx="1" />
                </svg>
                Playing...
              </>
            ) : (
              <>
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M8 5v14l11-7z" />
                </svg>
                Play audio
              </>
            )}
          </button>
        )}

        {/* Timestamp (shown on click) */}
        {showTimestamp && (
          <p className="text-xs text-muted-foreground mt-2 opacity-70">
            {formatTime(message.timestamp)}
          </p>
        )}
      </div>
    </div>
  )
}
