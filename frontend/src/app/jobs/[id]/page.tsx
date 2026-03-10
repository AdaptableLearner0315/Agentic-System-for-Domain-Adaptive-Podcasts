'use client'

import { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { Header } from '@/components/Header'
import { ProgressTracker } from '@/components/ProgressTracker'
import { OutputPlayer } from '@/components/OutputPlayer'
import { getJob, getJobResult } from '@/lib/api'
import { useProgress } from '@/hooks/useProgress'
import type { JobResponse, ResultResponse } from '@/types'

/**
 * Job details page.
 *
 * Displays the status, progress, and result of a specific generation job.
 * Supports real-time progress updates via WebSocket.
 */
export default function JobPage() {
  const params = useParams()
  const router = useRouter()
  const jobId = params.id as string

  const [job, setJob] = useState<JobResponse | null>(null)
  const [result, setResult] = useState<ResultResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Connect to WebSocket if job is running
  const shouldConnect = job?.status === 'pending' || job?.status === 'running'
  const { progress, isComplete, completionData } = useProgress(
    shouldConnect ? jobId : null
  )

  // Fetch initial job data
  useEffect(() => {
    async function fetchJob() {
      try {
        const jobData = await getJob(jobId)
        setJob(jobData)

        // If already completed, fetch result
        if (jobData.status === 'completed') {
          try {
            const resultData = await getJobResult(jobId)
            setResult(resultData)
          } catch (e) {
            // Result may not be available
          }
        }
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Failed to load job')
      } finally {
        setLoading(false)
      }
    }

    fetchJob()
  }, [jobId])

  // Handle WebSocket completion
  useEffect(() => {
    if (isComplete && completionData) {
      setJob((prev) =>
        prev
          ? {
              ...prev,
              status: completionData.success ? 'completed' : 'failed',
            }
          : null
      )

      if (completionData.success) {
        // Fetch full result
        getJobResult(jobId)
          .then(setResult)
          .catch(() => {
            // Use partial data
            setResult({
              job_id: jobId,
              success: true,
              video_url: completionData.videoUrl,
              output_path: completionData.outputPath,
              duration_seconds: completionData.durationSeconds,
            })
          })
      }
    }
  }, [isComplete, completionData, jobId])

  /**
   * Navigate back to home.
   */
  const handleGoHome = () => {
    router.push('/')
  }

  /**
   * Reset and create new job.
   */
  const handleReset = () => {
    router.push('/')
  }

  if (loading) {
    return (
      <main className="min-h-screen bg-ambient">
        <Header />
        <div className="container mx-auto px-4 py-8 max-w-4xl">
          <div className="flex justify-center items-center h-64">
            <span className="spinner h-8 w-8" />
          </div>
        </div>
      </main>
    )
  }

  if (error || !job) {
    return (
      <main className="min-h-screen bg-ambient">
        <Header />
        <div className="container mx-auto px-4 py-8 max-w-4xl">
          <div className="card text-center py-12">
            <svg
              className="w-16 h-16 mx-auto text-muted-foreground mb-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M12 12h.01M12 12h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <h2 className="text-xl font-bold mb-2">Job Not Found</h2>
            <p className="text-muted-foreground mb-4">
              {error || 'The requested job does not exist.'}
            </p>
            <button className="btn-primary" onClick={handleGoHome}>
              Go Home
            </button>
          </div>
        </div>
      </main>
    )
  }

  return (
    <main className="min-h-screen bg-ambient">
      <Header />

      <div className="container mx-auto px-4 py-8 max-w-4xl">
        {/* Breadcrumb */}
        <div className="flex items-center gap-2 text-sm text-muted-foreground mb-6">
          <button
            className="hover:text-foreground transition-colors"
            onClick={handleGoHome}
          >
            Home
          </button>
          <span>/</span>
          <span>Job {jobId}</span>
        </div>

        {/* Job Info Header */}
        <div className="card mb-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-xl font-bold">Job {jobId}</h1>
              <p className="text-sm text-muted-foreground mt-1">
                Mode: <span className="capitalize">{job.mode}</span>
                {job.prompt && ` • "${job.prompt.slice(0, 50)}..."`}
              </p>
            </div>
            <div
              className={`
                badge
                ${job.status === 'completed' ? 'badge-success' : ''}
                ${job.status === 'running' ? 'badge-primary' : ''}
                ${job.status === 'pending' ? 'bg-secondary text-muted-foreground' : ''}
                ${job.status === 'failed' ? 'badge-destructive' : ''}
                ${job.status === 'cancelled' ? 'badge-warning' : ''}
              `}
            >
              {job.status}
            </div>
          </div>
        </div>

        {/* Progress (if running) */}
        {(job.status === 'pending' || job.status === 'running') && progress && (
          <div className="mb-6">
            <ProgressTracker progress={progress} />
          </div>
        )}

        {/* Result (if completed) */}
        {job.status === 'completed' && result && (
          <OutputPlayer result={result} onReset={handleReset} />
        )}

        {/* Error (if failed) */}
        {job.status === 'failed' && (
          <div className="card border-destructive/50 bg-destructive/10">
            <div className="flex items-start gap-3">
              <svg
                className="w-5 h-5 text-destructive mt-0.5"
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
              <div>
                <h3 className="font-medium text-destructive">Generation Failed</h3>
                <p className="text-sm text-muted-foreground mt-1">
                  {job.error || 'An error occurred during generation.'}
                </p>
              </div>
            </div>
            <button className="btn-secondary mt-4" onClick={handleReset}>
              Try Again
            </button>
          </div>
        )}

        {/* Cancelled */}
        {job.status === 'cancelled' && (
          <div className="card text-center py-8">
            <svg
              className="w-12 h-12 mx-auto text-muted-foreground mb-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
            <h2 className="text-xl font-bold mb-2">Job Cancelled</h2>
            <p className="text-muted-foreground mb-4">
              This job was cancelled before completion.
            </p>
            <button className="btn-primary" onClick={handleReset}>
              Create New Podcast
            </button>
          </div>
        )}
      </div>
    </main>
  )
}
