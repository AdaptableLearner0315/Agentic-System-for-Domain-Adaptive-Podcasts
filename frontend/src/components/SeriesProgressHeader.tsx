/**
 * Series Progress Header Component
 *
 * Sticky header that displays series generation progress during auto-generation.
 * Shows episode status chips, current episode info, and stop controls.
 */

import type { EpisodeSummary, CliffhangerType } from '@/types'

interface SeriesProgressHeaderProps {
  /** Series title */
  seriesTitle: string
  /** All episodes with their status */
  episodes: EpisodeSummary[]
  /** Currently generating episode number */
  generatingEpisodeNumber: number
  /** Title of the generating episode */
  generatingEpisodeTitle: string
  /** Cliffhanger type for the generating episode */
  cliffhangerType?: CliffhangerType
  /** Aggregate quality average score */
  averageScore?: number
  /** Callback to stop auto-generation */
  onStopAfterCurrent: () => void
  /** Whether stop has been requested */
  stopRequested: boolean
  /** Additional CSS classes */
  className?: string
}

/**
 * Sticky header for series auto-generation progress.
 */
export function SeriesProgressHeader({
  seriesTitle,
  episodes,
  generatingEpisodeNumber,
  generatingEpisodeTitle,
  cliffhangerType,
  averageScore,
  onStopAfterCurrent,
  stopRequested,
  className = '',
}: SeriesProgressHeaderProps) {
  const cliffhangerColors: Record<CliffhangerType, string> = {
    revelation: 'bg-purple-500/20 text-purple-400 border-purple-500/50',
    twist: 'bg-red-500/20 text-red-400 border-red-500/50',
    question: 'bg-cyan-500/20 text-cyan-400 border-cyan-500/50',
    countdown: 'bg-orange-500/20 text-orange-400 border-orange-500/50',
    promise: 'bg-green-500/20 text-green-400 border-green-500/50',
  }

  const truncatedTitle = seriesTitle.length > 30
    ? seriesTitle.slice(0, 30) + '...'
    : seriesTitle

  return (
    <div
      className={`sticky top-0 z-40 bg-card/95 backdrop-blur-sm border-b border-border px-4 py-3 ${className}`}
    >
      <div className="container mx-auto max-w-4xl">
        {/* Top row: Series title + episode chips + average score */}
        <div className="flex items-center justify-between gap-4 mb-2">
          <div className="flex items-center gap-3 min-w-0">
            <span className="text-lg" title="Series">&#128250;</span>
            <span className="font-medium text-foreground truncate" title={seriesTitle}>
              {truncatedTitle}
            </span>
          </div>

          {/* Episode status chips */}
          <div className="flex items-center gap-1.5 flex-shrink-0">
            {episodes.map((ep) => {
              const isCompleted = ep.status === 'completed'
              const isGenerating = ep.episode_number === generatingEpisodeNumber
              const isPending = ep.status === 'pending' && !isGenerating

              return (
                <span
                  key={ep.episode_number}
                  className={`
                    inline-flex items-center justify-center w-7 h-7 rounded text-xs font-medium
                    ${isCompleted ? 'bg-green-500/20 text-green-400' : ''}
                    ${isGenerating ? 'bg-primary/20 text-primary animate-pulse' : ''}
                    ${isPending ? 'bg-secondary text-muted-foreground' : ''}
                  `}
                  title={`Episode ${ep.episode_number}: ${ep.title} (${ep.status})`}
                >
                  {isCompleted && '✓'}
                  {isGenerating && '⚡'}
                  {isPending && ep.episode_number}
                </span>
              )
            })}
          </div>

          {/* Average score */}
          {averageScore !== undefined && averageScore > 0 && (
            <div className="flex items-center gap-1.5 flex-shrink-0">
              <span className="text-xs text-muted-foreground">Avg:</span>
              <span className={`text-sm font-medium ${
                averageScore >= 85 ? 'text-emerald-400' :
                averageScore >= 70 ? 'text-green-400' :
                averageScore >= 55 ? 'text-yellow-400' :
                'text-orange-400'
              }`}>
                {Math.round(averageScore)}/100
              </span>
            </div>
          )}
        </div>

        {/* Bottom row: Currently generating + cliffhanger + stop button */}
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-3 min-w-0">
            <span className="text-xs text-muted-foreground flex-shrink-0">Now:</span>
            <span className="text-sm text-foreground truncate">
              &ldquo;{generatingEpisodeTitle}&rdquo;
            </span>
            {cliffhangerType && (
              <span
                className={`text-xs px-2 py-0.5 rounded border flex-shrink-0 ${cliffhangerColors[cliffhangerType]}`}
              >
                {cliffhangerType.toUpperCase()}
              </span>
            )}
          </div>

          {/* Stop button */}
          <button
            onClick={onStopAfterCurrent}
            disabled={stopRequested}
            className={`
              text-xs px-3 py-1.5 rounded border transition-colors flex-shrink-0
              ${stopRequested
                ? 'bg-yellow-500/10 text-yellow-400 border-yellow-500/30 cursor-not-allowed'
                : 'bg-secondary hover:bg-secondary/80 text-muted-foreground hover:text-foreground border-border'
              }
            `}
          >
            {stopRequested ? 'Stopping after this...' : 'Stop after this episode'}
          </button>
        </div>
      </div>
    </div>
  )
}
