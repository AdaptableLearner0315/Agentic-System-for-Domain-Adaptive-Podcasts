'use client'

/**
 * Countdown ring component for visual silence countdown.
 *
 * Displays a circular progress indicator around the mic button
 * that fills as silence duration increases.
 */

import { useEffect, useState } from 'react'

interface CountdownRingProps {
  /** Current progress (0-1) */
  progress: number
  /** Ring size in pixels */
  size?: number
  /** Ring stroke width */
  strokeWidth?: number
  /** Whether the countdown is active */
  isActive?: boolean
  /** Ring color at start of countdown */
  startColor?: string
  /** Ring color at end of countdown */
  endColor?: string
  /** Background ring color */
  backgroundColor?: string
  /** Children to render in the center */
  children?: React.ReactNode
}

/**
 * Countdown ring with gradient color transition.
 *
 * Shows visual feedback for the silence detection countdown,
 * transitioning from blue to amber to green as it fills.
 *
 * @example
 * ```tsx
 * <CountdownRing progress={silenceProgress} isActive={state === 'countdown'}>
 *   <VoiceButton />
 * </CountdownRing>
 * ```
 */
export function CountdownRing({
  progress,
  size = 80,
  strokeWidth = 4,
  isActive = false,
  startColor = '#3b82f6', // blue-500
  endColor = '#22c55e', // green-500
  backgroundColor = 'rgba(255, 255, 255, 0.1)',
  children,
}: CountdownRingProps) {
  const [displayProgress, setDisplayProgress] = useState(0)

  // Smooth animation for progress changes
  useEffect(() => {
    if (!isActive) {
      setDisplayProgress(0)
      return
    }

    // Animate to target progress
    const animationDuration = 100 // ms
    const startProgress = displayProgress
    const delta = progress - startProgress
    const startTime = Date.now()

    const animate = () => {
      const elapsed = Date.now() - startTime
      const t = Math.min(elapsed / animationDuration, 1)
      // Ease out
      const eased = 1 - Math.pow(1 - t, 3)
      setDisplayProgress(startProgress + delta * eased)

      if (t < 1) {
        requestAnimationFrame(animate)
      }
    }

    requestAnimationFrame(animate)
  }, [progress, isActive])

  // Calculate SVG values
  const center = size / 2
  const radius = (size - strokeWidth) / 2
  const circumference = 2 * Math.PI * radius
  const strokeDashoffset = circumference * (1 - displayProgress)

  // Interpolate color based on progress
  const getColor = () => {
    if (displayProgress < 0.5) {
      // Blue to amber
      const t = displayProgress * 2
      return interpolateColor('#3b82f6', '#f59e0b', t)
    } else {
      // Amber to green
      const t = (displayProgress - 0.5) * 2
      return interpolateColor('#f59e0b', '#22c55e', t)
    }
  }

  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg
        className="absolute inset-0 -rotate-90"
        width={size}
        height={size}
        viewBox={`0 0 ${size} ${size}`}
      >
        {/* Background circle */}
        <circle
          cx={center}
          cy={center}
          r={radius}
          fill="none"
          stroke={backgroundColor}
          strokeWidth={strokeWidth}
        />

        {/* Progress circle */}
        {isActive && displayProgress > 0 && (
          <circle
            cx={center}
            cy={center}
            r={radius}
            fill="none"
            stroke={getColor()}
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            className="transition-all duration-100"
          />
        )}
      </svg>

      {/* Pulse effect when nearing completion */}
      {isActive && displayProgress > 0.8 && (
        <div
          className="absolute inset-0 rounded-full animate-ping"
          style={{
            backgroundColor: 'rgba(34, 197, 94, 0.2)',
            animationDuration: '1s',
          }}
        />
      )}

      {/* Center content */}
      <div className="absolute inset-0 flex items-center justify-center">
        {children}
      </div>
    </div>
  )
}

/**
 * Interpolate between two hex colors.
 */
function interpolateColor(color1: string, color2: string, t: number): string {
  const r1 = parseInt(color1.slice(1, 3), 16)
  const g1 = parseInt(color1.slice(3, 5), 16)
  const b1 = parseInt(color1.slice(5, 7), 16)

  const r2 = parseInt(color2.slice(1, 3), 16)
  const g2 = parseInt(color2.slice(3, 5), 16)
  const b2 = parseInt(color2.slice(5, 7), 16)

  const r = Math.round(r1 + (r2 - r1) * t)
  const g = Math.round(g1 + (g2 - g1) * t)
  const b = Math.round(b1 + (b2 - b1) * t)

  return `#${r.toString(16).padStart(2, '0')}${g.toString(16).padStart(2, '0')}${b.toString(16).padStart(2, '0')}`
}
