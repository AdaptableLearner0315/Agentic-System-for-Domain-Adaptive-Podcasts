'use client'

import { useEffect, useState, useRef } from 'react'
import type { JobLogs, LogEntry } from '@/types'
import { getJobLogs } from '@/lib/api'

interface LogsModalProps {
  jobId: string
  onClose: () => void
}

/**
 * Format timestamp for display.
 */
function formatTimestamp(isoString: string): string {
  const date = new Date(isoString)
  return date.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
}

/**
 * Format full timestamp for copy text.
 */
function formatFullTimestamp(isoString: string): string {
  const date = new Date(isoString)
  return date.toISOString()
}

/**
 * Get color class for log level.
 */
function getLevelColor(level: string): string {
  switch (level) {
    case 'ERROR':
      return 'text-red-400'
    case 'WARNING':
      return 'text-yellow-400'
    default:
      return 'text-gray-400'
  }
}

/**
 * Get background color for log level.
 */
function getLevelBg(level: string): string {
  switch (level) {
    case 'ERROR':
      return 'bg-red-500/10'
    case 'WARNING':
      return 'bg-yellow-500/10'
    default:
      return ''
  }
}

/**
 * Modal component for displaying job execution logs.
 */
export function LogsModal({ jobId, onClose }: LogsModalProps) {
  const [logs, setLogs] = useState<JobLogs | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)
  const modalRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    async function fetchLogs() {
      try {
        setLoading(true)
        setError(null)
        const data = await getJobLogs(jobId)
        setLogs(data)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load logs')
      } finally {
        setLoading(false)
      }
    }

    fetchLogs()

    // Poll for updates if job is running
    const interval = setInterval(async () => {
      try {
        const data = await getJobLogs(jobId)
        setLogs(data)
        // Stop polling if job is done
        if (data.status === 'completed' || data.status === 'failed' || data.status === 'cancelled') {
          clearInterval(interval)
        }
      } catch {
        // Ignore polling errors
      }
    }, 2000)

    return () => clearInterval(interval)
  }, [jobId])

  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === 'Escape') {
        onClose()
      }
    }

    function handleClickOutside(e: MouseEvent) {
      if (modalRef.current && !modalRef.current.contains(e.target as Node)) {
        onClose()
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    document.addEventListener('mousedown', handleClickOutside)

    return () => {
      document.removeEventListener('keydown', handleKeyDown)
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [onClose])

  const handleCopyLogs = async () => {
    if (!logs) return

    const logText = [
      `Job ID: ${logs.job_id}`,
      `Status: ${logs.status}`,
      `Mode: ${logs.mode}`,
      `Created: ${logs.created_at}`,
      logs.started_at ? `Started: ${logs.started_at}` : null,
      logs.completed_at ? `Completed: ${logs.completed_at}` : null,
      logs.error ? `Error: ${logs.error}` : null,
      '',
      '--- Logs ---',
      ...logs.logs.map(
        (log) =>
          `[${formatFullTimestamp(log.timestamp)}] [${log.level}]${log.phase ? ` [${log.phase}]` : ''} ${log.message}`
      ),
    ]
      .filter(Boolean)
      .join('\n')

    try {
      await navigator.clipboard.writeText(logText)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      // Fallback for browsers without clipboard API
      const textarea = document.createElement('textarea')
      textarea.value = logText
      document.body.appendChild(textarea)
      textarea.select()
      document.execCommand('copy')
      document.body.removeChild(textarea)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  const getStatusColor = (status: string): string => {
    switch (status) {
      case 'completed':
        return 'text-green-400'
      case 'failed':
        return 'text-red-400'
      case 'running':
        return 'text-blue-400'
      case 'cancelled':
        return 'text-gray-400'
      default:
        return 'text-yellow-400'
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div
        ref={modalRef}
        className="bg-gray-900 border border-gray-700 rounded-xl shadow-2xl w-full max-w-3xl max-h-[80vh] flex flex-col mx-4"
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-700">
          <div>
            <h2 className="text-lg font-semibold text-gray-100">Job Logs</h2>
            <p className="text-sm text-gray-400 font-mono">{jobId}</p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={handleCopyLogs}
              disabled={!logs}
              className="flex items-center gap-2 px-3 py-1.5 text-sm bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg transition-colors disabled:opacity-50"
            >
              {copied ? (
                <>
                  <svg className="w-4 h-4 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  Copied
                </>
              ) : (
                <>
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"
                    />
                  </svg>
                  Copy All
                </>
              )}
            </button>
            <button
              onClick={onClose}
              className="p-1.5 text-gray-400 hover:text-gray-200 hover:bg-gray-800 rounded-lg transition-colors"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Job metadata */}
        {logs && (
          <div className="px-6 py-3 border-b border-gray-700/50 bg-gray-800/30">
            <div className="flex flex-wrap gap-x-6 gap-y-1 text-sm">
              <div>
                <span className="text-gray-500">Status:</span>{' '}
                <span className={`font-medium capitalize ${getStatusColor(logs.status)}`}>{logs.status}</span>
              </div>
              <div>
                <span className="text-gray-500">Mode:</span>{' '}
                <span className="text-gray-300 capitalize">{logs.mode}</span>
              </div>
              {logs.started_at && (
                <div>
                  <span className="text-gray-500">Duration:</span>{' '}
                  <span className="text-gray-300">
                    {logs.completed_at
                      ? `${((new Date(logs.completed_at).getTime() - new Date(logs.started_at).getTime()) / 1000).toFixed(1)}s`
                      : `${((Date.now() - new Date(logs.started_at).getTime()) / 1000).toFixed(0)}s (running)`}
                  </span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Logs content */}
        <div className="flex-1 overflow-y-auto p-4">
          {loading && (
            <div className="flex items-center justify-center py-12">
              <div className="flex items-center gap-3 text-gray-400">
                <svg className="w-5 h-5 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  />
                </svg>
                Loading logs...
              </div>
            </div>
          )}

          {error && (
            <div className="flex flex-col items-center justify-center py-12 text-red-400">
              <svg className="w-8 h-8 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                />
              </svg>
              <p>{error}</p>
            </div>
          )}

          {logs && !loading && (
            <div className="space-y-1 font-mono text-sm">
              {logs.logs.length === 0 ? (
                <p className="text-gray-500 text-center py-8">No logs available</p>
              ) : (
                logs.logs.map((log, index) => (
                  <div
                    key={index}
                    className={`flex gap-3 px-3 py-1.5 rounded ${getLevelBg(log.level)}`}
                  >
                    <span className="text-gray-500 flex-shrink-0">{formatTimestamp(log.timestamp)}</span>
                    <span className={`flex-shrink-0 w-16 ${getLevelColor(log.level)}`}>[{log.level}]</span>
                    {log.phase && (
                      <span className="text-purple-400 flex-shrink-0">[{log.phase}]</span>
                    )}
                    <span className="text-gray-200 break-all">{log.message}</span>
                  </div>
                ))
              )}
            </div>
          )}
        </div>

        {/* Footer with error display */}
        {logs?.error && (
          <div className="px-6 py-3 border-t border-gray-700 bg-red-500/10">
            <div className="flex items-start gap-2 text-red-400 text-sm">
              <svg className="w-5 h-5 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
              <div>
                <p className="font-medium">Error</p>
                <p className="text-red-300 mt-1">{logs.error}</p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
