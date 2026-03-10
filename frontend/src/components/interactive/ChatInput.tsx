'use client'

import { useState, useRef, useCallback, KeyboardEvent } from 'react'
import { VoiceExperience } from '@/components/voice'

interface ChatInputProps {
  /** Callback when message is submitted */
  onSend: (message: string) => void
  /** Whether input is disabled */
  disabled?: boolean
  /** Whether the system is connecting (shows indicator on voice button) */
  isConnecting?: boolean
  /** Placeholder text */
  placeholder?: string
  /** Whether to show voice input button */
  showVoiceInput?: boolean
  /** Job ID for voice transcription (required when showVoiceInput is true) */
  jobId?: string
  /** Callback when interaction starts (e.g., for pausing video) */
  onInteraction?: () => void
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
 * @param jobId - Job ID for voice transcription
 * @param onInteraction - Callback when interaction starts
 */
export function ChatInput({
  onSend,
  disabled = false,
  isConnecting = false,
  placeholder = 'Type a message...',
  showVoiceInput = false,
  jobId,
  onInteraction,
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
   * Handle voice transcription - auto-send as message.
   */
  const handleVoiceTranscription = useCallback(
    (transcribedText: string) => {
      if (transcribedText.trim()) {
        onSend(transcribedText.trim())
      }
    },
    [onSend]
  )

  /**
   * Handle voice interaction start.
   */
  const handleVoiceInteraction = useCallback(() => {
    onInteraction?.()
  }, [onInteraction])

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
          disabled={disabled}
          rows={1}
        />
      </div>

      {/* Voice input button - tap-to-talk */}
      {showVoiceInput && jobId && (
        <VoiceExperience
          jobId={jobId}
          onSend={handleVoiceTranscription}
          onInteraction={handleVoiceInteraction}
          disabled={disabled}
          isConnecting={isConnecting}
          layout="compact"
        />
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
        disabled={disabled || !text.trim()}
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
