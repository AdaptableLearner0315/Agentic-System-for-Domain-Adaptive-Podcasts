'use client'

/**
 * Voice avatar component for AI speaking visualization.
 *
 * Displays an animated avatar when the AI is speaking,
 * with visual feedback for audio activity.
 */

import { useEffect, useState } from 'react'

interface VoiceAvatarProps {
  /** Whether the AI is currently speaking */
  isSpeaking: boolean
  /** Current text being spoken */
  text?: string
  /** Avatar size */
  size?: 'sm' | 'md' | 'lg'
  /** Whether to show the text */
  showText?: boolean
  /** Avatar name */
  name?: string
}

const SIZE_CLASSES = {
  sm: 'w-10 h-10',
  md: 'w-14 h-14',
  lg: 'w-20 h-20',
}

const TEXT_SIZES = {
  sm: 'text-lg',
  md: 'text-2xl',
  lg: 'text-4xl',
}

/**
 * Animated AI avatar for voice responses.
 *
 * Shows a pulsing avatar with sound wave effects
 * when the AI is speaking.
 *
 * @example
 * ```tsx
 * <VoiceAvatar
 *   isSpeaking={state === 'speaking'}
 *   text={responseText}
 * />
 * ```
 */
export function VoiceAvatar({
  isSpeaking,
  text,
  size = 'md',
  showText = true,
  name = 'Nell',
}: VoiceAvatarProps) {
  const [wavePhase, setWavePhase] = useState(0)

  // Animate wave effect when speaking
  useEffect(() => {
    if (!isSpeaking) {
      setWavePhase(0)
      return
    }

    const interval = setInterval(() => {
      setWavePhase((prev) => (prev + 1) % 360)
    }, 50)

    return () => clearInterval(interval)
  }, [isSpeaking])

  const sizeClass = SIZE_CLASSES[size]
  const textSize = TEXT_SIZES[size]

  // Generate wave bars for speaking animation
  const renderWaves = () => {
    const bars = 3
    return (
      <div className="flex items-center gap-0.5 h-3">
        {Array.from({ length: bars }).map((_, i) => {
          const phase = (wavePhase + i * 40) * (Math.PI / 180)
          const height = 4 + Math.sin(phase) * 8
          return (
            <div
              key={i}
              className="w-1 bg-success rounded-full transition-all duration-75"
              style={{ height: `${height}px` }}
            />
          )
        })}
      </div>
    )
  }

  return (
    <div className="flex items-start gap-3">
      {/* Avatar */}
      <div className="relative flex-shrink-0">
        {/* Outer glow when speaking */}
        {isSpeaking && (
          <div
            className={`absolute inset-0 ${sizeClass} rounded-full bg-success/20 animate-ping`}
            style={{ animationDuration: '2s' }}
          />
        )}

        {/* Avatar circle */}
        <div
          className={`
            relative ${sizeClass} rounded-full flex items-center justify-center
            ${isSpeaking ? 'bg-success/20 border-2 border-success/50' : 'bg-secondary'}
            transition-all duration-300
          `}
        >
          {/* Initial or icon */}
          <span className={`${textSize} font-bold ${isSpeaking ? 'text-success' : 'text-muted-foreground'}`}>
            {name.charAt(0)}
          </span>

          {/* Speaking indicator */}
          {isSpeaking && (
            <div className="absolute -bottom-1 -right-1 bg-background rounded-full p-0.5">
              {renderWaves()}
            </div>
          )}
        </div>
      </div>

      {/* Text content */}
      {showText && text && (
        <div className="flex-1 min-w-0">
          <div className="text-xs text-muted-foreground mb-1 flex items-center gap-2">
            <span className="font-medium">{name}</span>
            {isSpeaking && (
              <span className="text-success text-[10px] flex items-center gap-1">
                <span className="w-1.5 h-1.5 bg-success rounded-full animate-pulse" />
                Speaking
              </span>
            )}
          </div>
          <div className="text-sm text-foreground">
            {text}
            {isSpeaking && (
              <span className="inline-block w-2 h-4 bg-foreground/50 ml-0.5 animate-pulse" />
            )}
          </div>
        </div>
      )}
    </div>
  )
}

/**
 * Compact speaking indicator without avatar.
 */
export function SpeakingIndicator({ isSpeaking }: { isSpeaking: boolean }) {
  if (!isSpeaking) return null

  return (
    <div className="flex items-center gap-2 text-xs text-success">
      <div className="flex items-center gap-0.5">
        {[0, 1, 2].map((i) => (
          <div
            key={i}
            className="w-1 bg-success rounded-full animate-pulse"
            style={{
              height: `${8 + Math.random() * 8}px`,
              animationDelay: `${i * 0.1}s`,
            }}
          />
        ))}
      </div>
      <span>Nell is speaking...</span>
    </div>
  )
}
