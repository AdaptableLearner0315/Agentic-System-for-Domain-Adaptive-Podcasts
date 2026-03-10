'use client'

/**
 * Series Detail Page
 *
 * View and manage a specific podcast series, including outline approval
 * and episode generation. Uses the same warm orange/brown theme as the main page.
 */

import { useState, useEffect, useCallback, useRef } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import { Header } from '@/components/Header'
import { ProgressTracker } from '@/components/ProgressTracker'
import { QualityPanel } from '@/components/QualityPanel'
import { SeriesProgressHeader } from '@/components/SeriesProgressHeader'
import { useSeries } from '@/hooks/useSeries'
import { createProgressConnection, ProgressWebSocket } from '@/lib/websocket'
import { getSeries, API_URL } from '@/lib/api'
import type { Episode, EpisodeSummary, SeriesStatus, CliffhangerType, ProgressResponse, QualityReport } from '@/types'

/**
 * Episode card in the outline view.
 */
function EpisodeOutlineCard({ episode, index }: {
  episode: EpisodeSummary
  index: number
}) {
  const cliffhangerColors: Record<CliffhangerType, string> = {
    revelation: 'text-purple-400',
    twist: 'text-red-400',
    question: 'text-cyan-400',
    countdown: 'text-orange-400',
    promise: 'text-green-400',
  }

  const statusIcons: Record<string, string> = {
    pending: '○',
    generating: '◐',
    completed: '●',
    failed: '✕',
  }

  return (
    <div className="card border-l-4 border-primary">
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-3">
          <span className="text-2xl font-bold text-muted-foreground/50">{index + 1}</span>
          <div>
            <h4 className="font-semibold text-foreground">{episode.title}</h4>
            <span className="text-xs text-muted-foreground">
              {statusIcons[episode.status]} {episode.status}
            </span>
          </div>
        </div>
        {episode.cliffhanger_type && (
          <span className={`text-xs font-medium ${cliffhangerColors[episode.cliffhanger_type] || 'text-muted-foreground'}`}>
            {episode.cliffhanger_type.toUpperCase()}
          </span>
        )}
      </div>
      <p className="text-muted-foreground text-sm">{episode.premise}</p>
    </div>
  )
}

/**
 * Generated episode card with inline playback.
 */
function GeneratedEpisodeCard({
  episode,
  quality,
  onShowQuality,
}: {
  episode: Episode
  quality?: QualityReport
  onShowQuality?: () => void
}) {
  const statusColors: Record<string, string> = {
    pending: 'bg-muted-foreground',
    generating: 'bg-primary animate-pulse',
    completed: 'bg-green-500',
    failed: 'bg-destructive',
  }

  // Build full URLs for media playback
  const videoUrl = episode.video_url
    ? `${API_URL}${episode.video_url}`
    : null
  const audioUrl = episode.audio_url
    ? `${API_URL}${episode.audio_url}`
    : null

  return (
    <div className="card">
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          <div className={`w-3 h-3 rounded-full ${statusColors[episode.status]}`} />
          <div>
            <h4 className="font-semibold text-foreground">
              Episode {episode.episode_number}: {episode.title}
            </h4>
            <span className="text-xs text-muted-foreground capitalize">{episode.status}</span>
          </div>
        </div>
        <div className="flex items-center gap-3">
          {/* Quality score badge */}
          {quality && episode.status === 'completed' && (
            <button
              onClick={onShowQuality}
              className="flex items-center gap-1.5 px-2 py-1 rounded bg-amber-500/10 hover:bg-amber-500/20 text-amber-400 transition-colors"
              title="View quality report"
            >
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
              </svg>
              <span className={`text-xs font-medium px-1.5 py-0.5 rounded ${
                quality.overall_grade?.startsWith('A') ? 'bg-emerald-500/20 text-emerald-400' :
                quality.overall_grade?.startsWith('B') ? 'bg-green-500/20 text-green-400' :
                quality.overall_grade?.startsWith('C') ? 'bg-yellow-500/20 text-yellow-400' :
                'bg-orange-500/20 text-orange-400'
              }`}>
                {quality.overall_grade}
              </span>
            </button>
          )}
          {episode.duration_seconds && (
            <span className="text-sm text-muted-foreground">
              {Math.floor(episode.duration_seconds / 60)}:{String(Math.floor(episode.duration_seconds % 60)).padStart(2, '0')}
            </span>
          )}
        </div>
      </div>

      {episode.previously_on && (
        <div className="mb-3 p-2 bg-secondary rounded text-sm">
          <span className="text-muted-foreground text-xs block mb-1">Previously on:</span>
          <p className="text-foreground/80 italic">{episode.previously_on}</p>
        </div>
      )}

      {episode.cliffhanger && (
        <div className="mb-3 p-2 bg-secondary rounded text-sm">
          <span className="text-muted-foreground text-xs block mb-1">Cliffhanger:</span>
          <p className="text-foreground/80 italic">{episode.cliffhanger}</p>
        </div>
      )}

      {/* Inline media player for completed episodes */}
      {episode.status === 'completed' && (videoUrl || audioUrl) && (
        <div className="mt-4">
          {/* Video player (primary) */}
          {videoUrl && (
            <div className="relative aspect-video rounded-lg overflow-hidden bg-black">
              <video
                className="w-full h-full"
                controls
                src={videoUrl}
              >
                Your browser does not support video playback.
              </video>
            </div>
          )}

          {/* Audio player (fallback if no video, or expandable) */}
          {audioUrl && (
            <div className={videoUrl ? 'mt-3' : ''}>
              {videoUrl ? (
                // Show as expandable audio option when video exists
                <details className="group">
                  <summary className="cursor-pointer text-sm text-muted-foreground hover:text-foreground flex items-center gap-2">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3" />
                    </svg>
                    <span>Audio Only</span>
                    <svg
                      className="w-4 h-4 transition-transform group-open:rotate-180"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </summary>
                  <div className="mt-2">
                    <audio controls className="w-full" src={audioUrl}>
                      Your browser does not support audio playback.
                    </audio>
                  </div>
                </details>
              ) : (
                // Show audio player directly when no video
                <audio controls className="w-full" src={audioUrl}>
                  Your browser does not support audio playback.
                </audio>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

/**
 * Episode generation progress view.
 * Shows ProgressTracker and QualityPanel during episode generation.
 * Layout matches GeneratingView from the single podcast flow.
 */
function EpisodeProgressView({
  jobId,
  episodeNumber,
  episodeTitle,
  mode,
  cliffhangerType,
  onComplete,
  onError,
}: {
  jobId: string
  episodeNumber: number
  episodeTitle: string
  mode: string
  cliffhangerType?: CliffhangerType
  onComplete: (quality?: QualityReport | null) => void
  onError: (error: string) => void
}) {
  const [progress, setProgress] = useState<ProgressResponse>({
    job_id: jobId,
    phase: 'initializing',
    message: 'Starting episode generation...',
    progress_percent: 0,
    current_step: 0,
    total_steps: 0,
    elapsed_seconds: 0,
  })
  const [quality, setQuality] = useState<QualityReport | null>(null)
  const [wsConnection, setWsConnection] = useState<ProgressWebSocket | null>(null)

  // Use ref to capture latest quality for onComplete callback
  const qualityRef = useRef<QualityReport | null>(null)

  useEffect(() => {
    // Create WebSocket connection for progress updates
    const ws = createProgressConnection(jobId, {
      onProgress: (update) => {
        setProgress(update)
        if (update.quality) {
          setQuality(update.quality)
          qualityRef.current = update.quality
        }
      },
      onComplete: () => {
        // Pass final quality data to parent
        onComplete(qualityRef.current)
      },
      onError: (error) => {
        onError(error)
      },
    })

    setWsConnection(ws)

    return () => {
      ws.disconnect()
    }
  }, [jobId, onComplete, onError])

  const isComplete = progress.phase === 'complete'

  const cliffhangerColors: Record<CliffhangerType, string> = {
    revelation: 'text-purple-400',
    twist: 'text-red-400',
    question: 'text-cyan-400',
    countdown: 'text-orange-400',
    promise: 'text-green-400',
  }

  return (
    <div className="animate-slide-in-up mb-8">
      {/* Centered header */}
      <div className="text-center mb-6">
        <p className="text-sm text-muted-foreground mb-2">
          Generating Episode {episodeNumber}...
          <span className="ml-2 text-xs px-2 py-0.5 bg-secondary rounded">{mode} mode</span>
        </p>
        <h2 className="text-lg font-medium max-w-md mx-auto text-foreground">
          &ldquo;{episodeTitle}&rdquo;
        </h2>
        {cliffhangerType && (
          <p className={`text-xs mt-1 ${cliffhangerColors[cliffhangerType]}`}>
            Ending: {cliffhangerType.toUpperCase()} cliffhanger
          </p>
        )}
      </div>

      {/* Main content: Progress + Quality Panel side by side */}
      <div className="flex flex-col lg:flex-row gap-6 justify-center items-start">
        {/* Left: Progress Tracker */}
        <div className="flex-1 max-w-xl w-full space-y-6">
          <ProgressTracker progress={progress} />

          {/* Cancel Button */}
          {!isComplete && wsConnection && (
            <div className="text-center">
              <button
                className="btn-outline px-8"
                onClick={() => wsConnection.requestCancel()}
              >
                Cancel
              </button>
            </div>
          )}
        </div>

        {/* Right: Quality Panel (desktop) */}
        <div className="hidden lg:block">
          <QualityPanel quality={quality} isComplete={isComplete} />
        </div>
      </div>

      {/* Mobile Quality Panel (collapsed by default) */}
      <div className="lg:hidden mt-6">
        <details className="group">
          <summary className="cursor-pointer text-sm text-muted-foreground hover:text-foreground flex items-center justify-center gap-2">
            <span>Quality Metrics</span>
            <svg
              className="w-4 h-4 transition-transform group-open:rotate-180"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </summary>
          <div className="mt-4 flex justify-center">
            <QualityPanel quality={quality} isComplete={isComplete} />
          </div>
        </details>
      </div>
    </div>
  )
}

/**
 * Style DNA display component.
 */
function StyleDNADisplay({ styleDna }: {
  styleDna: {
    era: string
    genre: string
    geography?: string
    tone: string
    music_style: string
    voice_style: string
  }
}) {
  return (
    <div className="card">
      <h3 className="text-sm font-medium text-muted-foreground mb-3">Detected Style DNA</h3>
      <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
        <div>
          <span className="text-xs text-muted-foreground">Era</span>
          <p className="text-foreground font-medium">{styleDna.era}</p>
        </div>
        <div>
          <span className="text-xs text-muted-foreground">Genre</span>
          <p className="text-foreground font-medium">{styleDna.genre}</p>
        </div>
        {styleDna.geography && (
          <div>
            <span className="text-xs text-muted-foreground">Geography</span>
            <p className="text-foreground font-medium">{styleDna.geography}</p>
          </div>
        )}
        <div>
          <span className="text-xs text-muted-foreground">Tone</span>
          <p className="text-foreground font-medium">{styleDna.tone}</p>
        </div>
        <div>
          <span className="text-xs text-muted-foreground">Music Style</span>
          <p className="text-foreground font-medium text-sm">{styleDna.music_style || 'Era-appropriate'}</p>
        </div>
        <div>
          <span className="text-xs text-muted-foreground">Voice Style</span>
          <p className="text-foreground font-medium text-sm">{styleDna.voice_style || 'Natural'}</p>
        </div>
      </div>
    </div>
  )
}

/**
 * Main series detail page component.
 */
export default function SeriesDetailPage() {
  const params = useParams()
  const router = useRouter()
  const seriesId = params?.id as string

  const {
    currentSeries,
    isLoading,
    isApproving,
    isGenerating,
    generatingJobId,
    generatingEpisodeNumber,
    error,
    isAutoGenerating,
    pendingEpisodeNumbers,
    aggregateQuality,
    stopAfterCurrent,
    load,
    approve,
    generateEpisode,
    remove,
    clearError,
    clearGenerating,
    startAutoGeneration,
    stopAutoGeneration,
    handleEpisodeComplete,
  } = useSeries()

  // Store quality reports by episode number for display after generation
  const [episodeQuality, setEpisodeQuality] = useState<Record<number, QualityReport>>({})
  // Track which episode quality to show in modal
  const [showQualityModal, setShowQualityModal] = useState<number | null>(null)

  useEffect(() => {
    if (seriesId) {
      load(seriesId)
    }
  }, [seriesId, load])

  const handleApprove = async () => {
    try {
      await approve(seriesId, { approved: true })
    } catch (e) {
      // Error handled by hook
    }
  }

  const handleGenerateNext = async () => {
    try {
      await generateEpisode(seriesId)
    } catch (e) {
      // Error handled by hook
    }
  }

  const handleGenerateAll = async () => {
    if (!currentSeries) return
    const pendingEpisodes = currentSeries.episodes
      .filter((ep) => ep.status === 'pending')
      .map((ep) => ep.episode_number)
      .sort((a, b) => a - b)

    if (pendingEpisodes.length > 0) {
      await startAutoGeneration(seriesId, pendingEpisodes)
    }
  }

  const handleGenerationComplete = useCallback(async (quality?: QualityReport | null) => {
    // Store quality for the generated episode
    if (quality && generatingEpisodeNumber) {
      setEpisodeQuality((prev) => ({
        ...prev,
        [generatingEpisodeNumber]: quality,
      }))
    }

    // If auto-generating, handle episode completion (triggers next episode)
    if (isAutoGenerating && generatingEpisodeNumber) {
      const qualityForAggregate = quality?.overall_score
        ? { overall_score: quality.overall_score }
        : undefined
      await handleEpisodeComplete(seriesId, generatingEpisodeNumber, qualityForAggregate)
    }

    // Refresh series to get updated episode status
    await load(seriesId)
    clearGenerating()
  }, [seriesId, load, clearGenerating, generatingEpisodeNumber, isAutoGenerating, handleEpisodeComplete])

  const handleGenerationError = useCallback((errorMsg: string) => {
    clearGenerating()
    // Error will be shown through the hook's error state
  }, [clearGenerating])

  const handleDelete = async () => {
    if (confirm('Are you sure you want to delete this series?')) {
      await remove(seriesId)
      router.push('/')
    }
  }

  if (isLoading && !currentSeries) {
    return (
      <main className="min-h-screen">
        <Header />
        <div className="flex items-center justify-center py-24">
          <div className="text-center">
            <div className="animate-spin text-4xl text-primary mb-4">&#9696;</div>
            <p className="text-muted-foreground">Loading series...</p>
          </div>
        </div>
      </main>
    )
  }

  if (!currentSeries) {
    return (
      <main className="min-h-screen">
        <Header />
        <div className="flex items-center justify-center py-24">
          <div className="text-center">
            <p className="text-muted-foreground mb-4">Series not found</p>
            <Link href="/" className="text-primary hover:text-primary/80">
              Back to Home
            </Link>
          </div>
        </div>
      </main>
    )
  }

  const { outline, episodes, status, progress_percent, assets_generated } = currentSeries

  // Compute pending episodes for Generate All button
  const pendingEpisodes = episodes.filter((ep) => ep.status === 'pending')
  const showGenerateAllButton = status === 'in_progress' && pendingEpisodes.length > 1 && !isGenerating && !isAutoGenerating

  // Get generating episode info for headers
  const generatingEpisodeInfo = generatingEpisodeNumber
    ? outline.episodes.find((ep) => ep.episode_number === generatingEpisodeNumber)
    : null

  // Calculate average quality score
  const averageQualityScore = aggregateQuality.episodeCount > 0
    ? aggregateQuality.totalScore / aggregateQuality.episodeCount
    : undefined

  const statusColors: Record<SeriesStatus, string> = {
    draft: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/50',
    in_progress: 'bg-primary/20 text-primary border-primary/50',
    completed: 'bg-green-500/20 text-green-400 border-green-500/50',
    cancelled: 'bg-destructive/20 text-destructive border-destructive/50',
  }

  const nextPendingEpisode = episodes.find((ep) => ep.status === 'pending')
  const generatingEpisode = episodes.find((ep) => ep.status === 'generating')

  return (
    <main className="min-h-screen">
      <Header />

      {/* Sticky Series Progress Header during auto-generation */}
      {isAutoGenerating && generatingEpisodeNumber && generatingEpisodeInfo && (
        <SeriesProgressHeader
          seriesTitle={outline.title}
          episodes={outline.episodes}
          generatingEpisodeNumber={generatingEpisodeNumber}
          generatingEpisodeTitle={generatingEpisodeInfo.title}
          cliffhangerType={generatingEpisodeInfo.cliffhanger_type}
          averageScore={averageQualityScore}
          onStopAfterCurrent={stopAutoGeneration}
          stopRequested={stopAfterCurrent}
        />
      )}

      <div className="container mx-auto px-4 py-12 max-w-4xl">
        {/* Header */}
        <div className="flex items-start justify-between mb-6">
          <div>
            <Link href="/" className="text-sm text-muted-foreground hover:text-foreground mb-2 inline-block transition-colors">
              &larr; Back to Home
            </Link>
            <h1 className="text-3xl font-bold gradient-text">{outline.title}</h1>
            <p className="text-muted-foreground mt-1">{outline.description}</p>
          </div>
          <span className={`px-3 py-1 rounded border ${statusColors[status as SeriesStatus]}`}>
            {status.replace('_', ' ')}
          </span>
        </div>

        {error && (
          <div className="card border-destructive/50 bg-destructive/10 mb-6 flex items-center justify-between">
            <span className="text-destructive">{error}</span>
            <button onClick={clearError} className="text-destructive/70 hover:text-destructive text-xl">
              &times;
            </button>
          </div>
        )}

        {/* Progress bar for in-progress series */}
        {status === 'in_progress' && (
          <div className="card mb-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-muted-foreground">Series Progress</span>
              <span className="text-sm text-foreground font-medium">{Math.round(progress_percent)}%</span>
            </div>
            <div className="w-full h-3 bg-secondary rounded-full overflow-hidden">
              <div
                className="h-full bg-primary transition-all duration-500"
                style={{ width: `${progress_percent}%` }}
              />
            </div>
            {generatingEpisode && !generatingJobId && (
              <p className="text-sm text-primary mt-2 flex items-center gap-2">
                <span className="animate-pulse">●</span>
                Generating Episode {generatingEpisode.episode_number}...
              </p>
            )}
          </div>
        )}

        {/* Episode Generation Progress View - Full focus mode */}
        {generatingJobId && generatingEpisodeNumber ? (
          <EpisodeProgressView
            jobId={generatingJobId}
            episodeNumber={generatingEpisodeNumber}
            episodeTitle={generatingEpisodeInfo?.title || `Episode ${generatingEpisodeNumber}`}
            mode={currentSeries.mode}
            cliffhangerType={generatingEpisodeInfo?.cliffhanger_type}
            onComplete={handleGenerationComplete}
            onError={handleGenerationError}
          />
        ) : (
          <>
            {/* Style DNA */}
            <StyleDNADisplay styleDna={outline.style_dna} />

            {/* Draft status: Show outline for approval */}
            {status === 'draft' && (
          <div className="mt-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold text-foreground">Episode Outline</h2>
              <div className="flex gap-2">
                <button
                  onClick={handleDelete}
                  className="px-4 py-2 text-destructive hover:text-destructive/80 transition-colors"
                >
                  Delete
                </button>
                <button
                  onClick={handleApprove}
                  disabled={isApproving}
                  className="btn-create !w-auto !py-2 !text-base disabled:opacity-50"
                >
                  {isApproving ? (
                    <>
                      <span className="animate-spin mr-2">&#9696;</span>
                      Approving...
                    </>
                  ) : (
                    'Approve & Generate Assets'
                  )}
                </button>
              </div>
            </div>

            <div className="space-y-3">
              {outline.episodes.map((ep, i) => (
                <EpisodeOutlineCard key={ep.episode_number} episode={ep} index={i} />
              ))}
            </div>

            <p className="text-sm text-muted-foreground mt-4">
              Approving will generate series audio assets (intro, outro, stings) which takes 2-3 minutes.
            </p>
          </div>
        )}

        {/* In-progress or completed: Show generated episodes */}
        {(status === 'in_progress' || status === 'completed') && (
          <div className="mt-6">
            <div className="flex items-center justify-between mb-4 flex-wrap gap-3">
              <h2 className="text-xl font-semibold text-foreground">Episodes</h2>
              <div className="flex items-center gap-2 flex-wrap">
                {/* Generate All button */}
                {showGenerateAllButton && (
                  <button
                    onClick={handleGenerateAll}
                    className="btn-outline !py-2 !px-4 !text-sm"
                  >
                    Generate All ({pendingEpisodes.length})
                  </button>
                )}
                {/* Generate single episode button */}
                {status === 'in_progress' && nextPendingEpisode && !generatingEpisode && !isAutoGenerating && (
                  <button
                    onClick={handleGenerateNext}
                    disabled={isGenerating}
                    className="btn-create !w-auto !py-2 !text-base disabled:opacity-50"
                  >
                    {isGenerating ? (
                      <>
                        <span className="animate-spin mr-2">&#9696;</span>
                        Starting...
                      </>
                    ) : (
                      `Generate Episode ${nextPendingEpisode.episode_number}`
                    )}
                  </button>
                )}
              </div>
            </div>

            <div className="space-y-3">
              {episodes.map((ep) => (
                <GeneratedEpisodeCard
                  key={ep.id}
                  episode={ep}
                  quality={episodeQuality[ep.episode_number]}
                  onShowQuality={() => setShowQualityModal(ep.episode_number)}
                />
              ))}
            </div>

            {assets_generated && (
              <div className="mt-4 card text-sm text-muted-foreground">
                Series assets generated (intro, outro, cliffhanger stings)
              </div>
            )}
          </div>
        )}
          </>
        )}

        {/* Series info footer */}
        <div className="mt-8 pt-6 border-t border-border text-sm text-muted-foreground">
          <div className="flex flex-wrap gap-4">
            <span>{outline.episode_count} episodes</span>
            <span>{outline.episode_length === 'short' ? '5-10' : '10-20'} min each</span>
            <span>{outline.series_type}</span>
            {outline.themes.length > 0 && (
              <span>Themes: {outline.themes.join(', ')}</span>
            )}
          </div>
          <p className="mt-2">
            Created {new Date(currentSeries.created_at).toLocaleString()}
          </p>
        </div>
      </div>

      {/* Quality Report Modal */}
      {showQualityModal !== null && episodeQuality[showQualityModal] && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm"
          onClick={() => setShowQualityModal(null)}
        >
          <div
            className="relative max-h-[90vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Close button */}
            <button
              onClick={() => setShowQualityModal(null)}
              className="absolute -top-2 -right-2 z-10 p-2 bg-card border border-border rounded-full shadow-lg hover:bg-secondary transition-colors"
              aria-label="Close quality report"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>

            {/* Quality Panel */}
            <QualityPanel quality={episodeQuality[showQualityModal]} isComplete={true} />
          </div>
        </div>
      )}
    </main>
  )
}
