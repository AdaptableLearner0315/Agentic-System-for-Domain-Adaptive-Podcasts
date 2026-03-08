'use client'

/**
 * Series List Page
 *
 * View and manage all podcast series. Series creation is now integrated
 * into the main page - this page focuses on listing and managing existing series.
 */

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { Header } from '@/components/Header'
import { useSeries } from '@/hooks/useSeries'
import type { SeriesStatus } from '@/types'

/**
 * Series card component for the list view.
 */
function SeriesCard({ series, onDelete }: {
  series: {
    id: string
    status: string
    prompt: string
    outline: {
      title: string
      description: string
      episode_count: number
      style_dna: { era: string; genre: string }
    }
    progress_percent: number
    created_at: string
  }
  onDelete: (id: string) => void
}) {
  const statusColors: Record<string, string> = {
    draft: 'bg-yellow-500/20 text-yellow-400',
    in_progress: 'bg-primary/20 text-primary',
    completed: 'bg-green-500/20 text-green-400',
    cancelled: 'bg-destructive/20 text-destructive',
  }

  return (
    <div className="card hover:border-primary/30 transition-colors">
      <div className="flex justify-between items-start mb-3">
        <Link href={`/series/${series.id}`} className="flex-1">
          <h3 className="text-lg font-semibold text-foreground hover:text-primary transition-colors">
            {series.outline.title}
          </h3>
        </Link>
        <span className={`px-2 py-1 rounded text-xs font-medium ${statusColors[series.status] || 'bg-muted text-muted-foreground'}`}>
          {series.status.replace('_', ' ')}
        </span>
      </div>

      <p className="text-muted-foreground text-sm mb-4 line-clamp-2">
        {series.outline.description || series.prompt}
      </p>

      <div className="flex items-center justify-between text-sm">
        <div className="flex items-center gap-4 text-muted-foreground">
          <span>{series.outline.episode_count} episodes</span>
          <span>{series.outline.style_dna?.era || 'modern'}</span>
          <span>{series.outline.style_dna?.genre || 'documentary'}</span>
        </div>

        {series.status === 'in_progress' && (
          <div className="flex items-center gap-2">
            <div className="w-24 h-2 bg-secondary rounded-full overflow-hidden">
              <div
                className="h-full bg-primary transition-all"
                style={{ width: `${series.progress_percent}%` }}
              />
            </div>
            <span className="text-muted-foreground text-xs">{Math.round(series.progress_percent)}%</span>
          </div>
        )}
      </div>

      <div className="flex items-center justify-between mt-4 pt-4 border-t border-border">
        <span className="text-xs text-muted-foreground">
          Created {new Date(series.created_at).toLocaleDateString()}
        </span>
        <div className="flex gap-2">
          <Link
            href={`/series/${series.id}`}
            className="px-3 py-1 text-sm text-primary hover:text-primary/80 transition-colors"
          >
            View
          </Link>
          {series.status === 'draft' && (
            <button
              onClick={() => onDelete(series.id)}
              className="px-3 py-1 text-sm text-destructive hover:text-destructive/80 transition-colors"
            >
              Delete
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

/**
 * Main series list page component.
 */
export default function SeriesPage() {
  const {
    seriesList,
    isLoading,
    error,
    total,
    remove,
    refresh,
    clearError,
  } = useSeries()

  const [statusFilter, setStatusFilter] = useState<string>('')

  useEffect(() => {
    refresh(statusFilter as SeriesStatus || undefined)
  }, [statusFilter, refresh])

  const handleDelete = async (id: string) => {
    if (confirm('Are you sure you want to delete this series?')) {
      await remove(id)
    }
  }

  return (
    <main className="min-h-screen">
      <Header />

      <div className="container mx-auto px-4 py-12 max-w-4xl">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold gradient-text">Your Series</h1>
            <p className="text-muted-foreground mt-1">Manage your podcast series</p>
          </div>
          <Link
            href="/"
            className="text-muted-foreground hover:text-foreground transition-colors"
          >
            &larr; Back to Home
          </Link>
        </div>

        {error && (
          <div className="card border-destructive/50 bg-destructive/10 mb-6 flex items-center justify-between">
            <span className="text-destructive">{error}</span>
            <button onClick={clearError} className="text-destructive/70 hover:text-destructive text-xl">
              &times;
            </button>
          </div>
        )}

        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-medium text-foreground">
            {total} {total === 1 ? 'Series' : 'Series'}
          </h2>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-secondary border border-border rounded-lg px-3 py-2 text-foreground text-sm focus:outline-none focus:border-primary"
          >
            <option value="">All Status</option>
            <option value="draft">Draft</option>
            <option value="in_progress">In Progress</option>
            <option value="completed">Completed</option>
            <option value="cancelled">Cancelled</option>
          </select>
        </div>

        {isLoading ? (
          <div className="text-center py-12">
            <div className="animate-spin text-4xl text-primary mb-4">&#9696;</div>
            <p className="text-muted-foreground">Loading series...</p>
          </div>
        ) : seriesList.length === 0 ? (
          <div className="text-center py-12 card">
            <p className="text-muted-foreground mb-2">No series found</p>
            <p className="text-muted-foreground/70 text-sm mb-4">Create your first series from the home page</p>
            <Link
              href="/"
              className="inline-flex items-center gap-2 text-primary hover:text-primary/80 transition-colors"
            >
              Create a Series &rarr;
            </Link>
          </div>
        ) : (
          <div className="space-y-4">
            {seriesList.map((series) => (
              <SeriesCard
                key={series.id}
                series={series}
                onDelete={handleDelete}
              />
            ))}
          </div>
        )}
      </div>
    </main>
  )
}
