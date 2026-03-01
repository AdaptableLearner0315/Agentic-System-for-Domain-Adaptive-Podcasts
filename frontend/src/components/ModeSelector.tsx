'use client'

import { PipelineMode } from '@/types'

interface ModeSelectorProps {
  /** Currently selected mode */
  mode: PipelineMode
  /** Callback when mode changes */
  onModeChange: (mode: PipelineMode) => void
  /** Whether selector is disabled */
  disabled?: boolean
}

/**
 * Compact pill toggle for Normal/Pro pipeline modes.
 *
 * Suno AI-style toggle with two options inside a rounded container.
 *
 * @param mode - Currently selected mode
 * @param onModeChange - Mode change handler
 * @param disabled - Whether selector is disabled
 */
export function ModeSelector({
  mode,
  onModeChange,
  disabled = false,
}: ModeSelectorProps) {
  const options = [
    { id: 'normal' as PipelineMode, label: 'Normal', sub: '~2 min' },
    { id: 'pro' as PipelineMode, label: 'Pro', sub: '~6 min' },
  ]

  return (
    <div
      className={`
        inline-flex rounded-full bg-secondary p-1
        ${disabled ? 'opacity-50 pointer-events-none' : ''}
      `}
    >
      {options.map((opt) => {
        const isSelected = mode === opt.id
        return (
          <button
            key={opt.id}
            className={`
              relative px-5 py-2 rounded-full text-sm font-medium transition-all duration-200
              ${isSelected
                ? 'bg-primary text-primary-foreground shadow-md'
                : 'text-muted-foreground hover:text-foreground'
              }
            `}
            onClick={() => onModeChange(opt.id)}
            disabled={disabled}
          >
            {opt.label}
            <span className={`ml-1.5 text-xs ${isSelected ? 'opacity-80' : 'opacity-60'}`}>
              {opt.sub}
            </span>
          </button>
        )
      })}
    </div>
  )
}
