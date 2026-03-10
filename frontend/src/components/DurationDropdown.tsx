'use client'

import { DurationOption } from '@/types'

interface DurationDropdownProps {
  duration: DurationOption
  onDurationChange: (duration: DurationOption) => void
  disabled?: boolean
}

const DURATION_OPTIONS: Array<{ value: DurationOption; label: string }> = [
  { value: 'auto', label: 'Auto' },
  { value: 3, label: '3 min' },
  { value: 5, label: '5 min' },
  { value: 10, label: '10 min' },
  { value: 15, label: '15 min' },
  { value: 20, label: '20 min' },
]

export function DurationDropdown({ duration, onDurationChange, disabled }: DurationDropdownProps) {
  return (
    <select
      value={String(duration)}
      onChange={(e) => {
        const val = e.target.value
        onDurationChange(val === 'auto' ? 'auto' : Number(val) as DurationOption)
      }}
      disabled={disabled}
      className="px-2.5 py-1 text-xs font-medium rounded-md bg-secondary/80 text-muted-foreground
                 hover:bg-secondary hover:text-foreground transition-colors
                 disabled:opacity-40 disabled:cursor-not-allowed
                 border-none outline-none cursor-pointer appearance-none
                 pr-6 bg-no-repeat bg-[length:12px] bg-[right_6px_center]"
      style={{
        backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='%239ca3af'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M19 9l-7 7-7-7'/%3E%3C/svg%3E")`,
      }}
      title="Target duration"
    >
      {DURATION_OPTIONS.map((opt) => (
        <option key={String(opt.value)} value={String(opt.value)}>
          {opt.label}
        </option>
      ))}
    </select>
  )
}
