'use client'

import type { JobStatus } from '@/types'

interface FilterBarProps {
  currentFilter: JobStatus | null
  onFilterChange: (status: JobStatus | null) => void
}

/**
 * Configuration for a filter option button.
 * @property label - Display text for the filter button
 * @property value - JobStatus to filter by, or null for "All"
 */
interface FilterOption {
  label: string
  value: JobStatus | null
}

const filters: FilterOption[] = [
  { label: 'All', value: null },
  { label: 'Completed', value: 'completed' },
  { label: 'Running', value: 'running' },
  { label: 'Failed', value: 'failed' },
  { label: 'Cancelled', value: 'cancelled' },
]

/**
 * Filter bar component for filtering jobs by status.
 */
export function FilterBar({ currentFilter, onFilterChange }: FilterBarProps) {
  return (
    <div className="flex items-center gap-1 flex-wrap">
      <span className="text-sm text-muted-foreground mr-2">Filter:</span>
      {filters.map((filter) => (
        <button
          key={filter.value ?? 'all'}
          onClick={() => onFilterChange(filter.value)}
          className={`px-3 py-1.5 text-sm font-medium rounded-lg transition-colors ${
            currentFilter === filter.value
              ? 'bg-primary/10 text-primary'
              : 'text-muted-foreground hover:text-foreground hover:bg-muted/50'
          }`}
        >
          {filter.label}
        </button>
      ))}
    </div>
  )
}
