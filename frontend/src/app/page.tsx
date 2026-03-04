'use client'

import { useState, useEffect } from 'react'
import { Header } from '@/components/Header'
import { PromptInput } from '@/components/PromptInput'
import { FileUpload } from '@/components/FileUpload'
import { ModeSelector } from '@/components/ModeSelector'
import { DurationSelector } from '@/components/DurationSelector'
import { ProgressTracker } from '@/components/ProgressTracker'
import { OutputPlayer } from '@/components/OutputPlayer'
import { TrailerPreview } from '@/components/TrailerPreview'
import { useGeneration } from '@/hooks/useGeneration'
import { suggestTopic } from '@/lib/api'
import { STORAGE_KEYS } from '@/lib/constants'
import { PipelineMode, DurationOption } from '@/types'

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
 * Main podcast generation page.
 *
 * Suno AI-inspired centered stacked card layout with collapsible sections.
 */
export default function Home() {
  // Form state
  const [prompt, setPrompt] = useState('')
  const [guidance, setGuidance] = useState('')
  const [mode, setMode] = useState<PipelineMode>('normal')
  const [duration, setDuration] = useState<DurationOption>('auto')
  const [uploadedFiles, setUploadedFiles] = useState<string[]>([])
  const [isSuggestingTopic, setIsSuggestingTopic] = useState(false)

  // Generation hook handles all API interactions
  const {
    status,
    progress,
    result,
    error,
    trailer,
    startGeneration,
    cancelGeneration,
    reset,
  } = useGeneration()

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
    setDuration('auto')
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

  // Determine UI state
  const isGenerating = status === 'running' || status === 'pending'
  const isComplete = status === 'completed'
  const hasFailed = status === 'failed'
  const canGenerate = (prompt || uploadedFiles.length > 0) && !isGenerating

  return (
    <main className="min-h-screen">
      <Header />

      <div className={`container mx-auto px-4 py-12 ${isComplete ? 'max-w-6xl' : 'max-w-xl'}`}>
        {/* Title */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold gradient-text mb-2">
            Create a Podcast
          </h1>
          <p className="text-sm text-muted-foreground">
            Enter a topic, upload content, or both — AI does the rest.
          </p>
        </div>

        {/* Generation Form */}
        {!isComplete && (
          <div className="space-y-5 animate-in">
            {/* Stacked Card */}
            <div className="card">
              {/* Section: Describe your podcast */}
              <Section title="Describe your podcast" defaultOpen={true}>
                <div className="relative">
                  <PromptInput
                    value={prompt}
                    onChange={setPrompt}
                    placeholder="The history of electronic music, AI breakthroughs in 2025..."
                    disabled={isGenerating}
                  />
                  <button
                    className="absolute top-2 right-2 p-1.5 rounded-md hover:bg-secondary transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                    onClick={handleSuggestTopic}
                    disabled={isGenerating || isSuggestingTopic}
                    aria-label="Suggest a topic"
                    title="Suggest a topic"
                  >
                    <svg
                      className={`w-5 h-5 text-amber-400 ${isSuggestingTopic ? 'animate-spin' : ''}`}
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
                  </button>
                </div>
              </Section>

              {/* Section: Style & Mode */}
              <Section title="Style & Mode" defaultOpen={true}>
                <div className="space-y-4">
                  <input
                    type="text"
                    className="input"
                    placeholder="e.g., For beginners, Technical deep-dive, Casual tone..."
                    value={guidance}
                    onChange={(e) => setGuidance(e.target.value)}
                    disabled={isGenerating}
                  />
                  <div className="flex items-center gap-3">
                    <span className="text-xs text-muted-foreground">Mode</span>
                    <ModeSelector
                      mode={mode}
                      onModeChange={setMode}
                      disabled={isGenerating}
                    />
                  </div>
                  <DurationSelector
                    duration={duration}
                    onDurationChange={setDuration}
                    disabled={isGenerating}
                  />
                </div>
              </Section>

              {/* Section: Upload Files — collapsed by default */}
              <Section title="Upload Files" defaultOpen={false}>
                <FileUpload
                  onFileUploaded={handleFileUploaded}
                  onFileRemoved={handleFileRemoved}
                  uploadedFiles={uploadedFiles}
                  disabled={isGenerating}
                />
              </Section>
            </div>

            {/* Create Button */}
            {!isGenerating && (
              <button
                className="btn-create"
                onClick={handleGenerate}
                disabled={!canGenerate}
              >
                Create Podcast
              </button>
            )}

            {/* Cancel Button */}
            {isGenerating && (
              <button
                className="btn-outline w-full py-3"
                onClick={cancelGeneration}
              >
                Cancel
              </button>
            )}

            {/* Error Message */}
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
          </div>
        )}

        {/* Progress Tracker */}
        {isGenerating && progress && (
          <div className="mt-6 animate-in">
            <ProgressTracker progress={progress} />
          </div>
        )}

        {/* Trailer Preview - shows while full podcast is generating */}
        {trailer && showTrailer && !result && isGenerating && (
          <div className="mt-6 animate-in">
            <TrailerPreview
              trailerUrl={`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}${trailer.url}`}
              duration={trailer.duration_seconds}
              isFullReady={!!result}
              onViewFull={() => setShowTrailer(false)}
            />
          </div>
        )}

        {/* Output Player */}
        {isComplete && result && (
          <div className="animate-in">
            <OutputPlayer result={result} onReset={handleReset} />
          </div>
        )}
      </div>
    </main>
  )
}
