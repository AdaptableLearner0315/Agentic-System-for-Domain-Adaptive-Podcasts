/**
 * Interruption detection hook for handling user speech during AI playback.
 *
 * Monitors the microphone while TTS audio is playing to detect
 * when the user wants to interrupt and take over the conversation.
 */

import { useState, useCallback, useRef, useEffect } from 'react'

/**
 * Interruption configuration.
 */
export interface InterruptionConfig {
  /** Audio level threshold to detect interruption (0-1, default 0.05) */
  interruptionThreshold?: number
  /** Minimum duration of speech to trigger interruption (default 200ms) */
  minDurationMs?: number
  /** Debounce interval for interruption detection (default 100ms) */
  debounceMs?: number
  /** Whether interruption detection is enabled (default true) */
  enabled?: boolean
}

/**
 * Return type for useInterruption hook.
 */
export interface UseInterruptionReturn {
  /** Whether an interruption was detected */
  isInterrupted: boolean
  /** Whether monitoring is active */
  isMonitoring: boolean
  /** Current audio level being monitored */
  audioLevel: number
  /** Start monitoring for interruption */
  startMonitoring: (stream: MediaStream) => void
  /** Stop monitoring */
  stopMonitoring: () => void
  /** Reset interruption state */
  reset: () => void
  /** Update configuration */
  updateConfig: (config: Partial<InterruptionConfig>) => void
}

const DEFAULT_CONFIG: Required<InterruptionConfig> = {
  interruptionThreshold: 0.05,
  minDurationMs: 200,
  debounceMs: 100,
  enabled: true,
}

/**
 * Hook for detecting user interruptions during AI speech.
 *
 * Runs voice activity detection in parallel with TTS playback,
 * triggering an interruption event when significant user speech is detected.
 *
 * @param config - Configuration options
 * @param onInterrupt - Callback when interruption is detected
 * @returns Interruption state and controls
 *
 * @example
 * ```tsx
 * const { startMonitoring, stopMonitoring, reset } = useInterruption({
 *   onInterrupt: () => {
 *     audioPlayer.stop()
 *     stateMachine.send('interrupt')
 *   }
 * })
 *
 * // When AI starts speaking
 * useEffect(() => {
 *   if (state === 'speaking' && stream) {
 *     startMonitoring(stream)
 *   }
 *   return () => stopMonitoring()
 * }, [state])
 * ```
 */
export function useInterruption(
  config: InterruptionConfig = {},
  onInterrupt?: () => void
): UseInterruptionReturn {
  const [isInterrupted, setIsInterrupted] = useState(false)
  const [isMonitoring, setIsMonitoring] = useState(false)
  const [audioLevel, setAudioLevel] = useState(0)

  // Configuration ref
  const configRef = useRef<Required<InterruptionConfig>>({
    ...DEFAULT_CONFIG,
    ...config,
  })

  // Audio analysis refs
  const audioContextRef = useRef<AudioContext | null>(null)
  const analyserRef = useRef<AnalyserNode | null>(null)
  const intervalRef = useRef<NodeJS.Timeout | null>(null)

  // Detection state refs
  const speechStartRef = useRef<number | null>(null)
  const lastInterruptRef = useRef<number>(0)

  // Callback ref
  const onInterruptRef = useRef(onInterrupt)

  useEffect(() => {
    onInterruptRef.current = onInterrupt
  }, [onInterrupt])

  /**
   * Cleanup all resources.
   */
  const cleanup = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current)
      intervalRef.current = null
    }

    if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
      audioContextRef.current.close()
    }

    audioContextRef.current = null
    analyserRef.current = null
    speechStartRef.current = null
  }, [])

  // Cleanup on unmount
  useEffect(() => cleanup, [cleanup])

  /**
   * Analyze audio for interruption.
   */
  const analyzeAudio = useCallback(() => {
    if (!analyserRef.current || !configRef.current.enabled) return

    const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount)
    analyserRef.current.getByteFrequencyData(dataArray)

    // Calculate RMS level
    const sum = dataArray.reduce((acc, val) => acc + val * val, 0)
    const rms = Math.sqrt(sum / dataArray.length) / 255
    setAudioLevel(rms)

    const config = configRef.current
    const now = Date.now()

    // Check if we're above the interruption threshold
    if (rms > config.interruptionThreshold) {
      if (!speechStartRef.current) {
        speechStartRef.current = now
      }

      // Check if speech has been long enough
      const speechDuration = now - speechStartRef.current
      if (speechDuration >= config.minDurationMs) {
        // Check debounce
        if (now - lastInterruptRef.current > config.debounceMs) {
          lastInterruptRef.current = now
          setIsInterrupted(true)
          onInterruptRef.current?.()
        }
      }
    } else {
      // Reset speech start if audio level drops
      speechStartRef.current = null
    }
  }, [])

  /**
   * Start monitoring for interruption.
   */
  const startMonitoring = useCallback(
    (stream: MediaStream) => {
      // Don't start if disabled
      if (!configRef.current.enabled) return

      cleanup()
      setIsInterrupted(false)

      try {
        const audioContext = new AudioContext()
        const source = audioContext.createMediaStreamSource(stream)
        const analyser = audioContext.createAnalyser()

        analyser.fftSize = 256
        analyser.smoothingTimeConstant = 0.3 // Lower smoothing for faster response
        source.connect(analyser)

        audioContextRef.current = audioContext
        analyserRef.current = analyser

        // Start analysis at higher frequency for responsiveness
        intervalRef.current = setInterval(analyzeAudio, 50)

        setIsMonitoring(true)
      } catch (error) {
        console.error('Failed to start interruption monitoring:', error)
        cleanup()
      }
    },
    [cleanup, analyzeAudio]
  )

  /**
   * Stop monitoring.
   */
  const stopMonitoring = useCallback(() => {
    cleanup()
    setIsMonitoring(false)
    setAudioLevel(0)
  }, [cleanup])

  /**
   * Reset interruption state.
   */
  const reset = useCallback(() => {
    setIsInterrupted(false)
    speechStartRef.current = null
    lastInterruptRef.current = 0
  }, [])

  /**
   * Update configuration.
   */
  const updateConfig = useCallback((newConfig: Partial<InterruptionConfig>) => {
    configRef.current = {
      ...configRef.current,
      ...newConfig,
    }
  }, [])

  return {
    isInterrupted,
    isMonitoring,
    audioLevel,
    startMonitoring,
    stopMonitoring,
    reset,
    updateConfig,
  }
}
