'use client'

import { useState, useRef, useCallback } from 'react'
import { ResultResponse } from '@/types'
import { API_URL } from '@/lib/api'
import { formatDuration } from '@/lib/utils'
import { ChatPanel } from './interactive'

interface OutputPlayerProps {
  /** Generation result data */
  result: ResultResponse
  /** Callback to reset and start over */
  onReset: () => void
  /** Whether to show the interactive chat panel */
  showChat?: boolean
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
export function OutputPlayer({ result, onReset, showChat = true }: OutputPlayerProps) {
  const [activeTab, setActiveTab] = useState<'video' | 'details'>('video')
  const [isMuted, setIsMuted] = useState(true)
  const [isChatOpen, setIsChatOpen] = useState(false)
  const videoRef = useRef<HTMLVideoElement>(null)

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

  return (
    <div className={`flex ${isChatOpen ? 'gap-4' : ''}`}>
      {/* Main content area */}
      <div className={`card space-y-6 ${isChatOpen ? 'flex-[7]' : 'w-full'}`}>
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

          {/* Chat toggle button */}
          {showChat && !isChatOpen && (
            <button
              className="btn-outline flex items-center gap-2"
              onClick={toggleChat}
            >
              <svg
                className="w-4 h-4"
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
              Chat
            </button>
          )}
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
                  d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3"
                />
              </svg>
              Audio Only
            </button>
            <button
              className="btn-outline"
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

      {/* Chat Panel (side-by-side on desktop, hidden until toggled) */}
      {showChat && isChatOpen && (
        <div className="flex-[3] min-w-[300px] max-w-[400px] h-[600px] rounded-lg overflow-hidden border border-border">
          <ChatPanel
            jobId={result.job_id}
            isVisible={isChatOpen}
            onClose={() => setIsChatOpen(false)}
            onInteraction={handleChatInteraction}
            enableVoice={false}
          />
        </div>
      )}
    </div>
  )
}
