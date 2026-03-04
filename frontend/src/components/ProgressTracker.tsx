'use client'

import { useState, useEffect, useRef } from 'react'
import { ProgressResponse, GenerationPhase, PhaseTimings, ParallelStatus } from '@/types'

interface ProgressTrackerProps {
  /** Current progress data */
  progress: ProgressResponse
}

/**
 * Visual progress tracker component.
 *
 * Displays the current generation phase with a progress bar
 * and detailed status information. Includes per-phase timing
 * and a client-side elapsed timer that ticks independently of server updates.
 *
 * @param progress - Current progress data from the API
 */
export function ProgressTracker({ progress }: ProgressTrackerProps) {
  // Client-side elapsed timer: anchors to server value, ticks locally
  const [displayElapsed, setDisplayElapsed] = useState(0)
  const anchorRef = useRef<{ serverElapsed: number; anchoredAt: number } | null>(null)

  // Per-phase active timer
  const [activePhaseElapsed, setActivePhaseElapsed] = useState(0)
  const phaseAnchorRef = useRef<{ serverElapsed: number; anchoredAt: number } | null>(null)

  // Extract phase timing data from details
  const phaseTimings = (progress.details as PhaseTimings | undefined)?.phase_timings ?? {}
  const serverCurrentPhaseElapsed = (progress.details as PhaseTimings | undefined)?.current_phase_elapsed ?? 0

  // Anchor to server elapsed_seconds whenever it changes
  useEffect(() => {
    if (progress.elapsed_seconds > 0) {
      anchorRef.current = {
        serverElapsed: progress.elapsed_seconds,
        anchoredAt: Date.now() / 1000,
      }
      setDisplayElapsed(progress.elapsed_seconds)
    }
  }, [progress.elapsed_seconds])

  // Anchor to server current_phase_elapsed whenever it changes
  useEffect(() => {
    if (serverCurrentPhaseElapsed > 0) {
      phaseAnchorRef.current = {
        serverElapsed: serverCurrentPhaseElapsed,
        anchoredAt: Date.now() / 1000,
      }
      setActivePhaseElapsed(serverCurrentPhaseElapsed)
    }
  }, [serverCurrentPhaseElapsed])

  // Reset phase anchor on phase change
  useEffect(() => {
    phaseAnchorRef.current = null
    setActivePhaseElapsed(0)
  }, [progress.phase])

  // Tick every second while generation is active
  useEffect(() => {
    const isTerminal = progress.phase === 'complete' || progress.phase === 'error'
    if (isTerminal) {
      setDisplayElapsed(0)
      return
    }

    const interval = setInterval(() => {
      // Total elapsed - read from current ref values to avoid stale closures
      if (anchorRef.current) {
        const now = Date.now() / 1000
        const delta = now - anchorRef.current.anchoredAt
        setDisplayElapsed(anchorRef.current.serverElapsed + delta)
      } else {
        setDisplayElapsed((prev) => prev + 1)
      }

      // Active phase elapsed - read from current ref values to avoid stale closures
      if (phaseAnchorRef.current) {
        const now = Date.now() / 1000
        const delta = now - phaseAnchorRef.current.anchoredAt
        setActivePhaseElapsed(phaseAnchorRef.current.serverElapsed + delta)
      } else {
        setActivePhaseElapsed((prev) => prev + 1)
      }
    }, 1000)

    return () => clearInterval(interval)
  }, [progress.phase])

  // Extract parallel sub-progress from details
  const parallelStatus = (progress.details as Record<string, unknown> | undefined)?.parallel_status as ParallelStatus | undefined

  const phases: { id: GenerationPhase; label: string; icon: string }[] = [
    { id: 'analyzing', label: 'Analyzing', icon: '🔍' },
    { id: 'scripting', label: 'Scripting', icon: '✍️' },
    { id: 'generating_assets', label: 'Assets', icon: '⚡' },
    { id: 'mixing_audio', label: 'Mixing', icon: '🎛️' },
    { id: 'assembling_video', label: 'Video', icon: '🎬' },
  ]

  /**
   * Get the index of the current phase.
   */
  const getCurrentPhaseIndex = (): number => {
    const index = phases.findIndex((p) => p.id === progress.phase)
    return index >= 0 ? index : 0
  }

  /**
   * Format seconds into a compact display string.
   */
  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  /**
   * Format seconds for per-phase display (compact).
   */
  const formatPhaseDuration = (seconds: number): string => {
    if (seconds < 60) return `${Math.round(seconds)}s`
    const mins = Math.floor(seconds / 60)
    const secs = Math.round(seconds % 60)
    return `${mins}m ${secs}s`
  }

  // Determine mode from details or phase for initial ETA
  const isProMode = progress.details && 'config_used' in (progress.details as Record<string, unknown>)
  const modeEstimate = isProMode ? '~4-6 minutes' : '~1-2 minutes'

  const currentIndex = getCurrentPhaseIndex()
  const isComplete = progress.phase === 'complete'
  const isError = progress.phase === 'error'

  return (
    <div className="card space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="font-semibold text-lg">Generating Podcast</h3>
          <p className="text-sm text-muted-foreground">{progress.message}</p>
        </div>
        <div className="text-right">
          <p className="text-2xl font-bold tabular-nums">
            {Math.round(progress.progress_percent)}%
          </p>
          {progress.eta_seconds && progress.eta_seconds > 0 ? (
            <p className="text-xs text-muted-foreground">
              ~{formatTime(progress.eta_seconds)} remaining
            </p>
          ) : (
            !isComplete && !isError && progress.progress_percent < 5 && (
              <p className="text-xs text-muted-foreground">
                Typically takes {modeEstimate}
              </p>
            )
          )}
        </div>
      </div>

      {/* Progress Bar */}
      <div className="relative h-3 bg-secondary rounded-full overflow-hidden">
        <div
          className="absolute inset-y-0 left-0 bg-gradient-to-r from-primary to-accent rounded-full transition-all duration-500"
          style={{ width: `${progress.progress_percent}%` }}
        />
        <div className="absolute inset-0 progress-shimmer" />
      </div>

      {/* Phase Timeline */}
      <div className="flex justify-between">
        {phases.map((phase, index) => {
          const isActive = index === currentIndex && !isComplete
          const isCompleted = index < currentIndex || isComplete
          const isPending = index > currentIndex && !isComplete

          // Get timing for this phase
          const completedDuration = phaseTimings[phase.id]
          const hasCompletedTiming = isCompleted && completedDuration !== undefined

          return (
            <div
              key={phase.id}
              className={`
                flex flex-col items-center gap-1 transition-all
                ${isActive ? 'scale-110' : ''}
              `}
            >
              <div
                className={`
                  w-10 h-10 rounded-full flex items-center justify-center text-lg
                  transition-all duration-300
                  ${isActive ? 'bg-primary text-primary-foreground ring-4 ring-primary/20 animate-pulse' : ''}
                  ${isCompleted ? 'bg-success/20 text-success' : ''}
                  ${isPending ? 'bg-secondary text-muted-foreground' : ''}
                  ${isError && isActive ? 'bg-destructive/20 text-destructive' : ''}
                `}
              >
                {isCompleted ? '✓' : phase.icon}
              </div>
              <span
                className={`
                  text-xs font-medium hidden sm:block
                  ${isActive ? 'text-primary' : ''}
                  ${isCompleted ? 'text-success' : ''}
                  ${isPending ? 'text-muted-foreground' : ''}
                `}
              >
                {phase.label}
              </span>
              {/* Per-phase timing */}
              <span
                className={`
                  text-[10px] tabular-nums hidden sm:block
                  ${hasCompletedTiming ? 'text-muted-foreground' : ''}
                  ${isActive ? 'text-primary font-medium' : ''}
                `}
              >
                {hasCompletedTiming && formatPhaseDuration(completedDuration)}
                {isActive && !isComplete && (
                  <span className="animate-pulse">{formatPhaseDuration(activePhaseElapsed)}</span>
                )}
              </span>
            </div>
          )
        })}
      </div>

      {/* Parallel Asset Sub-Progress */}
      {progress.phase === 'generating_assets' && parallelStatus && (
        <div className="space-y-2">
          <div
            className="flex justify-center gap-6 text-xs tabular-nums cursor-help"
            title={`Voice: ${parallelStatus.tts.elapsed_s ?? 0}s (${parallelStatus.tts.done}/${parallelStatus.tts.total}) | Music: ${parallelStatus.bgm.elapsed_s ?? 0}s (${parallelStatus.bgm.done}/${parallelStatus.bgm.total}) | Images: ${parallelStatus.images.elapsed_s ?? 0}s (${parallelStatus.images.done}/${parallelStatus.images.total})`}
          >
            <span className={parallelStatus.tts.done >= parallelStatus.tts.total ? 'text-success' : 'text-muted-foreground'}>
              🎙️ Voice {parallelStatus.tts.done}/{parallelStatus.tts.total}
              {parallelStatus.tts.elapsed_s !== undefined && parallelStatus.tts.elapsed_s > 0 && (
                <span className="text-muted-foreground ml-1">({parallelStatus.tts.elapsed_s}s)</span>
              )}
            </span>
            <span className={parallelStatus.bgm.done >= parallelStatus.bgm.total ? 'text-success' : 'text-muted-foreground'}>
              🎵 Music {parallelStatus.bgm.done}/{parallelStatus.bgm.total}
              {parallelStatus.bgm.elapsed_s !== undefined && parallelStatus.bgm.elapsed_s > 0 && (
                <span className="text-muted-foreground ml-1">({parallelStatus.bgm.elapsed_s}s)</span>
              )}
            </span>
            <span className={parallelStatus.images.done >= parallelStatus.images.total ? 'text-success' : 'text-muted-foreground'}>
              🖼️ Images {parallelStatus.images.done}/{parallelStatus.images.total}
              {parallelStatus.images.elapsed_s !== undefined && parallelStatus.images.elapsed_s > 0 && (
                <span className="text-muted-foreground ml-1">({parallelStatus.images.elapsed_s}s)</span>
              )}
            </span>
          </div>
          {/* Asset generation preview text */}
          {(() => {
            const previewText = (progress.details as Record<string, unknown> | undefined)?.preview
            return previewText ? (
              <p className="text-xs text-muted-foreground text-center italic truncate px-4">
                {String(previewText)}
              </p>
            ) : null
          })()}
        </div>
      )}

      {/* Step Counter */}
      {progress.total_steps > 0 && (
        <div className="flex justify-center">
          <span className="badge bg-secondary text-muted-foreground">
            Step {progress.current_step} of {progress.total_steps}
          </span>
        </div>
      )}

      {/* Preview Text */}
      {progress.preview && (
        <div className="p-4 rounded-lg bg-secondary/50 border border-border">
          <p className="text-xs text-muted-foreground mb-1">Preview:</p>
          <p className="text-sm italic line-clamp-3">{progress.preview}</p>
        </div>
      )}

      {/* Elapsed Time */}
      <div className="flex justify-center">
        <p className="text-xs text-muted-foreground">
          Elapsed: {formatTime(displayElapsed)}
        </p>
      </div>

      {/* Timing Breakdown Summary (shown on complete or error) */}
      {(isComplete || isError) && Object.keys(phaseTimings).length > 0 && (
        <div className="p-4 rounded-lg bg-secondary/50 border border-border text-xs tabular-nums space-y-1">
          <p className="font-medium text-sm mb-2">Timing Breakdown</p>
          {phaseTimings['scripting'] !== undefined && (
            <div className="flex justify-between">
              <span className="text-muted-foreground">Scripting</span>
              <span>{formatPhaseDuration(phaseTimings['scripting'])}</span>
            </div>
          )}
          {phaseTimings['generating_assets'] !== undefined && (
            <>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Assets</span>
                <span>{formatPhaseDuration(phaseTimings['generating_assets'])} <span className="text-muted-foreground">(parallel)</span></span>
              </div>
              {phaseTimings['tts'] !== undefined && (
                <div className="flex justify-between pl-4">
                  <span className="text-muted-foreground">├ Voice</span>
                  <span>{formatPhaseDuration(phaseTimings['tts'])}</span>
                </div>
              )}
              {phaseTimings['bgm'] !== undefined && (
                <div className="flex justify-between pl-4">
                  <span className="text-muted-foreground">├ Music</span>
                  <span>{formatPhaseDuration(phaseTimings['bgm'])}</span>
                </div>
              )}
              {phaseTimings['images'] !== undefined && (
                <div className="flex justify-between pl-4">
                  <span className="text-muted-foreground">└ Images</span>
                  <span>{formatPhaseDuration(phaseTimings['images'])}</span>
                </div>
              )}
            </>
          )}
          {phaseTimings['mixing_audio'] !== undefined && (
            <div className="flex justify-between">
              <span className="text-muted-foreground">Mixing</span>
              <span>{formatPhaseDuration(phaseTimings['mixing_audio'])}</span>
            </div>
          )}
          {phaseTimings['assembling_video'] !== undefined && (
            <div className="flex justify-between">
              <span className="text-muted-foreground">Video</span>
              <span>{formatPhaseDuration(phaseTimings['assembling_video'])}</span>
            </div>
          )}
          <div className="border-t border-border pt-1 mt-1 flex justify-between font-medium">
            <span>Total</span>
            <span>{formatPhaseDuration(displayElapsed)}</span>
          </div>
        </div>
      )}
    </div>
  )
}
