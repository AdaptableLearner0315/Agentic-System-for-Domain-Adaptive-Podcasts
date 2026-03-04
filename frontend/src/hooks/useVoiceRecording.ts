/**
 * React hook for voice recording using MediaRecorder API.
 *
 * Provides push-to-talk functionality for voice input in
 * interactive conversations.
 */

import { useState, useRef, useCallback, useEffect } from 'react'
import type { UseVoiceRecordingReturn } from '@/types'

// Recording configuration optimized for Whisper
const RECORDING_CONFIG = {
  mimeType: 'audio/webm;codecs=opus',
  sampleRate: 16000,
  echoCancellation: true,
  noiseSuppression: true,
}

/**
 * Hook for voice recording with push-to-talk.
 *
 * Uses the MediaRecorder API to capture audio with settings
 * optimized for speech recognition.
 *
 * @returns Voice recording state and controls
 *
 * @example
 * ```tsx
 * const { isRecording, startRecording, stopRecording } = useVoiceRecording()
 *
 * const handleVoice = async () => {
 *   await startRecording()
 *   // ... user speaks ...
 *   const blob = await stopRecording()
 *   // Send blob to STT API
 * }
 * ```
 */
export function useVoiceRecording(): UseVoiceRecordingReturn {
  const [isRecording, setIsRecording] = useState(false)
  const [audioLevel, setAudioLevel] = useState(0)
  const [hasPermission, setHasPermission] = useState(false)
  const [duration, setDuration] = useState(0)
  const [error, setError] = useState<string | null>(null)

  // Refs for recording state
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const audioChunksRef = useRef<Blob[]>([])
  const streamRef = useRef<MediaStream | null>(null)
  const analyserRef = useRef<AnalyserNode | null>(null)
  const animationFrameRef = useRef<number | null>(null)
  const durationIntervalRef = useRef<NodeJS.Timeout | null>(null)
  const startTimeRef = useRef<number>(0)

  /**
   * Cleanup all resources.
   */
  const cleanup = useCallback(() => {
    // Stop animation frame
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current)
      animationFrameRef.current = null
    }

    // Stop duration interval
    if (durationIntervalRef.current) {
      clearInterval(durationIntervalRef.current)
      durationIntervalRef.current = null
    }

    // Stop media recorder
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      try {
        mediaRecorderRef.current.stop()
      } catch {
        // Ignore errors on cleanup
      }
    }

    // Stop media stream tracks
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop())
      streamRef.current = null
    }

    // Reset state
    mediaRecorderRef.current = null
    analyserRef.current = null
    audioChunksRef.current = []
    setAudioLevel(0)
    setDuration(0)
  }, [])

  // Cleanup on unmount
  useEffect(() => {
    return cleanup
  }, [cleanup])

  /**
   * Request microphone permission.
   */
  const requestPermission = useCallback(async (): Promise<boolean> => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: RECORDING_CONFIG.echoCancellation,
          noiseSuppression: RECORDING_CONFIG.noiseSuppression,
          sampleRate: RECORDING_CONFIG.sampleRate,
        },
      })

      // Permission granted, stop the test stream
      stream.getTracks().forEach((track) => track.stop())
      setHasPermission(true)
      setError(null)
      return true
    } catch (e) {
      setHasPermission(false)
      if (e instanceof DOMException) {
        if (e.name === 'NotAllowedError') {
          setError('Microphone permission denied')
        } else if (e.name === 'NotFoundError') {
          setError('No microphone found')
        } else {
          setError(`Microphone error: ${e.message}`)
        }
      } else {
        setError('Failed to access microphone')
      }
      return false
    }
  }, [])

  /**
   * Check permission on mount.
   */
  useEffect(() => {
    // Check if we already have permission
    navigator.permissions
      ?.query({ name: 'microphone' as PermissionName })
      .then((result) => {
        setHasPermission(result.state === 'granted')
      })
      .catch(() => {
        // Permissions API not supported, will check on first use
      })
  }, [])

  /**
   * Update audio level visualization.
   */
  const updateAudioLevel = useCallback(() => {
    if (!analyserRef.current) return

    const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount)
    analyserRef.current.getByteFrequencyData(dataArray)

    // Calculate average level
    const average = dataArray.reduce((a, b) => a + b, 0) / dataArray.length
    const normalizedLevel = average / 255

    setAudioLevel(normalizedLevel)

    // Continue animation
    if (isRecording) {
      animationFrameRef.current = requestAnimationFrame(updateAudioLevel)
    }
  }, [isRecording])

  /**
   * Start recording audio.
   */
  const startRecording = useCallback(async (): Promise<void> => {
    // Check permission first
    if (!hasPermission) {
      const granted = await requestPermission()
      if (!granted) return
    }

    setError(null)
    audioChunksRef.current = []

    try {
      // Get media stream
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: RECORDING_CONFIG.echoCancellation,
          noiseSuppression: RECORDING_CONFIG.noiseSuppression,
          sampleRate: RECORDING_CONFIG.sampleRate,
        },
      })
      streamRef.current = stream

      // Set up audio analyzer for visualizer
      const audioContext = new AudioContext()
      const source = audioContext.createMediaStreamSource(stream)
      const analyser = audioContext.createAnalyser()
      analyser.fftSize = 256
      source.connect(analyser)
      analyserRef.current = analyser

      // Check for supported MIME type
      let mimeType = RECORDING_CONFIG.mimeType
      if (!MediaRecorder.isTypeSupported(mimeType)) {
        // Fallback to webm without codecs specification
        mimeType = 'audio/webm'
        if (!MediaRecorder.isTypeSupported(mimeType)) {
          throw new Error('No supported audio format found')
        }
      }

      // Create media recorder
      const mediaRecorder = new MediaRecorder(stream, { mimeType })
      mediaRecorderRef.current = mediaRecorder

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data)
        }
      }

      mediaRecorder.onerror = () => {
        setError('Recording error')
        cleanup()
      }

      // Start recording
      mediaRecorder.start(100) // Collect data every 100ms
      setIsRecording(true)

      // Start duration timer
      startTimeRef.current = Date.now()
      durationIntervalRef.current = setInterval(() => {
        setDuration(Math.floor((Date.now() - startTimeRef.current) / 1000))
      }, 100)

      // Start audio level visualization
      animationFrameRef.current = requestAnimationFrame(updateAudioLevel)
    } catch (e) {
      cleanup()
      if (e instanceof Error) {
        setError(e.message)
      } else {
        setError('Failed to start recording')
      }
    }
  }, [hasPermission, requestPermission, cleanup, updateAudioLevel])

  /**
   * Stop recording and return audio blob.
   */
  const stopRecording = useCallback(async (): Promise<Blob | null> => {
    return new Promise((resolve) => {
      const mediaRecorder = mediaRecorderRef.current

      if (!mediaRecorder || mediaRecorder.state === 'inactive') {
        setIsRecording(false)
        resolve(null)
        return
      }

      mediaRecorder.onstop = () => {
        // Create blob from chunks
        const blob = new Blob(audioChunksRef.current, { type: 'audio/webm' })

        // Cleanup
        cleanup()
        setIsRecording(false)

        // Return blob (even if empty, let caller decide)
        resolve(blob.size > 0 ? blob : null)
      }

      // Stop recording
      mediaRecorder.stop()
    })
  }, [cleanup])

  return {
    isRecording,
    audioLevel,
    hasPermission,
    duration,
    startRecording,
    stopRecording,
    requestPermission,
    error,
  }
}
