'use client'

import { DurationOption } from '@/types'

interface DurationSelectorProps {
  /** Currently selected duration option */
  duration: DurationOption
  /** Callback when duration changes */
  onDurationChange: (duration: DurationOption) => void
  /** Whether selector is disabled */
  disabled?: boolean
}

/**
 * Duration options with labels and descriptions.
 */
const DURATION_OPTIONS: Array<{
  value: DurationOption
  label: string
  description: string
}> = [
  { value: 'auto', label: 'Auto', description: 'Based on content' },
  { value: 3, label: '3 min', description: 'Quick' },
  { value: 5, label: '5 min', description: 'Short' },
  { value: 10, label: '10 min', description: 'Standard' },
  { value: 15, label: '15 min', description: 'In-depth' },
  { value: 20, label: '20 min', description: 'Extended' },
]

/**
 * Pill-style selector for target podcast duration.
 *
 * Allows users to specify how long they want their generated podcast to be.
 * "Auto" option extracts duration from prompt or uses 10-minute default.
 *
 * @param duration - Currently selected duration
 * @param onDurationChange - Duration change handler
 * @param disabled - Whether selector is disabled
 */
export function DurationSelector({
  duration,
  onDurationChange,
  disabled = false,
}: DurationSelectorProps) {
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <span className="text-xs text-muted-foreground">Duration</span>
        <span className="text-xs text-muted-foreground">
          {duration === 'auto' ? 'Auto-detect' : `${duration} minutes`}
        </span>
      </div>
      <div
        className={`
          flex flex-wrap gap-2
          ${disabled ? 'opacity-50 pointer-events-none' : ''}
        `}
      >
        {DURATION_OPTIONS.map((opt) => {
          const isSelected = duration === opt.value
          return (
            <button
              key={String(opt.value)}
              type="button"
              className={`
                px-3 py-1.5 rounded-full text-xs font-medium transition-all duration-200
                ${isSelected
                  ? 'bg-primary text-primary-foreground shadow-sm'
                  : 'bg-secondary text-muted-foreground hover:text-foreground hover:bg-secondary/80'
                }
              `}
              onClick={() => onDurationChange(opt.value)}
              disabled={disabled}
              title={opt.description}
            >
              {opt.label}
            </button>
          )
        })}
      </div>
    </div>
  )
}
