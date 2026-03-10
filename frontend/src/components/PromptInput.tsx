'use client'

interface PromptInputProps {
  /** Current prompt value */
  value: string
  /** Callback when prompt changes */
  onChange: (value: string) => void
  /** Placeholder text */
  placeholder?: string
  /** Whether input is disabled */
  disabled?: boolean
}

/**
 * Suno-style prompt input textarea.
 *
 * Larger textarea with transparent background, warm border,
 * and subtle char counter positioned bottom-right.
 *
 * @param value - Current input value
 * @param onChange - Change handler
 * @param placeholder - Placeholder text
 * @param disabled - Whether input is disabled
 */
export function PromptInput({
  value,
  onChange,
  placeholder = 'Describe your podcast topic...',
  disabled = false,
}: PromptInputProps) {
  return (
    <div className="relative">
      <textarea
        className="w-full min-h-[140px] rounded-lg border border-border bg-transparent px-4 pt-3 pb-10 text-sm placeholder:text-muted-foreground resize-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        placeholder={placeholder}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        rows={5}
      />
    </div>
  )
}
