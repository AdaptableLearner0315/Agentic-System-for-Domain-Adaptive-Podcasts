'use client'

import { QualityReport, QualityScore } from '@/types'

interface QualityPanelProps {
  /** Quality report data */
  quality: QualityReport | null
  /** Whether generation is complete */
  isComplete: boolean
  /** Callback when user wants to regenerate with a fix */
  onRegenerate?: (dimension: string, issue: string) => void
}

/**
 * Quality dimension display order and labels.
 */
const QUALITY_DIMENSIONS = [
  { key: 'script', label: 'Script', icon: '📝' },
  { key: 'pacing', label: 'Pacing', icon: '⏱️' },
  { key: 'voice', label: 'Voice', icon: '🎙️' },
  { key: 'bgm', label: 'BGM', icon: '🎵' },
  { key: 'audio_mix', label: 'Audio Mix', icon: '🎛️' },
  { key: 'video', label: 'Video', icon: '🎬' },
  { key: 'ending', label: 'Ending', icon: '🎭' },
  { key: 'duration', label: 'Duration', icon: '⏳' },
]

/**
 * Get color class based on score.
 */
function getScoreColor(score: number | null): string {
  if (score === null) return 'text-muted-foreground'
  if (score >= 90) return 'text-emerald-400'
  if (score >= 80) return 'text-green-400'
  if (score >= 70) return 'text-yellow-400'
  if (score >= 60) return 'text-orange-400'
  return 'text-red-400'
}

/**
 * Get background color for progress bar based on score.
 */
function getBarColor(score: number | null): string {
  if (score === null) return 'bg-secondary'
  if (score >= 90) return 'bg-emerald-500'
  if (score >= 80) return 'bg-green-500'
  if (score >= 70) return 'bg-yellow-500'
  if (score >= 60) return 'bg-orange-500'
  return 'bg-red-500'
}

/**
 * Get grade badge color.
 */
function getGradeColor(grade: string | null): string {
  if (!grade) return 'bg-secondary text-muted-foreground'
  if (grade.startsWith('A')) return 'bg-emerald-500/20 text-emerald-400'
  if (grade.startsWith('B')) return 'bg-green-500/20 text-green-400'
  if (grade.startsWith('C')) return 'bg-yellow-500/20 text-yellow-400'
  if (grade.startsWith('D')) return 'bg-orange-500/20 text-orange-400'
  return 'bg-red-500/20 text-red-400'
}

/**
 * Individual dimension score row.
 */
function DimensionRow({
  dimension,
  scoreData,
}: {
  dimension: { key: string; label: string; icon: string }
  scoreData: QualityScore | null
}) {
  const score = scoreData?.score ?? null
  const grade = scoreData?.grade ?? null
  const status = scoreData?.status ?? 'pending'
  const isPending = status === 'pending'
  const isEvaluating = status === 'evaluating'
  const hasWarning = score !== null && score < 70

  return (
    <div className="flex items-center gap-2 py-1.5">
      {/* Icon */}
      <span className="text-sm w-6 text-center">{dimension.icon}</span>

      {/* Label */}
      <span className="text-xs w-20 text-muted-foreground truncate">
        {dimension.label}
      </span>

      {/* Progress bar */}
      <div className="flex-1 h-2 bg-secondary rounded-full overflow-hidden">
        {isEvaluating ? (
          <div className="h-full w-full bg-primary/30 animate-pulse" />
        ) : (
          <div
            className={`h-full transition-all duration-500 ${getBarColor(score)}`}
            style={{ width: score !== null ? `${score}%` : '0%' }}
          />
        )}
      </div>

      {/* Score */}
      <span className={`text-xs w-8 text-right tabular-nums font-medium ${getScoreColor(score)}`}>
        {isPending || isEvaluating ? '--' : score}
      </span>

      {/* Grade badge */}
      <span
        className={`text-[10px] w-7 text-center rounded px-1 py-0.5 font-medium ${getGradeColor(grade)}`}
      >
        {isPending || isEvaluating ? (
          <span className={isEvaluating ? 'animate-pulse' : ''}>--</span>
        ) : (
          grade
        )}
      </span>

      {/* Warning icon for low scores */}
      <span className="w-4 text-center">
        {hasWarning && <span className="text-amber-400 text-xs">!</span>}
        {status === 'complete' && !hasWarning && score !== null && (
          <span className="text-success text-xs">OK</span>
        )}
      </span>
    </div>
  )
}

/**
 * Side panel component displaying real-time quality metrics.
 *
 * Shows quality scores for each dimension with animated progress bars,
 * letter grades, and actionable regeneration suggestions for low scores.
 */
export function QualityPanel({ quality, isComplete, onRegenerate }: QualityPanelProps) {
  // Find score data for each dimension
  const getScoreForDimension = (key: string): QualityScore | null => {
    if (!quality?.scores) return null
    return quality.scores.find((s) => s.dimension === key) ?? null
  }

  // Find low-scoring dimensions (< 70)
  const lowScoreDimensions = quality?.scores?.filter(
    (s) => s.score !== null && s.score < 70 && s.status === 'complete'
  ) ?? []

  const hasLowScores = isComplete && lowScoreDimensions.length > 0

  return (
    <div className="w-72 bg-card border border-border rounded-lg p-4 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="font-semibold text-sm flex items-center gap-2">
          <span>Quality Score</span>
        </h3>
        {quality?.overall_score !== null && quality?.overall_score !== undefined && (
          <span
            className={`text-xs px-2 py-0.5 rounded font-medium ${getGradeColor(quality.overall_grade)}`}
          >
            {quality.overall_grade}
          </span>
        )}
      </div>

      {/* Overall score bar */}
      <div className="space-y-1">
        <div className="flex justify-between items-baseline">
          <span className="text-xs text-muted-foreground">Overall</span>
          <span className={`text-lg font-bold tabular-nums ${getScoreColor(quality?.overall_score ?? null)}`}>
            {quality?.overall_score !== null && quality?.overall_score !== undefined
              ? `${quality.overall_score}/100`
              : '--/100'}
          </span>
        </div>
        <div className="h-3 bg-secondary rounded-full overflow-hidden">
          <div
            className={`h-full transition-all duration-700 ${getBarColor(quality?.overall_score ?? null)}`}
            style={{ width: quality?.overall_score ? `${quality.overall_score}%` : '0%' }}
          />
        </div>
      </div>

      {/* Divider */}
      <div className="border-t border-border" />

      {/* Dimension scores */}
      <div className="space-y-0.5">
        {QUALITY_DIMENSIONS.map((dim) => (
          <DimensionRow
            key={dim.key}
            dimension={dim}
            scoreData={getScoreForDimension(dim.key)}
          />
        ))}
      </div>

      {/* Issues and recommendations (when complete) */}
      {isComplete && quality && (
        <>
          {/* Divider */}
          <div className="border-t border-border" />

          {/* Issues summary */}
          {quality.issues.length > 0 && (
            <div className="space-y-2">
              <h4 className="text-xs font-medium text-muted-foreground">Issues Detected</h4>
              <div className="space-y-1 max-h-24 overflow-y-auto">
                {quality.issues.slice(0, 3).map((issue, idx) => (
                  <div key={idx} className="text-xs text-amber-400 flex items-start gap-1.5">
                    <span className="mt-0.5">!</span>
                    <span className="line-clamp-2">{issue}</span>
                  </div>
                ))}
                {quality.issues.length > 3 && (
                  <p className="text-xs text-muted-foreground">
                    +{quality.issues.length - 3} more issues
                  </p>
                )}
              </div>
            </div>
          )}

          {/* Recommendations */}
          {quality.recommendations.length > 0 && (
            <div className="space-y-2">
              <h4 className="text-xs font-medium text-muted-foreground">Recommendations</h4>
              <div className="space-y-1 max-h-20 overflow-y-auto">
                {quality.recommendations.slice(0, 2).map((rec, idx) => (
                  <div key={idx} className="text-xs text-muted-foreground flex items-start gap-1.5">
                    <span className="text-primary mt-0.5">-</span>
                    <span className="line-clamp-2">{rec}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Regenerate button for low scores */}
          {hasLowScores && onRegenerate && (
            <div className="pt-2">
              <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/20 space-y-2">
                <p className="text-xs text-amber-400 font-medium">
                  Low Score Detected:
                </p>
                <p className="text-xs text-muted-foreground">
                  {lowScoreDimensions[0].dimension} ({lowScoreDimensions[0].score}) -{' '}
                  {lowScoreDimensions[0].issues[0] || 'Quality below threshold'}
                </p>
                <button
                  className="w-full btn-secondary text-xs py-2 flex items-center justify-center gap-2"
                  onClick={() =>
                    onRegenerate(
                      lowScoreDimensions[0].dimension,
                      lowScoreDimensions[0].issues[0] || 'fix'
                    )
                  }
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                    />
                  </svg>
                  Regenerate with fix
                </button>
              </div>
            </div>
          )}

          {/* Success message when no low scores */}
          {!hasLowScores && quality.overall_score !== null && quality.overall_score >= 80 && (
            <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
              <p className="text-xs text-emerald-400 flex items-center gap-2">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
                Great quality! All dimensions passed.
              </p>
            </div>
          )}
        </>
      )}

      {/* Insights during generation */}
      {!isComplete && quality && (
        <div className="space-y-1.5">
          {quality.issues.slice(0, 2).map((issue, idx) => (
            <p key={idx} className="text-xs text-amber-400">
              ! {issue}
            </p>
          ))}
          {quality.recommendations.slice(0, 1).map((rec, idx) => (
            <p key={idx} className="text-xs text-emerald-400">
              - {rec}
            </p>
          ))}
        </div>
      )}
    </div>
  )
}
