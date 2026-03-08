/**
 * React hook for series management.
 *
 * Provides state management for creating and managing episodic podcast series.
 */

import { useState, useCallback, useEffect } from 'react'
import {
  createSeries,
  getSeries,
  listSeries,
  approveSeriesOutline,
  generateSeriesEpisode,
  deleteSeries as apiDeleteSeries,
} from '@/lib/api'
import type {
  Series,
  SeriesStatus,
  CreateSeriesRequest,
  ApproveOutlineRequest,
} from '@/types'

/**
 * Aggregate quality data for completed episodes.
 */
interface AggregateQuality {
  totalScore: number
  episodeCount: number
}

/**
 * Return type for the useSeries hook.
 */
interface UseSeriesReturn {
  /** List of all series */
  seriesList: Series[]
  /** Currently selected series */
  currentSeries: Series | null
  /** Loading state */
  isLoading: boolean
  /** Creating state */
  isCreating: boolean
  /** Approving state */
  isApproving: boolean
  /** Generating episode state */
  isGenerating: boolean
  /** Job ID for current episode generation (for WebSocket progress) */
  generatingJobId: string | null
  /** Episode number currently being generated */
  generatingEpisodeNumber: number | null
  /** Error message if any */
  error: string | null
  /** Total series count */
  total: number
  /** Whether auto-generation is active */
  isAutoGenerating: boolean
  /** Episode numbers pending in auto-generation queue */
  pendingEpisodeNumbers: number[]
  /** Aggregate quality across completed episodes */
  aggregateQuality: AggregateQuality
  /** Whether to stop after current episode completes */
  stopAfterCurrent: boolean
  /** Create a new series */
  create: (data: CreateSeriesRequest) => Promise<Series>
  /** Load a specific series */
  load: (seriesId: string) => Promise<Series | null>
  /** Approve series outline */
  approve: (seriesId: string, data?: ApproveOutlineRequest) => Promise<Series>
  /** Generate next episode */
  generateEpisode: (seriesId: string, episodeNumber?: number) => Promise<void>
  /** Delete/cancel a series */
  remove: (seriesId: string) => Promise<void>
  /** Refresh series list */
  refresh: (status?: SeriesStatus, page?: number) => Promise<void>
  /** Clear current series selection */
  clearCurrent: () => void
  /** Clear error */
  clearError: () => void
  /** Clear generating state (called when generation completes) */
  clearGenerating: () => void
  /** Start auto-generation for all pending episodes */
  startAutoGeneration: (seriesId: string, pendingEpisodes: number[]) => Promise<void>
  /** Stop auto-generation after current episode */
  stopAutoGeneration: () => void
  /** Handle episode completion during auto-generation */
  handleEpisodeComplete: (seriesId: string, episodeNumber: number, quality?: { overall_score?: number }) => Promise<void>
}

/**
 * Hook for managing podcast series.
 *
 * @returns Series state and control functions
 *
 * @example
 * ```tsx
 * const { seriesList, create, approve, generateEpisode, isLoading } = useSeries()
 *
 * // Create a new series
 * const series = await create({
 *   prompt: 'The rise and fall of disco',
 *   episode_count: 5,
 * })
 *
 * // Approve the outline
 * await approve(series.id, { approved: true })
 *
 * // Generate episodes
 * await generateEpisode(series.id)
 * ```
 */
export function useSeries(): UseSeriesReturn {
  const [seriesList, setSeriesList] = useState<Series[]>([])
  const [currentSeries, setCurrentSeries] = useState<Series | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [isCreating, setIsCreating] = useState(false)
  const [isApproving, setIsApproving] = useState(false)
  const [isGenerating, setIsGenerating] = useState(false)
  const [generatingJobId, setGeneratingJobId] = useState<string | null>(null)
  const [generatingEpisodeNumber, setGeneratingEpisodeNumber] = useState<number | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [total, setTotal] = useState(0)

  // Auto-generation state
  const [isAutoGenerating, setIsAutoGenerating] = useState(false)
  const [stopAfterCurrent, setStopAfterCurrent] = useState(false)
  const [pendingEpisodeNumbers, setPendingEpisodeNumbers] = useState<number[]>([])
  const [aggregateQuality, setAggregateQuality] = useState<AggregateQuality>({
    totalScore: 0,
    episodeCount: 0,
  })

  /**
   * Refresh the series list.
   */
  const refresh = useCallback(
    async (status?: SeriesStatus, page: number = 1): Promise<void> => {
      setIsLoading(true)
      setError(null)

      try {
        const response = await listSeries(page, 20, status)
        setSeriesList(response.series)
        setTotal(response.total)
      } catch (e) {
        const errorMsg = e instanceof Error ? e.message : 'Failed to load series'
        setError(errorMsg)
      } finally {
        setIsLoading(false)
      }
    },
    []
  )

  /**
   * Create a new series.
   */
  const create = useCallback(async (data: CreateSeriesRequest): Promise<Series> => {
    setIsCreating(true)
    setError(null)

    try {
      const series = await createSeries(data)
      setCurrentSeries(series)
      setSeriesList((prev) => [series, ...prev])
      return series
    } catch (e) {
      const errorMsg = e instanceof Error ? e.message : 'Failed to create series'
      setError(errorMsg)
      throw e
    } finally {
      setIsCreating(false)
    }
  }, [])

  /**
   * Load a specific series by ID.
   */
  const load = useCallback(async (seriesId: string): Promise<Series | null> => {
    setIsLoading(true)
    setError(null)

    try {
      const series = await getSeries(seriesId)
      setCurrentSeries(series)
      return series
    } catch (e) {
      const errorMsg = e instanceof Error ? e.message : 'Failed to load series'
      setError(errorMsg)
      return null
    } finally {
      setIsLoading(false)
    }
  }, [])

  /**
   * Approve series outline.
   */
  const approve = useCallback(
    async (seriesId: string, data: ApproveOutlineRequest = { approved: true }): Promise<Series> => {
      setIsApproving(true)
      setError(null)

      try {
        const series = await approveSeriesOutline(seriesId, data)
        setCurrentSeries(series)
        // Update in list
        setSeriesList((prev) =>
          prev.map((s) => (s.id === seriesId ? series : s))
        )
        return series
      } catch (e) {
        const errorMsg = e instanceof Error ? e.message : 'Failed to approve outline'
        setError(errorMsg)
        throw e
      } finally {
        setIsApproving(false)
      }
    },
    []
  )

  /**
   * Generate the next episode.
   */
  const generateEpisode = useCallback(
    async (seriesId: string, episodeNumber?: number): Promise<void> => {
      setIsGenerating(true)
      setError(null)

      try {
        const response = await generateSeriesEpisode(seriesId, episodeNumber ? { episode_number: episodeNumber } : undefined)

        // Debug: Log the response to help identify job_id issues
        console.log('Generate episode response:', response)

        // Store job_id and episode number for WebSocket progress tracking
        if (response.job_id) {
          setGeneratingJobId(response.job_id)
        } else {
          console.error('No job_id in generate episode response:', response)
        }
        setGeneratingEpisodeNumber(response.episode_number)

        // Refresh the series to get updated episode status
        const series = await getSeries(seriesId)
        setCurrentSeries(series)
        setSeriesList((prev) =>
          prev.map((s) => (s.id === seriesId ? series : s))
        )
      } catch (e) {
        const errorMsg = e instanceof Error ? e.message : 'Failed to generate episode'
        setError(errorMsg)
        setGeneratingJobId(null)
        setGeneratingEpisodeNumber(null)
        throw e
      }
      // Note: isGenerating stays true until clearGenerating() is called on completion
    },
    []
  )

  /**
   * Delete/cancel a series.
   */
  const remove = useCallback(async (seriesId: string): Promise<void> => {
    try {
      await apiDeleteSeries(seriesId)
      setSeriesList((prev) => prev.filter((s) => s.id !== seriesId))
      if (currentSeries?.id === seriesId) {
        setCurrentSeries(null)
      }
    } catch (e) {
      const errorMsg = e instanceof Error ? e.message : 'Failed to delete series'
      setError(errorMsg)
      throw e
    }
  }, [currentSeries])

  /**
   * Clear current series selection.
   */
  const clearCurrent = useCallback(() => {
    setCurrentSeries(null)
  }, [])

  /**
   * Clear error.
   */
  const clearError = useCallback(() => {
    setError(null)
  }, [])

  /**
   * Clear generating state (called when generation completes or fails).
   */
  const clearGenerating = useCallback(() => {
    setIsGenerating(false)
    setGeneratingJobId(null)
    setGeneratingEpisodeNumber(null)
  }, [])

  /**
   * Start auto-generation for all pending episodes.
   */
  const startAutoGeneration = useCallback(
    async (seriesId: string, pendingEpisodes: number[]): Promise<void> => {
      if (pendingEpisodes.length === 0) return

      setIsAutoGenerating(true)
      setStopAfterCurrent(false)
      setPendingEpisodeNumbers(pendingEpisodes)
      setAggregateQuality({ totalScore: 0, episodeCount: 0 })

      // Start generating the first episode
      const firstEpisode = pendingEpisodes[0]
      setIsGenerating(true)
      setError(null)

      try {
        const response = await generateSeriesEpisode(seriesId, { episode_number: firstEpisode })
        if (response.job_id) {
          setGeneratingJobId(response.job_id)
        }
        setGeneratingEpisodeNumber(response.episode_number)

        const series = await getSeries(seriesId)
        setCurrentSeries(series)
        setSeriesList((prev) =>
          prev.map((s) => (s.id === seriesId ? series : s))
        )
      } catch (e) {
        const errorMsg = e instanceof Error ? e.message : 'Failed to start auto-generation'
        setError(errorMsg)
        setIsAutoGenerating(false)
        setGeneratingJobId(null)
        setGeneratingEpisodeNumber(null)
        setPendingEpisodeNumbers([])
      }
    },
    []
  )

  /**
   * Stop auto-generation after current episode completes.
   */
  const stopAutoGeneration = useCallback(() => {
    setStopAfterCurrent(true)
  }, [])

  /**
   * Handle episode completion during auto-generation.
   * Updates aggregate quality and triggers next episode if appropriate.
   */
  const handleEpisodeComplete = useCallback(
    async (seriesId: string, episodeNumber: number, quality?: { overall_score?: number }): Promise<void> => {
      // Update aggregate quality
      if (quality?.overall_score) {
        setAggregateQuality((prev) => ({
          totalScore: prev.totalScore + quality.overall_score!,
          episodeCount: prev.episodeCount + 1,
        }))
      }

      // Remove completed episode from pending
      setPendingEpisodeNumbers((prev) => {
        const remaining = prev.filter((ep) => ep !== episodeNumber)

        // Check if we should continue auto-generation
        if (isAutoGenerating && !stopAfterCurrent && remaining.length > 0) {
          // Trigger next episode generation
          const nextEpisode = remaining[0]
          setTimeout(async () => {
            setIsGenerating(true)
            setError(null)

            try {
              const response = await generateSeriesEpisode(seriesId, { episode_number: nextEpisode })
              if (response.job_id) {
                setGeneratingJobId(response.job_id)
              }
              setGeneratingEpisodeNumber(response.episode_number)

              const series = await getSeries(seriesId)
              setCurrentSeries(series)
              setSeriesList((prev) =>
                prev.map((s) => (s.id === seriesId ? series : s))
              )
            } catch (e) {
              const errorMsg = e instanceof Error ? e.message : 'Failed to generate next episode'
              setError(errorMsg)
              setIsAutoGenerating(false)
              setIsGenerating(false)
              setGeneratingJobId(null)
              setGeneratingEpisodeNumber(null)
            }
          }, 500) // Small delay before starting next episode
        } else if (remaining.length === 0 || stopAfterCurrent) {
          // Auto-generation complete or stopped
          setIsAutoGenerating(false)
          setStopAfterCurrent(false)
        }

        return remaining
      })
    },
    [isAutoGenerating, stopAfterCurrent]
  )

  return {
    seriesList,
    currentSeries,
    isLoading,
    isCreating,
    isApproving,
    isGenerating,
    generatingJobId,
    generatingEpisodeNumber,
    error,
    total,
    isAutoGenerating,
    pendingEpisodeNumbers,
    aggregateQuality,
    stopAfterCurrent,
    create,
    load,
    approve,
    generateEpisode,
    remove,
    refresh,
    clearCurrent,
    clearError,
    clearGenerating,
    startAutoGeneration,
    stopAutoGeneration,
    handleEpisodeComplete,
  }
}
