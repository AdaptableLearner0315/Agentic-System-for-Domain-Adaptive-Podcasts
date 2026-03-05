'use client'

/**
 * Voice visualizer component for audio waveform display.
 *
 * Shows animated bars that respond to audio input levels,
 * providing visual feedback during recording.
 */

import { useEffect, useState, useRef } from 'react'
import type { VoiceState } from '@/types/interactive'

interface VoiceVisualizerProps {
  /** Current voice state */
  state: VoiceState
  /** Current audio level (0-1) */
  audioLevel: number
  /** Number of bars to display */
  barCount?: number
  /** Height of the visualizer */
  height?: number
  /** Width of the visualizer */
  width?: number
  /** Bar color */
  color?: string
  /** Whether to show labels */
  showStatus?: boolean
  /** Recording duration in seconds */
  duration?: number
}

/**
 * Audio waveform visualizer with state-aware animations.
 *
 * Displays animated bars during recording that respond to audio levels,
 * and shows different animations for other voice states.
 *
 * @example
 * ```tsx
 * <VoiceVisualizer
 *   state={voiceState}
 *   audioLevel={level}
 *   duration={recordingDuration}
 * />
 * ```
 */
export function VoiceVisualizer({
  state,
  audioLevel,
  barCount = 5,
  height = 40,
  width = 100,
  color,
  showStatus = true,
  duration = 0,
}: VoiceVisualizerProps) {
  const [barHeights, setBarHeights] = useState<number[]>(Array(barCount).fill(0.1))
  const animationRef = useRef<number | null>(null)
  const lastUpdateRef = useRef<number>(0)

  // Determine color based on state
  const getColor = (): string => {
    if (color) return color
    switch (state) {
      case 'recording':
        return '#ef4444' // red-500
      case 'paused':
        return '#f59e0b' // amber-500
      case 'listening':
        return '#3b82f6' // blue-500
      case 'speaking':
        return '#22c55e' // green-500
      default:
        return '#6b7280' // gray-500
    }
  }

  // Update bar heights based on audio level
  useEffect(() => {
    if (state !== 'recording' && state !== 'paused') {
      // Show idle animation for non-recording states
      if (state === 'listening') {
        const interval = setInterval(() => {
          setBarHeights(
            Array(barCount)
              .fill(0)
              .map(() => 0.1 + Math.random() * 0.2)
          )
        }, 300)
        return () => clearInterval(interval)
      }

      if (state === 'speaking') {
        const interval = setInterval(() => {
          setBarHeights(
            Array(barCount)
              .fill(0)
              .map((_, i) => {
                const phase = (Date.now() / 200 + i) % (Math.PI * 2)
                return 0.3 + Math.sin(phase) * 0.4
              })
          )
        }, 50)
        return () => clearInterval(interval)
      }

      // Idle state - flat bars
      setBarHeights(Array(barCount).fill(0.1))
      return
    }

    // Recording/paused - animate based on audio level
    const updateBars = () => {
      const now = Date.now()
      if (now - lastUpdateRef.current < 50) {
        animationRef.current = requestAnimationFrame(updateBars)
        return
      }
      lastUpdateRef.current = now

      setBarHeights((prev) =>
        prev.map((h, i) => {
          // Add variation to each bar
          const variation = Math.sin(now / 100 + i * 1.5) * 0.15
          const target = Math.min(1, audioLevel * 1.5 + variation)
          // Smooth interpolation
          return h + (target - h) * 0.3
        })
      )

      animationRef.current = requestAnimationFrame(updateBars)
    }

    animationRef.current = requestAnimationFrame(updateBars)

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current)
      }
    }
  }, [state, audioLevel, barCount])

  const barWidth = (width - (barCount - 1) * 4) / barCount
  const stateColor = getColor()

  return (
    <div className="flex flex-col items-center gap-2">
      {/* Waveform bars */}
      <div
        className="flex items-center justify-center gap-1"
        style={{ height, width }}
        role="img"
        aria-label={`Audio visualizer: ${state}`}
      >
        {barHeights.map((h, i) => (
          <div
            key={i}
            className="rounded-full transition-all duration-75"
            style={{
              width: barWidth,
              height: Math.max(4, h * height),
              backgroundColor: stateColor,
              opacity: 0.6 + h * 0.4,
            }}
          />
        ))}
      </div>

      {/* Status text */}
      {showStatus && (
        <div className="text-xs text-center">
          {state === 'recording' && (
            <span className="text-destructive font-medium">
              Recording {formatDuration(duration)}
            </span>
          )}
          {state === 'paused' && (
            <span className="text-amber-500">Still listening...</span>
          )}
          {state === 'listening' && (
            <span className="text-primary animate-pulse">Listening...</span>
          )}
          {state === 'speaking' && (
            <span className="text-success">Speaking...</span>
          )}
          {state === 'processing' && (
            <span className="text-muted-foreground">Processing...</span>
          )}
          {state === 'idle' && (
            <span className="text-muted-foreground">Tap to speak</span>
          )}
        </div>
      )}
    </div>
  )
}

/**
 * Format duration as mm:ss.
 */
function formatDuration(seconds: number): string {
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}
