'use client'

/**
 * Transcript preview component for real-time speech display.
 *
 * Shows the user's speech as it's being transcribed,
 * with visual distinction between final and interim text.
 */

import { useEffect, useRef } from 'react'

interface TranscriptPreviewProps {
  /** Final transcript text */
  finalText: string
  /** Interim (in-progress) transcript text */
  interimText?: string
  /** Whether transcription is active */
  isListening: boolean
  /** Maximum height before scrolling */
  maxHeight?: number
  /** Placeholder text when empty */
  placeholder?: string
  /** Whether to show confidence indicator */
  showConfidence?: boolean
  /** Confidence score (0-1) */
  confidence?: number
}

/**
 * Real-time transcript preview with streaming text.
 *
 * Displays transcribed speech with visual distinction between
 * finalized text and in-progress interim results.
 *
 * @example
 * ```tsx
 * <TranscriptPreview
 *   finalText={finalTranscript}
 *   interimText={interimTranscript}
 *   isListening={isListening}
 * />
 * ```
 */
export function TranscriptPreview({
  finalText,
  interimText = '',
  isListening,
  maxHeight = 80,
  placeholder = 'Start speaking...',
  showConfidence = false,
  confidence = 0,
}: TranscriptPreviewProps) {
  const containerRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom when text changes
  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight
    }
  }, [finalText, interimText])

  const hasText = finalText || interimText
  const isEmpty = !hasText && !isListening

  return (
    <div className="relative">
      {/* Main text container */}
      <div
        ref={containerRef}
        className={`
          px-4 py-3 rounded-lg overflow-y-auto text-sm
          ${isEmpty ? 'bg-secondary/30' : 'bg-secondary/50'}
          transition-colors duration-200
        `}
        style={{ maxHeight }}
      >
        {isEmpty ? (
          <span className="text-muted-foreground/50 italic">{placeholder}</span>
        ) : (
          <div className="space-y-1">
            {/* Final text */}
            {finalText && <span className="text-foreground">{finalText}</span>}

            {/* Interim text with typing indicator */}
            {interimText && (
              <span className="text-muted-foreground/70 italic">
                {finalText ? ' ' : ''}
                {interimText}
                <span className="inline-flex ml-1">
                  <span className="w-1 h-1 bg-muted-foreground/50 rounded-full animate-bounce" />
                </span>
              </span>
            )}

            {/* Listening indicator when no text yet */}
            {isListening && !hasText && (
              <span className="text-primary/70 flex items-center gap-2">
                <span className="flex gap-1">
                  <span className="w-1.5 h-1.5 bg-primary rounded-full animate-bounce" />
                  <span
                    className="w-1.5 h-1.5 bg-primary rounded-full animate-bounce"
                    style={{ animationDelay: '0.1s' }}
                  />
                  <span
                    className="w-1.5 h-1.5 bg-primary rounded-full animate-bounce"
                    style={{ animationDelay: '0.2s' }}
                  />
                </span>
                Listening...
              </span>
            )}
          </div>
        )}
      </div>

      {/* Confidence indicator */}
      {showConfidence && hasText && confidence > 0 && (
        <div className="absolute bottom-1 right-2 flex items-center gap-1">
          <div
            className={`w-2 h-2 rounded-full ${
              confidence > 0.8
                ? 'bg-success'
                : confidence > 0.5
                ? 'bg-amber-500'
                : 'bg-destructive/50'
            }`}
          />
          <span className="text-[10px] text-muted-foreground/50">
            {Math.round(confidence * 100)}%
          </span>
        </div>
      )}

      {/* Active indicator */}
      {isListening && (
        <div className="absolute top-0 left-0 right-0 h-0.5">
          <div className="h-full bg-primary/50 animate-pulse" />
        </div>
      )}
    </div>
  )
}

/**
 * Compact inline transcript for showing in other components.
 */
export function TranscriptInline({
  text,
  isActive,
}: {
  text: string
  isActive: boolean
}) {
  if (!text && !isActive) return null

  return (
    <div className="text-xs text-muted-foreground truncate max-w-[200px]">
      {text ? (
        <span className="italic">"{text}"</span>
      ) : isActive ? (
        <span className="animate-pulse">Listening...</span>
      ) : null}
    </div>
  )
}
