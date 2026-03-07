'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Header } from '@/components/Header'
import { PromptInput } from '@/components/PromptInput'
import { FileUpload } from '@/components/FileUpload'
import { DurationDropdown } from '@/components/DurationDropdown'
import { ProgressTracker } from '@/components/ProgressTracker'
import { OutputPlayer } from '@/components/OutputPlayer'
import { TrailerPreview } from '@/components/TrailerPreview'
import { QualityPanel } from '@/components/QualityPanel'
import { useGeneration } from '@/hooks/useGeneration'
import { useSeries } from '@/hooks/useSeries'
import { suggestTopic } from '@/lib/api'
import { STORAGE_KEYS } from '@/lib/constants'
import { PipelineMode, DurationOption, ProgressResponse, QualityReport, SeriesType, EpisodeLength } from '@/types'

/**
 * Collapsible section component for stacked card layout.
 */
function Section({
  title,
  defaultOpen = true,
  children,
}: {
  title: string
  defaultOpen?: boolean
  children: React.ReactNode
}) {
  const [isOpen, setIsOpen] = useState(defaultOpen)

  return (
    <div className="border-b border-border last:border-b-0">
      <button
        className="flex items-center justify-between w-full py-3 px-1 text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
        onClick={() => setIsOpen(!isOpen)}
      >
        {title}
        <svg
          className={`w-4 h-4 transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>
      {isOpen && <div className="pb-4">{children}</div>}
    </div>
  )
}

/**
 * Format error messages for user-friendly display.
 */
function formatErrorMessage(error: string): { title: string; message: string } {
  if (error.toLowerCase().includes('timed out')) {
    return {
      title: 'Generation Timed Out',
      message:
        'The generation took longer than expected and was automatically stopped. Try again, or use Normal mode for faster generation.',
    }
  }
  return { title: 'Generation Failed', message: error }
}

/**
 * Generating view shown during podcast creation.
 * Displays prompt, progress tracker, quality panel, trailer preview, and cancel button.
 */
function GeneratingView({
  prompt,
  progress,
  quality,
  trailer,
  showTrailer,
  onCancel,
}: {
  prompt: string
  progress: ProgressResponse | null
  quality: QualityReport | null
  trailer: { url: string; duration_seconds: number } | null
  showTrailer: boolean
  onCancel: () => void
}) {
  return (
    <div className="animate-slide-in-up">
      {/* Topic being generated */}
      <div className="text-center mb-6">
        <p className="text-sm text-muted-foreground mb-2">Creating podcast...</p>
        <h2 className="text-lg font-medium max-w-md mx-auto text-foreground">
          &ldquo;{prompt || 'Uploaded content'}&rdquo;
        </h2>
      </div>

      {/* Main content: Progress + Quality Panel side by side */}
      <div className="flex flex-col lg:flex-row gap-6 justify-center items-start">
        {/* Left: Progress Tracker and Trailer */}
        <div className="flex-1 max-w-xl w-full space-y-6">
          {/* Progress Tracker */}
          {progress && <ProgressTracker progress={progress} />}

          {/* Trailer Preview (when ready) */}
          {trailer && showTrailer && (
            <TrailerPreview
              trailerUrl={`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}${trailer.url}`}
              duration={trailer.duration_seconds}
              isFullReady={false}
              onViewFull={() => {}}
            />
          )}

          {/* Cancel Button */}
          <div className="text-center">
            <button
              className="btn-outline px-8"
              onClick={onCancel}
            >
              Cancel
            </button>
          </div>
        </div>

        {/* Right: Quality Panel */}
        <div className="hidden lg:block">
          <QualityPanel quality={quality} isComplete={false} />
        </div>
      </div>

      {/* Mobile Quality Panel (collapsed by default, shown below progress) */}
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
            <QualityPanel quality={quality} isComplete={false} />
          </div>
        </details>
      </div>
    </div>
  )
}

/**
 * Main podcast generation page.
 *
 * Suno AI-inspired centered stacked card layout with collapsible sections.
 */
export default function Home() {
  const router = useRouter()

  // Creation mode: single podcast or series
  const [creationMode, setCreationMode] = useState<'single' | 'series'>('single')

  // Form state (shared)
  const [prompt, setPrompt] = useState('')
  const [guidance, setGuidance] = useState('')
  const [mode, setMode] = useState<PipelineMode>('normal')
  const [isSuggestingTopic, setIsSuggestingTopic] = useState(false)

  // Single podcast state
  const [duration, setDuration] = useState<DurationOption>(5)
  const [conversationalStyle, setConversationalStyle] = useState(false)
  const [uploadedFiles, setUploadedFiles] = useState<string[]>([])

  // Series state
  const [episodeCount, setEpisodeCount] = useState(5)
  const [episodeLength, setEpisodeLength] = useState<EpisodeLength>('short')
  const [seriesType, setSeriesType] = useState<SeriesType>('documentary')

  // Generation hook handles all API interactions
  const {
    status,
    progress,
    result,
    error,
    trailer,
    quality,
    startGeneration,
    cancelGeneration,
    reset,
  } = useGeneration()

  // Series hook for series creation
  const { create: createSeries, isCreating: isCreatingSeries, error: seriesError } = useSeries()

  // Track whether user dismissed trailer to view full result
  const [showTrailer, setShowTrailer] = useState(true)

  // Check for reuse data from History page on mount
  useEffect(() => {
    const reuseData = sessionStorage.getItem(STORAGE_KEYS.REUSE_JOB)
    if (reuseData) {
      try {
        const data = JSON.parse(reuseData)
        if (data.prompt) setPrompt(data.prompt)
        if (data.guidance) setGuidance(data.guidance)
        if (data.mode) setMode(data.mode)
        if (data.duration) setDuration(data.duration)
        if (data.conversational_style !== undefined) setConversationalStyle(data.conversational_style)
      } catch {
        // Ignore invalid JSON
      }
      // Clear after reading
      sessionStorage.removeItem(STORAGE_KEYS.REUSE_JOB)
    }
  }, [])

  /**
   * Handle form submission to start generation.
   */
  const handleGenerate = async () => {
    if (!prompt && uploadedFiles.length === 0) return

    await startGeneration({
      prompt: prompt || undefined,
      file_ids: uploadedFiles.length > 0 ? uploadedFiles : undefined,
      guidance: guidance || undefined,
      mode,
      // Only pass duration if not 'auto' - backend will extract from prompt or use default
      target_duration_minutes: duration !== 'auto' ? duration : undefined,
      conversational_style: conversationalStyle,
    })
  }

  const handleFileUploaded = (fileId: string) => {
    setUploadedFiles((prev) => [...prev, fileId])
  }

  const handleFileRemoved = (fileId: string) => {
    setUploadedFiles((prev) => prev.filter((id) => id !== fileId))
  }

  const handleReset = () => {
    setPrompt('')
    setGuidance('')
    setDuration(5)
    setConversationalStyle(false)
    setUploadedFiles([])
    setShowTrailer(true)
    reset()
  }

  /**
   * Handle suggesting a topic via the AI.
   */
  const handleSuggestTopic = async () => {
    if (isSuggestingTopic || isGenerating) return
    setIsSuggestingTopic(true)
    try {
      const { topic } = await suggestTopic()
      setPrompt(topic)
    } catch {
      // Silently fail — user can just type manually
    } finally {
      setIsSuggestingTopic(false)
    }
  }

  /**
   * Handle series creation.
   */
  const handleCreateSeries = async () => {
    if (!prompt) return

    try {
      const series = await createSeries({
        prompt,
        episode_count: episodeCount,
        episode_length: episodeLength,
        series_type: seriesType,
        mode,
        guidance: guidance || undefined,
      })
      // Navigate to series detail page for outline approval
      router.push(`/series/${series.id}`)
    } catch {
      // Error handled by hook
    }
  }

  // Determine UI state
  const isGenerating = status === 'running' || status === 'pending'
  const isComplete = status === 'completed'
  const hasFailed = status === 'failed'
  const canGenerateSingle = (prompt || uploadedFiles.length > 0) && !isGenerating
  const canCreateSeries = prompt && !isCreatingSeries
  const canSubmit = creationMode === 'single' ? canGenerateSingle : canCreateSeries

  return (
    <main className="min-h-screen">
      <Header />

      <div className={`container mx-auto px-4 py-12 ${isComplete ? 'max-w-6xl' : isGenerating ? 'max-w-4xl' : 'max-w-xl'}`}>
        {/* Title */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold gradient-text mb-2">
            Create a Podcast
          </h1>
          <p className="text-sm text-muted-foreground">
            Enter a topic, upload content, or both — AI does the rest.
          </p>
        </div>

        {/* Form View - shown when not generating and not complete */}
        {!isGenerating && !isComplete && (
          <div className="space-y-5 animate-slide-in-up">
            {/* Creation Mode Toggle */}
            <div className="flex justify-center gap-2">
              <button
                className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors
                  ${creationMode === 'single'
                    ? 'bg-primary/20 text-primary border border-primary/30'
                    : 'bg-secondary/80 text-muted-foreground hover:text-foreground'}`}
                onClick={() => setCreationMode('single')}
              >
                Single Podcast
              </button>
              <button
                className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors
                  ${creationMode === 'series'
                    ? 'bg-primary/20 text-primary border border-primary/30'
                    : 'bg-secondary/80 text-muted-foreground hover:text-foreground'}`}
                onClick={() => setCreationMode('series')}
              >
                Series
              </button>
            </div>

            {/* Stacked Card */}
            <div className="card">
              {/* Section: Describe your podcast */}
              <Section title="Describe your podcast" defaultOpen={true}>
                <div className="relative">
                  <PromptInput
                    value={prompt}
                    onChange={setPrompt}
                    placeholder="The history of electronic music, AI breakthroughs in 2025..."
                    disabled={false}
                  />
                  {/* Inline controls at bottom of textarea */}
                  <div className="absolute bottom-2.5 left-3 right-3 flex items-center justify-between flex-wrap gap-y-2">
                    {/* Left: Mode and Style toggles */}
                    <div className="flex items-center gap-2">
                      {/* Mode Toggle */}
                      <button
                        className={`px-2.5 py-1 text-xs font-medium rounded-md transition-colors
                          ${mode === 'pro'
                            ? 'text-purple-400 bg-purple-400/10'
                            : 'text-muted-foreground bg-secondary/80 hover:bg-secondary hover:text-foreground'
                          }`}
                        onClick={() => setMode(mode === 'normal' ? 'pro' : 'normal')}
                        title={mode === 'normal'
                          ? "Normal mode: Fast generation (~2 min). Click for Pro mode."
                          : "Pro mode: Higher quality (~6 min). Click for Normal mode."}
                      >
                        {mode === 'normal' ? 'Normal' : 'Pro'}
                      </button>

                      {creationMode === 'single' ? (
                        <>
                          {/* Multiple Hosts Toggle */}
                          <button
                            className={`flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium rounded-md transition-colors
                              ${conversationalStyle
                                ? 'text-cyan-400 bg-cyan-400/10'
                                : 'text-muted-foreground bg-secondary/80 hover:bg-secondary hover:text-foreground'
                              }`}
                            onClick={() => setConversationalStyle(!conversationalStyle)}
                            aria-label="Toggle multiple hosts"
                            aria-pressed={conversationalStyle}
                            title={conversationalStyle
                              ? "Multiple hosts: ON (dynamic multi-host dialogue)"
                              : "Multiple hosts: OFF (click to enable multi-host format)"}
                          >
                            <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                                d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                            </svg>
                            <span className="hidden sm:inline">Multiple Hosts</span>
                          </button>
                          {/* Duration Dropdown */}
                          <DurationDropdown
                            duration={duration}
                            onDurationChange={setDuration}
                            disabled={false}
                          />
                        </>
                      ) : (
                        <>
                          {/* Episode Count Dropdown */}
                          <select
                            className="px-2.5 py-1 text-xs font-medium rounded-md bg-secondary/80 text-muted-foreground hover:text-foreground transition-colors cursor-pointer"
                            value={episodeCount}
                            onChange={(e) => setEpisodeCount(Number(e.target.value))}
                            title="Number of episodes in the series"
                          >
                            {[3, 4, 5, 6, 8, 10, 12, 15, 20].map(n => (
                              <option key={n} value={n}>{n} episodes</option>
                            ))}
                          </select>

                          {/* Episode Length Dropdown */}
                          <select
                            className="px-2.5 py-1 text-xs font-medium rounded-md bg-secondary/80 text-muted-foreground hover:text-foreground transition-colors cursor-pointer"
                            value={episodeLength}
                            onChange={(e) => setEpisodeLength(e.target.value as EpisodeLength)}
                            title="Duration of each episode"
                          >
                            <option value="short">Short (5-10 min)</option>
                            <option value="medium">Medium (10-20 min)</option>
                          </select>

                          {/* Series Type Dropdown */}
                          <select
                            className="px-2.5 py-1 text-xs font-medium rounded-md bg-secondary/80 text-muted-foreground hover:text-foreground transition-colors cursor-pointer"
                            value={seriesType}
                            onChange={(e) => setSeriesType(e.target.value as SeriesType)}
                            title="Style of series storytelling"
                          >
                            <option value="documentary">Documentary</option>
                            <option value="narrative">Narrative</option>
                            <option value="hybrid">Hybrid</option>
                          </select>
                        </>
                      )}
                    </div>
                    {/* Right: Suggest Topic */}
                    <button
                      className="flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium rounded-md bg-secondary/80 hover:bg-secondary transition-colors disabled:opacity-40 disabled:cursor-not-allowed shrink-0"
                      onClick={handleSuggestTopic}
                      disabled={isSuggestingTopic}
                      aria-label="Suggest a topic"
                      title="Suggest a topic"
                    >
                      <svg
                        className={`w-4 h-4 text-amber-400 ${isSuggestingTopic ? 'animate-spin' : ''}`}
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 00-2.455 2.456zM16.894 20.567L16.5 21.75l-.394-1.183a2.25 2.25 0 00-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 001.423-1.423l.394-1.183.394 1.183a2.25 2.25 0 001.423 1.423l1.183.394-1.183.394a2.25 2.25 0 00-1.423 1.423z"
                        />
                      </svg>
                      <span className="hidden sm:inline text-muted-foreground whitespace-nowrap">Surprise me</span>
                    </button>
                  </div>
                </div>
              </Section>

              {/* Section: Style */}
              <Section title="Style" defaultOpen={true}>
                <input
                  type="text"
                  className="input"
                  placeholder="e.g., For beginners, Technical deep-dive, Casual tone..."
                  value={guidance}
                  onChange={(e) => setGuidance(e.target.value)}
                />
              </Section>

              {/* Section: Upload Files — collapsed by default, single mode only */}
              {creationMode === 'single' && (
                <Section title="Upload Files" defaultOpen={false}>
                  <FileUpload
                    onFileUploaded={handleFileUploaded}
                    onFileRemoved={handleFileRemoved}
                    uploadedFiles={uploadedFiles}
                    disabled={false}
                  />
                </Section>
              )}
            </div>

            {/* Create Button */}
            <button
              className="btn-create"
              onClick={creationMode === 'single' ? handleGenerate : handleCreateSeries}
              disabled={!canSubmit}
            >
              {creationMode === 'single' ? 'Create Podcast' : (isCreatingSeries ? 'Creating Series...' : 'Create Series')}
            </button>

            {/* Error Message - Single Podcast */}
            {hasFailed && error && (() => {
              const { title, message } = formatErrorMessage(error)
              return (
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
                      <h3 className="font-medium text-destructive">{title}</h3>
                      <p className="text-sm text-muted-foreground mt-1">{message}</p>
                    </div>
                  </div>
                  <button className="btn-secondary mt-4" onClick={handleReset}>
                    Try Again
                  </button>
                </div>
              )
            })()}

            {/* Error Message - Series */}
            {seriesError && (
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
                    <h3 className="font-medium text-destructive">Series Creation Failed</h3>
                    <p className="text-sm text-muted-foreground mt-1">{seriesError}</p>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Generating View - slides in when generation starts */}
        {isGenerating && (
          <GeneratingView
            prompt={prompt}
            progress={progress}
            quality={quality}
            trailer={trailer}
            showTrailer={showTrailer}
            onCancel={cancelGeneration}
          />
        )}

        {/* Output Player */}
        {isComplete && result && (
          <div className="animate-in">
            <OutputPlayer result={result} onReset={handleReset} quality={quality} />
          </div>
        )}
      </div>
    </main>
  )
}
