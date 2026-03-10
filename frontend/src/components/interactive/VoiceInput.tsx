'use client'

import { useCallback, useState } from 'react'
import { useVoiceRecording } from '@/hooks/useVoiceRecording'
import { sendVoiceMessage } from '@/lib/api'

interface VoiceInputProps {
  /** Podcast job ID for the session */
  jobId: string
  /** Callback when transcription is ready */
  onTranscription: (text: string) => void
  /** Whether voice input is disabled */
  disabled?: boolean
  /** Callback when recording starts */
  onRecordingStart?: () => void
  /** Callback when recording ends */
  onRecordingEnd?: () => void
}

/**
 * Push-to-talk voice input button.
 *
 * Hold the button to record, release to transcribe.
 *
 * @param jobId - Podcast job ID
 * @param onTranscription - Callback with transcribed text
 * @param disabled - Whether input is disabled
 */
export function VoiceInput({
  jobId,
  onTranscription,
  disabled = false,
  onRecordingStart,
  onRecordingEnd,
}: VoiceInputProps) {
  const {
    isRecording,
    audioLevel,
    hasPermission,
    duration,
    startRecording,
    stopRecording,
    requestPermission,
    error: recordingError,
  } = useVoiceRecording()

  const [isTranscribing, setIsTranscribing] = useState(false)
  const [error, setError] = useState<string | null>(null)

  /**
   * Handle mouse/touch down - start recording.
   */
  const handlePressStart = useCallback(async () => {
    if (disabled || isTranscribing) return

    setError(null)

    // Request permission if needed
    if (!hasPermission) {
      const granted = await requestPermission()
      if (!granted) return
    }

    onRecordingStart?.()
    await startRecording()
  }, [disabled, isTranscribing, hasPermission, requestPermission, startRecording, onRecordingStart])

  /**
   * Handle mouse/touch up - stop recording and transcribe.
   */
  const handlePressEnd = useCallback(async () => {
    if (!isRecording) return

    const blob = await stopRecording()
    onRecordingEnd?.()

    if (!blob) {
      setError('No audio recorded')
      return
    }

    // Check minimum duration (0.5 seconds)
    if (duration < 0.5) {
      setError('Recording too short')
      return
    }

    setIsTranscribing(true)
    setError(null)

    try {
      const result = await sendVoiceMessage(jobId, blob, true)

      if (result.transcription) {
        onTranscription(result.transcription)
      } else {
        setError('No speech detected')
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Transcription failed')
    } finally {
      setIsTranscribing(false)
    }
  }, [isRecording, stopRecording, duration, jobId, onTranscription, onRecordingEnd])

  /**
   * Format duration for display.
   */
  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  const displayError = error || recordingError

  return (
    <div className="flex flex-col items-center gap-2">
      {/* Main button */}
      <button
        className={`
          relative w-16 h-16 rounded-full flex items-center justify-center
          transition-all duration-150
          ${isRecording
            ? 'bg-destructive text-destructive-foreground scale-110'
            : isTranscribing
            ? 'bg-primary/50 text-primary-foreground'
            : 'bg-primary text-primary-foreground hover:bg-primary/90'
          }
          disabled:opacity-50 disabled:cursor-not-allowed
        `}
        onMouseDown={handlePressStart}
        onMouseUp={handlePressEnd}
        onMouseLeave={isRecording ? handlePressEnd : undefined}
        onTouchStart={(e) => {
          e.preventDefault()
          handlePressStart()
        }}
        onTouchEnd={(e) => {
          e.preventDefault()
          handlePressEnd()
        }}
        disabled={disabled || isTranscribing}
        aria-label={isRecording ? 'Release to send' : 'Hold to record'}
      >
        {/* Audio level visualizer (ring around button) */}
        {isRecording && (
          <div
            className="absolute inset-0 rounded-full border-4 border-destructive animate-pulse"
            style={{
              transform: `scale(${1 + audioLevel * 0.3})`,
              opacity: 0.5 + audioLevel * 0.5,
            }}
          />
        )}

        {/* Icon */}
        {isTranscribing ? (
          <svg className="w-8 h-8 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
        ) : isRecording ? (
          <svg className="w-8 h-8" fill="currentColor" viewBox="0 0 24 24">
            <circle cx="12" cy="12" r="8" />
          </svg>
        ) : (
          <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"
            />
          </svg>
        )}
      </button>

      {/* Status text */}
      <div className="text-xs text-center">
        {isRecording ? (
          <span className="text-destructive font-medium">
            Recording... {formatDuration(duration)}
          </span>
        ) : isTranscribing ? (
          <span className="text-primary">Transcribing...</span>
        ) : displayError ? (
          <span className="text-destructive">{displayError}</span>
        ) : (
          <span className="text-muted-foreground">Hold to speak</span>
        )}
      </div>
    </div>
  )
}
