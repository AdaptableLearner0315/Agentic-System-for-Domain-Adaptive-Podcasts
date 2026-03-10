'use client'

import { useState, useRef, useCallback } from 'react'
import { ResultResponse, QualityReport } from '@/types'
import { API_URL } from '@/lib/api'
import { formatDuration } from '@/lib/utils'
import { ChatPanel } from './interactive'
import { ChatDrawer } from './ChatDrawer'
import { QualityPanel } from './QualityPanel'

interface OutputPlayerProps {
  /** Generation result data */
  result: ResultResponse
  /** Callback to reset and start over */
  onReset: () => void
  /** Whether to show the interactive chat panel */
  showChat?: boolean
  /** Quality metrics from generation (fallback to result.quality_report if not provided) */
  quality?: QualityReport | null
}

/**
 * Output video player and download component.
 *
 * Displays the generated video with playback controls
 * and download options.
 *
 * @param result - Generation result with video URLs
 * @param onReset - Callback to reset the form
 */
export function OutputPlayer({ result, onReset, showChat = true, quality }: OutputPlayerProps) {
  const [activeTab, setActiveTab] = useState<'video' | 'details'>('video')
  const [isMuted, setIsMuted] = useState(true)
  const [isChatOpen, setIsChatOpen] = useState(false)
  const [showEvaluation, setShowEvaluation] = useState(false)
  const [showAudioPreview, setShowAudioPreview] = useState(false)
  const [showScriptPreview, setShowScriptPreview] = useState(false)
  const videoRef = useRef<HTMLVideoElement>(null)

  // Use quality prop if provided, otherwise fallback to result.quality_report
  const qualityData = quality ?? result.quality_report ?? null

  /**
   * Pause video when user interacts with chat.
   */
  const handleChatInteraction = useCallback(() => {
    if (videoRef.current && !videoRef.current.paused) {
      videoRef.current.pause()
    }
  }, [])

  /**
   * Toggle chat panel visibility.
   */
  const toggleChat = useCallback(() => {
    setIsChatOpen((prev) => !prev)
  }, [])

  /**
   * Handle video download.
   */
  const handleDownload = async (type: 'video' | 'audio' | 'script') => {
    let url = ''

    switch (type) {
      case 'video':
        url = `${API_URL}/api/outputs/download/${result.job_id}?file_type=video`
        break
      case 'audio':
        url = `${API_URL}/api/outputs/download/${result.job_id}?file_type=audio`
        break
      case 'script':
        url = `${API_URL}/api/outputs/download/${result.job_id}?file_type=script`
        break
    }

    window.open(url, '_blank')
  }

  const videoUrl = result.video_url
    ? `${API_URL}${result.video_url}`
    : null

  const audioUrl = result.audio_url
    ? `${API_URL}${result.audio_url}`
    : `${API_URL}/api/outputs/stream/${result.job_id}?file_type=audio`

  return (
    <div className="w-full">
      {/* Main layout: Video card on left, Quality panel on right */}
      <div className="flex flex-col lg:flex-row gap-6">
        {/* Left: Main content card */}
        <div className="flex-1 card space-y-6">
          {/* Success Header */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-full bg-success/20 flex items-center justify-center">
                <svg
                  className="w-6 h-6 text-success"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M5 13l4 4L19 7"
                  />
                </svg>
              </div>
              <div>
                <h3 className="text-xl font-bold">Your Podcast is Ready!</h3>
                <p className="text-muted-foreground">
                  {result.duration_seconds
                    ? `Duration: ${formatDuration(result.duration_seconds)}`
                    : 'Generation complete'}
                </p>
              </div>
            </div>

            {/* Action buttons */}
            <div className="flex items-center gap-2">
              {/* Evaluation Score button */}
              {qualityData ? (
                <button
                  className="flex items-center gap-2 px-3 py-2 rounded-lg bg-amber-500/10 hover:bg-amber-500/20 text-amber-400 transition-colors"
                  onClick={() => setShowEvaluation(true)}
                  aria-label="View evaluation score"
                >
                  <svg
                    className="w-5 h-5"
                    fill="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
                  </svg>
                  <span className="text-sm font-medium">Score</span>
                  {qualityData.overall_grade && (
                    <span className={`px-1.5 py-0.5 rounded text-xs font-medium ${
                      qualityData.overall_grade.startsWith('A') ? 'bg-emerald-500/20 text-emerald-400' :
                      qualityData.overall_grade.startsWith('B') ? 'bg-green-500/20 text-green-400' :
                      qualityData.overall_grade.startsWith('C') ? 'bg-yellow-500/20 text-yellow-400' :
                      'bg-orange-500/20 text-orange-400'
                    }`}>
                      {qualityData.overall_grade}
                    </span>
                  )}
                </button>
              ) : (
                <button
                  disabled
                  className="flex items-center gap-2 px-3 py-2 rounded-lg bg-secondary/50 text-muted-foreground opacity-50 cursor-not-allowed"
                  aria-label="Evaluation score unavailable"
                >
                  <svg
                    className="w-5 h-5"
                    fill="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
                  </svg>
                  <span className="text-sm font-medium">Score</span>
                </button>
              )}

              {/* Chat toggle button */}
              {showChat && (
                <button
                  className="flex items-center gap-2 px-3 py-2 rounded-lg bg-primary/10 hover:bg-primary/20 text-primary transition-colors"
                  onClick={toggleChat}
                  aria-label="Open chat"
                >
                  <svg
                    className="w-5 h-5"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
                    />
                  </svg>
                  <span className="text-sm font-medium">Chat</span>
                </button>
              )}
            </div>
          </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-border pb-2">
        <button
          className={activeTab === 'video' ? 'tab-active' : 'tab-inactive'}
          onClick={() => setActiveTab('video')}
        >
          Video
        </button>
        <button
          className={activeTab === 'details' ? 'tab-active' : 'tab-inactive'}
          onClick={() => setActiveTab('details')}
        >
          Details
        </button>
      </div>

      {/* Video Tab */}
      {activeTab === 'video' && (
        <div className="space-y-4">
          {videoUrl ? (
            <div className="relative aspect-video rounded-lg overflow-hidden bg-black">
              <video
                ref={videoRef}
                className="w-full h-full"
                controls
                autoPlay
                muted={isMuted}
                src={videoUrl}
              >
                Your browser does not support video playback.
              </video>
              {isMuted && (
                <button
                  className="absolute bottom-4 right-4 bg-black/70 text-white px-3 py-1.5 rounded-lg text-sm hover:bg-black/90 transition-colors"
                  onClick={() => {
                    setIsMuted(false)
                    if (videoRef.current) {
                      videoRef.current.muted = false
                    }
                  }}
                >
                  Unmute
                </button>
              )}
            </div>
          ) : (
            <div className="aspect-video rounded-lg bg-secondary flex items-center justify-center">
              <p className="text-muted-foreground">Video preview not available</p>
            </div>
          )}

          {/* Download Buttons */}
          <div className="flex flex-wrap gap-3">
            <button
              className="btn-primary flex-1 sm:flex-none"
              onClick={() => handleDownload('video')}
            >
              <svg
                className="w-4 h-4 mr-2"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
                />
              </svg>
              Download Video
            </button>
            <button
              className="btn-outline"
              onClick={() => setShowAudioPreview(true)}
            >
              <svg
                className="w-4 h-4 mr-2"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3"
                />
              </svg>
              Audio Only
            </button>
            <button
              className="btn-outline"
              onClick={() => setShowScriptPreview(true)}
            >
              <svg
                className="w-4 h-4 mr-2"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
              Script
            </button>
          </div>
        </div>
      )}

      {/* Details Tab */}
      {activeTab === 'details' && (
        <div className="space-y-4">
          {/* Script Preview */}
          {result.script && (
            <div>
              <h4 className="font-medium mb-2">Script Preview</h4>
              <div className="p-4 rounded-lg bg-secondary/50 max-h-60 overflow-y-auto">
                <p className="text-lg font-semibold mb-2">
                  {result.script.title || 'Untitled'}
                </p>
                {result.script.hook && (
                  <p className="text-sm text-muted-foreground">
                    {typeof result.script.hook === 'string'
                      ? result.script.hook
                      : result.script.hook.text}
                  </p>
                )}
              </div>
            </div>
          )}

          {/* Asset Counts */}
          <div className="grid grid-cols-3 gap-4">
            <div className="p-4 rounded-lg bg-secondary text-center">
              <p className="text-2xl font-bold">
                {result.tts_assets?.length || 0}
              </p>
              <p className="text-xs text-muted-foreground">Voice Clips</p>
            </div>
            <div className="p-4 rounded-lg bg-secondary text-center">
              <p className="text-2xl font-bold">
                {result.bgm_assets?.length || 0}
              </p>
              <p className="text-xs text-muted-foreground">Music Tracks</p>
            </div>
            <div className="p-4 rounded-lg bg-secondary text-center">
              <p className="text-2xl font-bold">
                {result.image_assets?.length || 0}
              </p>
              <p className="text-xs text-muted-foreground">Images</p>
            </div>
          </div>

          {/* Review History (Pro mode) */}
          {result.review_history && result.review_history.length > 0 && (
            <div>
              <h4 className="font-medium mb-2">Director Reviews</h4>
              <div className="space-y-2">
                {result.review_history.map((review, i) => (
                  <div key={i} className="p-3 rounded-lg bg-secondary/50 text-sm">
                    Round {i + 1}: Score {review.score || 'N/A'}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

        {/* Create Another */}
        <div className="pt-4 border-t border-border">
          <button className="btn-secondary w-full" onClick={onReset}>
            <svg
              className="w-4 h-4 mr-2"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 4v16m8-8H4"
              />
            </svg>
            Create Another Podcast
          </button>
        </div>
        </div>

        {/* Right: Quality Panel (desktop) */}
        {qualityData && (
          <div className="hidden lg:block">
            <QualityPanel quality={qualityData} isComplete={true} />
          </div>
        )}
      </div>

      {/* Mobile Quality Panel (shown below main content) */}
      {qualityData && (
        <div className="lg:hidden mt-6">
          <details className="group">
            <summary className="cursor-pointer text-sm text-muted-foreground hover:text-foreground flex items-center gap-2 mb-4">
              <span>Quality Report</span>
              <svg
                className="w-4 h-4 transition-transform group-open:rotate-180"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </summary>
            <div className="flex justify-center">
              <QualityPanel quality={qualityData} isComplete={true} />
            </div>
          </details>
        </div>
      )}

      {/* Chat Drawer - always mounted to preserve session */}
      {showChat && (
        <ChatDrawer isOpen={isChatOpen} onClose={() => setIsChatOpen(false)}>
          <ChatPanel
            jobId={result.job_id}
            isVisible={true}
            onClose={() => setIsChatOpen(false)}
            onInteraction={handleChatInteraction}
            enableVoice={true}
          />
        </ChatDrawer>
      )}

      {/* Evaluation Score Modal */}
      {showEvaluation && qualityData && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm"
          onClick={() => setShowEvaluation(false)}
        >
          <div
            className="relative max-h-[90vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Close button */}
            <button
              onClick={() => setShowEvaluation(false)}
              className="absolute -top-2 -right-2 z-10 p-2 bg-card border border-border rounded-full shadow-lg hover:bg-secondary transition-colors"
              aria-label="Close evaluation"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>

            {/* Quality Panel */}
            <QualityPanel quality={qualityData} isComplete={true} />
          </div>
        </div>
      )}

      {/* Audio Preview Modal */}
      {showAudioPreview && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm"
          onClick={() => setShowAudioPreview(false)}
        >
          <div
            className="bg-card border border-border rounded-lg p-6 max-w-md w-full mx-4"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold">Audio Preview</h3>
              <button
                onClick={() => setShowAudioPreview(false)}
                className="p-1 hover:bg-secondary rounded-lg transition-colors"
                aria-label="Close audio preview"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <audio
              controls
              autoPlay
              className="w-full mb-4"
              src={audioUrl}
            >
              Your browser does not support audio playback.
            </audio>
            <button
              className="btn-outline w-full"
              onClick={() => handleDownload('audio')}
            >
              <svg
                className="w-4 h-4 mr-2"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
                />
              </svg>
              Download Audio
            </button>
          </div>
        </div>
      )}

      {/* Script Preview Modal */}
      {showScriptPreview && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm"
          onClick={() => setShowScriptPreview(false)}
        >
          <div
            className="bg-card border border-border rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[80vh] flex flex-col"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold">Script</h3>
              <button
                onClick={() => setShowScriptPreview(false)}
                className="p-1 hover:bg-secondary rounded-lg transition-colors"
                aria-label="Close script preview"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <div className="flex-1 overflow-y-auto mb-4 p-4 rounded-lg bg-secondary/50">
              {result.script ? (
                <div className="space-y-4">
                  <h4 className="text-xl font-bold">{result.script.title || 'Untitled'}</h4>
                  {result.script.hook && (
                    <div>
                      <p className="text-sm text-muted-foreground font-medium mb-1">Hook</p>
                      <p className="text-foreground">
                        {typeof result.script.hook === 'string'
                          ? result.script.hook
                          : result.script.hook.text}
                      </p>
                    </div>
                  )}
                  {result.script.modules && result.script.modules.length > 0 && (
                    <div className="space-y-3">
                      <p className="text-sm text-muted-foreground font-medium">Modules</p>
                      {result.script.modules.map((module, i) => (
                        <div key={i} className="p-3 rounded bg-background/50">
                          <p className="font-medium text-sm text-primary mb-1">
                            {module.title || `Module ${i + 1}`}
                          </p>
                          {module.chunks && module.chunks.length > 0 && (
                            <div className="text-sm text-foreground">
                              {module.chunks.map((chunk, j) => (
                                <p key={j} className="mb-1">{chunk.text}</p>
                              ))}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ) : (
                <p className="text-muted-foreground">No script available</p>
              )}
            </div>
            <button
              className="btn-outline w-full"
              onClick={() => handleDownload('script')}
            >
              <svg
                className="w-4 h-4 mr-2"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
                />
              </svg>
              Download Script
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
