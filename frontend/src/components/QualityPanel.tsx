'use client'

import { useState, useRef } from 'react'
import { QualityReport, QualityScore, QualityTrace } from '@/types'

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
 * Tooltip component for showing reasoning on hover.
 * Uses a delay on mouse leave to allow cursor to reach the tooltip.
 */
function TraceTooltip({
  trace,
  children,
  onClick
}: {
  trace: QualityTrace | null
  children: React.ReactNode
  onClick?: () => void
}) {
  const [showTooltip, setShowTooltip] = useState(false)
  const timeoutRef = useRef<NodeJS.Timeout | null>(null)

  if (!trace) {
    return <>{children}</>
  }

  const handleMouseEnter = () => {
    if (timeoutRef.current) clearTimeout(timeoutRef.current)
    setShowTooltip(true)
  }

  const handleMouseLeave = () => {
    // Delay hide to allow mouse to reach tooltip
    timeoutRef.current = setTimeout(() => setShowTooltip(false), 150)
  }

  return (
    <div
      className="relative"
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
    >
      {children}
      {showTooltip && trace.reasoning && (
        <div
          className="absolute left-full ml-2 top-0 z-50 w-64 p-3 bg-popover border border-border rounded-lg shadow-lg cursor-pointer"
          onMouseEnter={handleMouseEnter}
          onMouseLeave={handleMouseLeave}
          onClick={onClick}
        >
          <p className="text-xs text-foreground leading-relaxed">{trace.reasoning}</p>
          <p className="text-[10px] text-primary mt-2 cursor-pointer hover:underline">Click for details</p>
        </div>
      )}
    </div>
  )
}

/**
 * Expanded detail modal for a dimension.
 */
function TraceDetailModal({
  trace,
  dimension,
  onClose,
}: {
  trace: QualityTrace
  dimension: { key: string; label: string; icon: string }
  onClose: () => void
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm">
      <div className="w-full max-w-md bg-card border border-border rounded-lg shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-border">
          <div className="flex items-center gap-2">
            <span className="text-lg">{dimension.icon}</span>
            <span className="font-semibold">{dimension.label} Quality</span>
          </div>
          <div className="flex items-center gap-3">
            <span className={`text-2xl font-bold tabular-nums ${getScoreColor(trace.score)}`}>
              {trace.score}
            </span>
            <span className={`px-2 py-1 rounded text-sm font-medium ${getGradeColor(trace.grade)}`}>
              {trace.grade}
            </span>
            <button
              onClick={onClose}
              className="p-1 hover:bg-secondary rounded-full transition-colors"
              aria-label="Close"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-4 space-y-4 max-h-96 overflow-y-auto">
          {/* Reasoning */}
          <div>
            <p className="text-sm text-foreground leading-relaxed">{trace.reasoning}</p>
            {trace.enhanced && (
              <span className="inline-flex items-center gap-1 mt-1 text-[10px] text-primary">
                <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                </svg>
                Enhanced
              </span>
            )}
          </div>

          {/* Strengths */}
          {trace.strengths.length > 0 && (
            <div className="space-y-2">
              <h4 className="text-xs font-medium text-emerald-400 flex items-center gap-1.5">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                Strengths
              </h4>
              <ul className="space-y-1.5">
                {trace.strengths.map((strength, idx) => (
                  <li key={idx} className="text-xs text-muted-foreground flex items-start gap-2">
                    <span className="text-emerald-400 mt-0.5 shrink-0">*</span>
                    <span>{strength}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Weaknesses */}
          {trace.weaknesses.length > 0 && (
            <div className="space-y-2">
              <h4 className="text-xs font-medium text-amber-400 flex items-center gap-1.5">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                  />
                </svg>
                Areas for Improvement
              </h4>
              <ul className="space-y-1.5">
                {trace.weaknesses.map((weakness, idx) => (
                  <li key={idx} className="text-xs text-muted-foreground flex items-start gap-2">
                    <span className="text-amber-400 mt-0.5 shrink-0">!</span>
                    <span>{weakness}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Suggestions (Pro mode) */}
          {trace.suggestions.length > 0 && (
            <div className="space-y-2">
              <h4 className="text-xs font-medium text-primary flex items-center gap-1.5">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
                  />
                </svg>
                Suggestions
              </h4>
              <ul className="space-y-1.5">
                {trace.suggestions.map((suggestion, idx) => (
                  <li key={idx} className="text-xs text-muted-foreground flex items-start gap-2">
                    <span className="text-primary mt-0.5 shrink-0">-</span>
                    <span>{suggestion}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

/**
 * Individual dimension score row with trace support.
 */
function DimensionRow({
  dimension,
  scoreData,
  trace,
  onClick,
}: {
  dimension: { key: string; label: string; icon: string }
  scoreData: QualityScore | null
  trace: QualityTrace | null
  onClick: () => void
}) {
  const score = scoreData?.score ?? trace?.score ?? null
  const grade = scoreData?.grade ?? trace?.grade ?? null
  const status = scoreData?.status ?? 'pending'
  const isPending = status === 'pending'
  const isEvaluating = status === 'evaluating'
  const hasWarning = score !== null && score < 70
  const hasTrace = trace !== null && trace.reasoning

  return (
    <TraceTooltip trace={trace} onClick={hasTrace ? onClick : undefined}>
      <div
        className={`flex items-center gap-2 py-1.5 rounded px-1 -mx-1 transition-colors ${
          hasTrace ? 'cursor-pointer hover:bg-secondary/50' : ''
        }`}
        onClick={hasTrace ? onClick : undefined}
      >
        {/* Icon */}
        <span className="text-sm w-6 text-center">{dimension.icon}</span>

        {/* Label */}
        <span className="text-xs w-20 text-muted-foreground truncate">{dimension.label}</span>

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

        {/* Status indicator */}
        <span className="w-4 text-center">
          {hasWarning && <span className="text-amber-400 text-xs">!</span>}
          {status === 'complete' && !hasWarning && score !== null && (
            <span className="text-success text-xs">OK</span>
          )}
          {hasTrace && (
            <svg className="w-3 h-3 text-muted-foreground inline" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          )}
        </span>
      </div>
    </TraceTooltip>
  )
}

/**
 * Evaluation sequence indicator.
 */
function EvaluationSequence({ traces }: { traces: QualityTrace[] }) {
  if (traces.length === 0) return null

  const sortedTraces = [...traces].sort((a, b) => a.sequence - b.sequence)
  const lastSequence = Math.max(...traces.map((t) => t.sequence))

  return (
    <div className="flex items-center gap-1 text-[10px] text-muted-foreground overflow-x-auto pb-1">
      {QUALITY_DIMENSIONS.map((dim, idx) => {
        const trace = sortedTraces.find((t) => t.dimension === dim.key)
        const isComplete = trace !== undefined
        const isCurrent = trace?.sequence === lastSequence
        return (
          <div key={dim.key} className="flex items-center gap-1 shrink-0">
            <span
              className={`px-1.5 py-0.5 rounded ${
                isCurrent
                  ? 'bg-primary/20 text-primary'
                  : isComplete
                  ? 'bg-emerald-500/20 text-emerald-400'
                  : 'bg-secondary text-muted-foreground'
              }`}
            >
              [{trace?.sequence ?? idx + 1}] {dim.label.slice(0, 3)}
              {isComplete && ' OK'}
            </span>
            {idx < QUALITY_DIMENSIONS.length - 1 && <span className="text-muted-foreground/50">-</span>}
          </div>
        )
      })}
    </div>
  )
}

/**
 * Side panel component displaying real-time quality metrics with explainable traces.
 *
 * Shows quality scores for each dimension with animated progress bars,
 * letter grades, and hover tooltips with reasoning. Click to see detailed
 * strengths, weaknesses, and suggestions.
 */
export function QualityPanel({ quality, isComplete, onRegenerate }: QualityPanelProps) {
  const [expandedDimension, setExpandedDimension] = useState<string | null>(null)

  // Find score data for each dimension
  const getScoreForDimension = (key: string): QualityScore | null => {
    if (!quality?.scores) return null
    return quality.scores.find((s) => s.dimension === key) ?? null
  }

  // Find trace for each dimension
  const getTraceForDimension = (key: string): QualityTrace | null => {
    if (!quality?.traces) return null
    return quality.traces.find((t) => t.dimension === key) ?? null
  }

  // Find low-scoring dimensions (< 70)
  const lowScoreDimensions =
    quality?.scores?.filter((s) => s.score !== null && s.score < 70 && s.status === 'complete') ?? []

  const hasLowScores = isComplete && lowScoreDimensions.length > 0

  // Get expanded trace and dimension
  const expandedTrace = expandedDimension ? getTraceForDimension(expandedDimension) : null
  const expandedDimensionData = QUALITY_DIMENSIONS.find((d) => d.key === expandedDimension)

  return (
    <>
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
            <span
              className={`text-lg font-bold tabular-nums ${getScoreColor(quality?.overall_score ?? null)}`}
            >
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

        {/* Evaluation sequence (if traces available) */}
        {quality?.traces && quality.traces.length > 0 && (
          <EvaluationSequence traces={quality.traces} />
        )}

        {/* Divider */}
        <div className="border-t border-border" />

        {/* Dimension scores */}
        <div className="space-y-0.5">
          {QUALITY_DIMENSIONS.map((dim) => (
            <DimensionRow
              key={dim.key}
              dimension={dim}
              scoreData={getScoreForDimension(dim.key)}
              trace={getTraceForDimension(dim.key)}
              onClick={() => setExpandedDimension(dim.key)}
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
              <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/20">
                <div className="flex items-center gap-2 mb-2">
                  <svg className="w-4 h-4 text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                      d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                  <h4 className="text-xs font-semibold text-amber-400">Issues Detected ({quality.issues.length})</h4>
                </div>
                <ul className="space-y-1.5 max-h-24 overflow-y-auto">
                  {quality.issues.slice(0, 4).map((issue, idx) => (
                    <li key={idx} className="text-xs text-amber-200/80 pl-4 relative before:content-['•'] before:absolute before:left-1 before:text-amber-400">
                      {issue.message}
                    </li>
                  ))}
                </ul>
                {quality.issues.length > 4 && (
                  <p className="text-xs text-amber-400/70 mt-2 pl-4">+{quality.issues.length - 4} more issues</p>
                )}
              </div>
            )}

            {/* Recommendations */}
            {quality.recommendations.length > 0 && (
              <div className="mt-3 p-3 rounded-lg bg-primary/10 border border-primary/20">
                <div className="flex items-center gap-2 mb-2">
                  <svg className="w-4 h-4 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                      d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                  </svg>
                  <h4 className="text-xs font-semibold text-primary">Recommendations</h4>
                </div>
                <ul className="space-y-1.5 max-h-20 overflow-y-auto">
                  {quality.recommendations.slice(0, 3).map((rec, idx) => (
                    <li key={idx} className="text-xs text-foreground/70 pl-4 relative before:content-['→'] before:absolute before:left-0 before:text-primary">
                      {rec}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Regenerate button for low scores */}
            {hasLowScores && onRegenerate && (
              <div className="pt-2">
                <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/20 space-y-2">
                  <p className="text-xs text-amber-400 font-medium">Low Score Detected:</p>
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
                ! {issue.message}
              </p>
            ))}
            {quality.recommendations.slice(0, 1).map((rec, idx) => (
              <p key={idx} className="text-xs text-emerald-400">
                - {rec}
              </p>
            ))}
          </div>
        )}

        {/* Hint about clicking for details */}
        {quality?.traces && quality.traces.length > 0 && (
          <p className="text-[10px] text-muted-foreground text-center">
            Click a dimension for detailed breakdown
          </p>
        )}
      </div>

      {/* Detail modal */}
      {expandedTrace && expandedDimensionData && (
        <TraceDetailModal
          trace={expandedTrace}
          dimension={expandedDimensionData}
          onClose={() => setExpandedDimension(null)}
        />
      )}
    </>
  )
}
