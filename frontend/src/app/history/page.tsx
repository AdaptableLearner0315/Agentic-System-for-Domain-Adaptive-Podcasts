'use client'

import { useState, useEffect, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { Header } from '@/components/Header'
import { JobCard } from '@/components/JobCard'
import { FilterBar } from '@/components/FilterBar'
import { Pagination } from '@/components/Pagination'
import { listJobs, deleteJob } from '@/lib/api'
import { STORAGE_KEYS } from '@/lib/constants'
import type { JobResponse, JobStatus } from '@/types'

const PAGE_SIZE = 10

/**
 * Empty state component when no jobs match the filter.
 */
function EmptyState({ hasFilter }: { hasFilter: boolean }) {
  const router = useRouter()

  return (
    <div className="card text-center py-12">
      <svg
        className="w-12 h-12 mx-auto text-muted-foreground/50 mb-4"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={1.5}
          d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"
        />
      </svg>
      <h3 className="text-lg font-medium mb-2">
        {hasFilter ? 'No matching podcasts' : 'No podcasts yet'}
      </h3>
      <p className="text-sm text-muted-foreground mb-4">
        {hasFilter
          ? 'Try changing the filter to see more results.'
          : 'Create your first podcast to see it here.'}
      </p>
      {!hasFilter && (
        <button
          onClick={() => router.push('/')}
          className="btn-primary"
        >
          Create Podcast
        </button>
      )}
    </div>
  )
}

/**
 * Loading skeleton for job cards.
 */
function LoadingSkeleton() {
  return (
    <div className="space-y-4">
      {[1, 2, 3].map((i) => (
        <div key={i} className="card animate-pulse">
          <div className="flex items-start gap-4">
            {/* Thumbnail skeleton */}
            <div className="w-20 h-20 bg-muted rounded-lg flex-shrink-0" />
            <div className="flex-1">
              <div className="h-5 bg-muted rounded w-2/3 mb-2" />
              <div className="h-4 bg-muted rounded w-1/3 mb-2" />
              <div className="h-5 bg-muted rounded w-1/4" />
            </div>
            <div className="flex gap-2">
              <div className="h-8 w-16 bg-muted rounded" />
              <div className="h-8 w-16 bg-muted rounded" />
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}

/**
 * History page for viewing past podcast generations.
 */
export default function HistoryPage() {
  const router = useRouter()
  const [jobs, setJobs] = useState<JobResponse[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [filter, setFilter] = useState<JobStatus | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const totalPages = Math.ceil(total / PAGE_SIZE)

  /**
   * Fetch jobs from the API.
   */
  const fetchJobs = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const response = await listJobs(page, PAGE_SIZE, filter ?? undefined)
      setJobs(response.jobs)
      setTotal(response.total)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load jobs')
    } finally {
      setIsLoading(false)
    }
  }, [page, filter])

  useEffect(() => {
    fetchJobs()
  }, [fetchJobs])

  /**
   * Handle filter change.
   */
  const handleFilterChange = (newFilter: JobStatus | null) => {
    setFilter(newFilter)
    setPage(1) // Reset to first page when filter changes
  }

  /**
   * Handle job deletion.
   */
  const handleDelete = async (jobId: string) => {
    try {
      await deleteJob(jobId)
      // Refresh the list
      await fetchJobs()
    } catch (err) {
      console.error('Failed to delete job:', err)
    }
  }

  /**
   * Handle reusing a job's prompt.
   */
  const handleReuse = (job: JobResponse) => {
    // Store the job data in sessionStorage for the home page to read
    sessionStorage.setItem(
      STORAGE_KEYS.REUSE_JOB,
      JSON.stringify({
        prompt: job.prompt,
        guidance: job.guidance,
        mode: job.mode,
      })
    )
    router.push('/')
  }

  return (
    <main className="min-h-screen">
      <Header />

      <div className="container mx-auto px-4 py-12 max-w-2xl">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold">History</h1>
            <p className="text-sm text-muted-foreground">
              {total} {total === 1 ? 'podcast' : 'podcasts'} generated
            </p>
          </div>
          <button
            onClick={() => router.push('/')}
            className="btn-primary"
          >
            Create New
          </button>
        </div>

        {/* Filter bar */}
        <div className="mb-6">
          <FilterBar currentFilter={filter} onFilterChange={handleFilterChange} />
        </div>

        {/* Error state */}
        {error && (
          <div className="card border-destructive/50 bg-destructive/10 mb-6">
            <div className="flex items-center gap-3">
              <svg
                className="w-5 h-5 text-destructive"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
              <span className="text-sm">{error}</span>
              <button
                onClick={fetchJobs}
                className="btn-secondary text-sm py-1 px-3 ml-auto"
              >
                Retry
              </button>
            </div>
          </div>
        )}

        {/* Loading state */}
        {isLoading && <LoadingSkeleton />}

        {/* Job list */}
        {!isLoading && !error && jobs.length > 0 && (
          <div className="space-y-4">
            {jobs.map((job) => (
              <JobCard
                key={job.id}
                job={job}
                onDelete={handleDelete}
                onReuse={handleReuse}
              />
            ))}
          </div>
        )}

        {/* Empty state */}
        {!isLoading && !error && jobs.length === 0 && (
          <EmptyState hasFilter={filter !== null} />
        )}

        {/* Pagination */}
        {!isLoading && totalPages > 1 && (
          <Pagination
            currentPage={page}
            totalPages={totalPages}
            onPageChange={setPage}
          />
        )}
      </div>
    </main>
  )
}
