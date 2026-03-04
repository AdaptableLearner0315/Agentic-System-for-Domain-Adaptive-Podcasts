'use client'

import { useState, useRef, useCallback, KeyboardEvent } from 'react'

interface ChatInputProps {
  /** Callback when message is submitted */
  onSend: (message: string) => void
  /** Whether input is disabled */
  disabled?: boolean
  /** Placeholder text */
  placeholder?: string
  /** Whether to show voice input button */
  showVoiceInput?: boolean
  /** Callback for voice input */
  onVoiceStart?: () => void
  /** Callback when voice input ends */
  onVoiceEnd?: () => void
  /** Whether voice is currently recording */
  isRecording?: boolean
}

/**
 * Chat text input with send button.
 *
 * Supports multiline input, Enter to send (Shift+Enter for newline),
 * and optional voice input button.
 *
 * @param onSend - Callback when message is submitted
 * @param disabled - Whether input is disabled
 * @param placeholder - Placeholder text
 * @param showVoiceInput - Whether to show voice input button
 * @param onVoiceStart - Callback when voice recording starts
 * @param onVoiceEnd - Callback when voice recording ends
 * @param isRecording - Whether voice is currently recording
 */
export function ChatInput({
  onSend,
  disabled = false,
  placeholder = 'Type a message...',
  showVoiceInput = false,
  onVoiceStart,
  onVoiceEnd,
  isRecording = false,
}: ChatInputProps) {
  const [text, setText] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  /**
   * Handle form submission.
   */
  const handleSubmit = useCallback(() => {
    const trimmed = text.trim()
    if (!trimmed || disabled) return

    onSend(trimmed)
    setText('')

    // Reset textarea height
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }
  }, [text, disabled, onSend])

  /**
   * Handle keyboard events (Enter to send).
   */
  const handleKeyDown = useCallback(
    (e: KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault()
        handleSubmit()
      }
    },
    [handleSubmit]
  )

  /**
   * Auto-resize textarea based on content.
   */
  const handleChange = useCallback((e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const target = e.target
    setText(target.value)

    // Auto-resize
    target.style.height = 'auto'
    target.style.height = `${Math.min(target.scrollHeight, 120)}px`
  }, [])

  /**
   * Handle voice button interaction.
   */
  const handleVoiceMouseDown = useCallback(() => {
    onVoiceStart?.()
  }, [onVoiceStart])

  const handleVoiceMouseUp = useCallback(() => {
    onVoiceEnd?.()
  }, [onVoiceEnd])

  return (
    <div className="flex items-end gap-2 p-3 border-t border-border bg-background">
      {/* Text input */}
      <div className="flex-1 relative">
        <textarea
          ref={textareaRef}
          className="
            w-full min-h-[44px] max-h-[120px] rounded-lg border border-border
            bg-secondary/50 px-4 py-3 text-sm placeholder:text-muted-foreground
            resize-none focus-visible:outline-none focus-visible:ring-2
            focus-visible:ring-ring disabled:opacity-50 disabled:cursor-not-allowed
          "
          placeholder={placeholder}
          value={text}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          disabled={disabled || isRecording}
          rows={1}
        />
      </div>

      {/* Voice input button */}
      {showVoiceInput && (
        <button
          className={`
            w-11 h-11 rounded-full flex items-center justify-center
            transition-all duration-150
            ${isRecording
              ? 'bg-destructive text-destructive-foreground scale-110 animate-pulse'
              : 'bg-secondary text-muted-foreground hover:text-foreground hover:bg-secondary/80'
            }
            disabled:opacity-50 disabled:cursor-not-allowed
          `}
          onMouseDown={handleVoiceMouseDown}
          onMouseUp={handleVoiceMouseUp}
          onMouseLeave={isRecording ? handleVoiceMouseUp : undefined}
          onTouchStart={handleVoiceMouseDown}
          onTouchEnd={handleVoiceMouseUp}
          disabled={disabled}
          aria-label={isRecording ? 'Release to send' : 'Hold to record'}
        >
          {isRecording ? (
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
              <circle cx="12" cy="12" r="8" />
            </svg>
          ) : (
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"
              />
            </svg>
          )}
        </button>
      )}

      {/* Send button */}
      <button
        className="
          w-11 h-11 rounded-full bg-primary text-primary-foreground
          flex items-center justify-center
          hover:bg-primary/90 transition-colors
          disabled:opacity-50 disabled:cursor-not-allowed
        "
        onClick={handleSubmit}
        disabled={disabled || !text.trim() || isRecording}
        aria-label="Send message"
      >
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
          />
        </svg>
      </button>
    </div>
  )
}
