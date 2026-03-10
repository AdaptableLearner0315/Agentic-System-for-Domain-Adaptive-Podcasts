'use client'

/**
 * Multi-state voice button for tap-to-talk interaction.
 *
 * Displays different visual states including idle, listening (breathing),
 * recording (waveform), and processing (spinner).
 */

import { useCallback } from 'react'
import type { VoiceState } from '@/types/interactive'

interface VoiceButtonProps {
  /** Current voice state */
  state: VoiceState
  /** Audio level for visualization (0-1) */
  audioLevel?: number
  /** Countdown progress (0-1) */
  countdownProgress?: number
  /** Whether the button is disabled */
  disabled?: boolean
  /** Whether the system is connecting (shows connecting indicator) */
  isConnecting?: boolean
  /** Click handler */
  onClick?: () => void
  /** Size variant */
  size?: 'sm' | 'md' | 'lg'
}

const SIZE_CLASSES = {
  sm: 'w-12 h-12',
  md: 'w-16 h-16',
  lg: 'w-20 h-20',
}

const ICON_SIZES = {
  sm: 'w-5 h-5',
  md: 'w-7 h-7',
  lg: 'w-9 h-9',
}

/**
 * Voice button with state-aware visuals.
 *
 * Shows breathing animation when listening, audio level visualization
 * when recording, and spinner when processing.
 *
 * @example
 * ```tsx
 * <VoiceButton
 *   state={voiceState}
 *   audioLevel={level}
 *   onClick={() => send('tap')}
 * />
 * ```
 */
export function VoiceButton({
  state,
  audioLevel = 0,
  countdownProgress = 0,
  disabled = false,
  isConnecting = false,
  onClick,
  size = 'md',
}: VoiceButtonProps) {
  const handleClick = useCallback(() => {
    if (!disabled) {
      onClick?.()
    }
  }, [disabled, onClick])

  const sizeClass = SIZE_CLASSES[size]
  const iconSize = ICON_SIZES[size]

  // State-based styling
  const getStateStyles = (): string => {
    switch (state) {
      case 'idle':
        return 'bg-secondary text-muted-foreground hover:bg-secondary/80 hover:text-foreground'
      case 'listening':
        return 'bg-primary/20 text-primary border-2 border-primary/50'
      case 'recording':
        return 'bg-destructive text-destructive-foreground'
      case 'paused':
        return 'bg-amber-500/20 text-amber-500 border-2 border-amber-500/50'
      case 'countdown':
        return 'bg-amber-500/30 text-amber-600 border-2 border-amber-500'
      case 'processing':
        return 'bg-primary/50 text-primary-foreground'
      case 'speaking':
        return 'bg-success/20 text-success border-2 border-success/50'
      default:
        return 'bg-secondary text-muted-foreground'
    }
  }

  // Render icon based on state
  const renderIcon = () => {
    // Show connecting spinner when connecting
    if (isConnecting) {
      return (
        <svg className={`${iconSize} animate-spin`} fill="none" viewBox="0 0 24 24">
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
      )
    }

    switch (state) {
      case 'processing':
        return (
          <svg className={`${iconSize} animate-spin`} fill="none" viewBox="0 0 24 24">
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
        )

      case 'recording':
      case 'paused':
        return (
          <svg className={iconSize} fill="currentColor" viewBox="0 0 24 24">
            <circle cx="12" cy="12" r="8" />
          </svg>
        )

      case 'speaking':
        return (
          <svg className={iconSize} fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z"
            />
          </svg>
        )

      default:
        return (
          <svg className={iconSize} fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"
            />
          </svg>
        )
    }
  }

  // Calculate audio level ring scale
  const audioRingScale = 1 + audioLevel * 0.4

  return (
    <button
      className={`
        relative ${sizeClass} rounded-full flex items-center justify-center
        transition-all duration-200 ease-out
        ${getStateStyles()}
        ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
      `}
      onClick={handleClick}
      disabled={disabled}
      aria-label={isConnecting ? 'Connecting...' : getAriaLabel(state)}
    >
      {/* Audio level ring (visible when recording) */}
      {(state === 'recording' || state === 'paused') && audioLevel > 0 && (
        <div
          className="absolute inset-0 rounded-full border-4 border-destructive/50 transition-transform duration-75"
          style={{
            transform: `scale(${audioRingScale})`,
            opacity: 0.3 + audioLevel * 0.7,
          }}
        />
      )}

      {/* Breathing animation (listening state) */}
      {state === 'listening' && (
        <div className="absolute inset-0 rounded-full bg-primary/10 animate-pulse" />
      )}

      {/* Speaking pulse */}
      {state === 'speaking' && (
        <>
          <div
            className="absolute inset-0 rounded-full bg-success/20 animate-ping"
            style={{ animationDuration: '1.5s' }}
          />
          <div
            className="absolute inset-0 rounded-full bg-success/10 animate-pulse"
            style={{ animationDuration: '1s' }}
          />
        </>
      )}

      {/* Countdown pulse */}
      {state === 'countdown' && (
        <div
          className="absolute inset-0 rounded-full bg-amber-500/20"
          style={{
            animation: 'pulse 1s ease-in-out infinite',
            transform: `scale(${1 + countdownProgress * 0.1})`,
          }}
        />
      )}

      {/* Icon */}
      <div className="relative z-10">{renderIcon()}</div>
    </button>
  )
}

/**
 * Get accessible label for current state.
 */
function getAriaLabel(state: VoiceState): string {
  switch (state) {
    case 'idle':
      return 'Tap to speak'
    case 'listening':
      return 'Listening for speech...'
    case 'recording':
      return 'Recording... Tap to send'
    case 'paused':
      return 'Paused. Tap to send or continue speaking'
    case 'countdown':
      return 'Sending soon... Tap to send now'
    case 'processing':
      return 'Processing your message...'
    case 'speaking':
      return 'AI is speaking. Tap to stop'
    default:
      return 'Voice input'
  }
}
