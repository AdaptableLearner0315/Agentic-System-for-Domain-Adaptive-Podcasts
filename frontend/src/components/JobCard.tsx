'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Image from 'next/image'
import type { JobResponse, JobStatus } from '@/types'
import { API_URL } from '@/lib/api'
import { formatDuration } from '@/lib/utils'

interface JobCardProps {
  job: JobResponse
  onDelete: (jobId: string) => Promise<void>
  onReuse: (job: JobResponse) => void
}

/**
 * Status badge component with color-coded styling.
 */
function StatusBadge({ status }: { status: JobStatus }) {
  const statusConfig: Record<JobStatus, { label: string; className: string }> = {
    pending: {
      label: 'Pending',
      className: 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20',
    },
    running: {
      label: 'Running',
      className: 'bg-blue-500/10 text-blue-500 border-blue-500/20',
    },
    completed: {
      label: 'Completed',
      className: 'bg-green-500/10 text-green-500 border-green-500/20',
    },
    failed: {
      label: 'Failed',
      className: 'bg-red-500/10 text-red-500 border-red-500/20',
    },
    cancelled: {
      label: 'Cancelled',
      className: 'bg-gray-500/10 text-gray-500 border-gray-500/20',
    },
  }

  const config = statusConfig[status]

  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 text-xs font-medium rounded-full border ${config.className}`}
    >
      {config.label}
    </span>
  )
}

/**
 * Format a date string for display.
 */
function formatDate(dateString: string): string {
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMins / 60)
  const diffDays = Math.floor(diffHours / 24)

  if (diffMins < 1) return 'Just now'
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  if (diffDays < 7) return `${diffDays}d ago`

  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  })
}

/**
 * Get a display title for the job.
 */
function getJobTitle(job: JobResponse): string {
  if (job.prompt) {
    // Truncate long prompts
    return job.prompt.length > 60 ? job.prompt.slice(0, 60) + '...' : job.prompt
  }
  if (job.file_ids && job.file_ids.length > 0) {
    return `${job.file_ids.length} file(s) enhanced`
  }
  return 'Untitled podcast'
}

/**
 * Get thumbnail URL from job's image assets.
 */
function getThumbnailUrl(job: JobResponse): string | null {
  const images = job.result?.image_assets
  if (!images || images.length === 0) return null

  // Use the first image as thumbnail via the preview endpoint
  const firstImage = images[0]
  return `${API_URL}/api/outputs/preview/${job.id}/image/${firstImage.id}`
}

/**
 * Genre badge component.
 */
function GenreBadge({ genre }: { genre: string }) {
  return (
    <span className="inline-flex items-center px-2 py-0.5 text-xs font-medium rounded-full bg-purple-500/10 text-purple-400 border border-purple-500/20">
      {genre}
    </span>
  )
}

/**
 * Job card component for displaying a job in the history list.
 */
export function JobCard({ job, onDelete, onReuse }: JobCardProps) {
  const router = useRouter()
  const [isDeleting, setIsDeleting] = useState(false)

  const handleView = () => {
    router.push(`/jobs/${job.id}`)
  }

  const handleReuse = () => {
    onReuse(job)
  }

  const handleDelete = async () => {
    if (isDeleting) return
    setIsDeleting(true)
    try {
      await onDelete(job.id)
    } finally {
      setIsDeleting(false)
    }
  }

  const canView = job.status === 'completed'
  const duration = job.result?.duration_seconds
  const thumbnailUrl = getThumbnailUrl(job)

  return (
    <div className="card hover:border-border/80 transition-colors">
      <div className="flex items-start gap-4">
        {/* Thumbnail */}
        {thumbnailUrl ? (
          <div className="relative w-20 h-20 flex-shrink-0 rounded-lg overflow-hidden bg-secondary">
            <Image
              src={thumbnailUrl}
              alt="Podcast thumbnail"
              fill
              className="object-cover"
              sizes="80px"
              unoptimized
            />
          </div>
        ) : (
          <div className="w-20 h-20 flex-shrink-0 rounded-lg bg-secondary flex items-center justify-center">
            <svg
              className="w-8 h-8 text-muted-foreground/50"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"
              />
            </svg>
          </div>
        )}

        {/* Main content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1 flex-wrap">
            <h3 className="font-medium truncate">{getJobTitle(job)}</h3>
            <StatusBadge status={job.status} />
          </div>
          <div className="flex items-center gap-2 text-sm text-muted-foreground flex-wrap">
            <span className="capitalize">{job.mode} mode</span>
            <span>·</span>
            <span>{formatDate(job.created_at)}</span>
            {duration && (
              <>
                <span>·</span>
                <span>{formatDuration(duration)}</span>
              </>
            )}
          </div>
          {/* Genre badge from guidance */}
          {job.guidance && (
            <div className="mt-2">
              <GenreBadge genre={job.guidance} />
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2 flex-shrink-0">
          {canView && (
            <button
              onClick={handleView}
              className="btn-secondary text-sm py-1.5 px-3"
            >
              View
            </button>
          )}
          <button
            onClick={handleReuse}
            className="btn-secondary text-sm py-1.5 px-3"
          >
            Reuse
          </button>
          <button
            onClick={handleDelete}
            disabled={isDeleting}
            className="p-2 text-muted-foreground hover:text-destructive hover:bg-destructive/10 rounded-lg transition-colors disabled:opacity-50"
            title="Delete"
          >
            {isDeleting ? (
              <svg
                className="w-4 h-4 animate-spin"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                />
              </svg>
            ) : (
              <svg
                className="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                />
              </svg>
            )}
          </button>
        </div>
      </div>
    </div>
  )
}
