/**
 * React hook for audio playback management.
 *
 * Provides controls for playing TTS audio responses with
 * queueing support for sequential playback.
 */

import { useState, useRef, useCallback, useEffect } from 'react'
import type { UseAudioPlaybackReturn, AudioQueueItem } from '@/types'
import { API_URL } from '@/lib/api'

/**
 * Hook for audio playback with queue support.
 *
 * Manages audio playback state, supports queueing for
 * sequential playback, and provides play/stop controls.
 *
 * @returns Audio playback state and controls
 *
 * @example
 * ```tsx
 * const { isPlaying, play, queue, currentMessageId } = useAudioPlayback()
 *
 * // Play immediately
 * play('/api/interactive/audio/123', '123')
 *
 * // Add to queue
 * queue('/api/interactive/audio/456', '456')
 * ```
 */
export function useAudioPlayback(): UseAudioPlaybackReturn {
  const [isPlaying, setIsPlaying] = useState(false)
  const [currentMessageId, setCurrentMessageId] = useState<string | null>(null)

  // Audio element ref
  const audioRef = useRef<HTMLAudioElement | null>(null)

  // Playback queue
  const queueRef = useRef<AudioQueueItem[]>([])

  // Flag to track if we're processing queue
  const processingRef = useRef(false)

  /**
   * Process the next item in the queue.
   */
  const processQueue = useCallback(() => {
    if (processingRef.current || queueRef.current.length === 0) {
      return
    }

    const nextItem = queueRef.current.shift()
    if (!nextItem) return

    processingRef.current = true
    playInternal(nextItem.url, nextItem.messageId)
  }, [])

  /**
   * Internal play function.
   */
  const playInternal = useCallback(
    (url: string, messageId: string) => {
      // Stop current audio if playing
      if (audioRef.current) {
        audioRef.current.pause()
        audioRef.current = null
      }

      // Construct full URL if relative
      const fullUrl = url.startsWith('http') ? url : `${API_URL}${url}`

      // Create new audio element
      const audio = new Audio(fullUrl)
      audioRef.current = audio

      audio.onplay = () => {
        setIsPlaying(true)
        setCurrentMessageId(messageId)
      }

      audio.onended = () => {
        setIsPlaying(false)
        setCurrentMessageId(null)
        processingRef.current = false
        // Process next item in queue
        processQueue()
      }

      audio.onerror = () => {
        setIsPlaying(false)
        setCurrentMessageId(null)
        processingRef.current = false
        // Process next item in queue even on error
        processQueue()
      }

      audio.onpause = () => {
        if (!audio.ended) {
          // Paused but not ended - still considered playing state for UI
        }
      }

      // Start playback
      audio.play().catch(() => {
        setIsPlaying(false)
        setCurrentMessageId(null)
        processingRef.current = false
        processQueue()
      })
    },
    [processQueue]
  )

  /**
   * Play audio immediately (stops current and clears queue).
   */
  const play = useCallback(
    (url: string, messageId: string) => {
      // Clear queue
      queueRef.current = []
      processingRef.current = false

      // Stop current audio
      if (audioRef.current) {
        audioRef.current.pause()
        audioRef.current = null
      }

      // Play new audio
      playInternal(url, messageId)
    },
    [playInternal]
  )

  /**
   * Stop playback and clear queue.
   */
  const stop = useCallback(() => {
    // Clear queue
    queueRef.current = []
    processingRef.current = false

    // Stop current audio
    if (audioRef.current) {
      audioRef.current.pause()
      audioRef.current = null
    }

    setIsPlaying(false)
    setCurrentMessageId(null)
  }, [])

  /**
   * Add audio to playback queue.
   */
  const queue = useCallback(
    (url: string, messageId: string) => {
      queueRef.current.push({ url, messageId })

      // Start processing if not already
      if (!isPlaying && !processingRef.current) {
        processQueue()
      }
    },
    [isPlaying, processQueue]
  )

  /**
   * Clear the playback queue (doesn't stop current audio).
   */
  const clearQueue = useCallback(() => {
    queueRef.current = []
  }, [])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (audioRef.current) {
        audioRef.current.pause()
        audioRef.current = null
      }
      queueRef.current = []
    }
  }, [])

  return {
    isPlaying,
    currentMessageId,
    play,
    stop,
    queue,
    clearQueue,
  }
}
