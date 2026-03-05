/**
 * Voice Activity Detection (VAD) hook for detecting speech and silence.
 *
 * Monitors audio input to detect when the user starts/stops speaking,
 * enabling smart end-of-speech detection.
 */

import { useState, useCallback, useRef, useEffect } from 'react'

/**
 * Voice activity configuration.
 */
export interface VoiceActivityConfig {
  /** Threshold for speech detection (0-1, default 0.02) */
  speechThreshold?: number
  /** Threshold for silence detection (0-1, default 0.01) */
  silenceThreshold?: number
  /** Milliseconds of silence before triggering silence event (default 1500) */
  silenceDelayMs?: number
  /** Minimum speech duration to be considered valid (default 200ms) */
  minSpeechDurationMs?: number
  /** Analysis interval in milliseconds (default 50) */
  analysisIntervalMs?: number
}

/**
 * Return type for useVoiceActivity hook.
 */
export interface UseVoiceActivityReturn {
  /** Whether voice activity is detected */
  isSpeaking: boolean
  /** Current audio level (0-1) */
  audioLevel: number
  /** Whether monitoring is active */
  isMonitoring: boolean
  /** Duration of current speech in milliseconds */
  speechDurationMs: number
  /** Duration of current silence in milliseconds */
  silenceDurationMs: number
  /** Start monitoring audio stream */
  startMonitoring: (stream: MediaStream) => void
  /** Stop monitoring */
  stopMonitoring: () => void
  /** Update configuration */
  updateConfig: (config: Partial<VoiceActivityConfig>) => void
}

const DEFAULT_CONFIG: Required<VoiceActivityConfig> = {
  speechThreshold: 0.02,
  silenceThreshold: 0.01,
  silenceDelayMs: 1500,
  minSpeechDurationMs: 200,
  analysisIntervalMs: 50,
}

/**
 * Hook for detecting voice activity in an audio stream.
 *
 * Uses the Web Audio API to analyze audio levels and detect
 * speech/silence patterns for smart end-of-speech detection.
 *
 * @param config - Configuration options
 * @param onSpeechStart - Callback when speech is detected
 * @param onSpeechEnd - Callback when speech ends (after silence threshold)
 * @param onSilenceDetected - Callback when silence is detected (before full end)
 * @returns Voice activity state and controls
 *
 * @example
 * ```tsx
 * const { isSpeaking, audioLevel, startMonitoring } = useVoiceActivity({
 *   onSpeechStart: () => stateMachine.send('speech_start'),
 *   onSpeechEnd: () => stateMachine.send('speech_end'),
 * })
 *
 * // Start monitoring when recording begins
 * startMonitoring(mediaStream)
 * ```
 */
export function useVoiceActivity(
  config: VoiceActivityConfig = {},
  onSpeechStart?: () => void,
  onSpeechEnd?: () => void,
  onSilenceDetected?: () => void
): UseVoiceActivityReturn {
  const [isSpeaking, setIsSpeaking] = useState(false)
  const [audioLevel, setAudioLevel] = useState(0)
  const [isMonitoring, setIsMonitoring] = useState(false)
  const [speechDurationMs, setSpeechDurationMs] = useState(0)
  const [silenceDurationMs, setSilenceDurationMs] = useState(0)

  // Refs for configuration and state
  const configRef = useRef<Required<VoiceActivityConfig>>({
    ...DEFAULT_CONFIG,
    ...config,
  })
  const audioContextRef = useRef<AudioContext | null>(null)
  const analyserRef = useRef<AnalyserNode | null>(null)
  const animationFrameRef = useRef<number | null>(null)
  const intervalRef = useRef<NodeJS.Timeout | null>(null)

  // Timing refs
  const speechStartTimeRef = useRef<number | null>(null)
  const silenceStartTimeRef = useRef<number | null>(null)
  const wasSpeakingRef = useRef(false)
  const silenceEventFiredRef = useRef(false)

  // Callback refs to avoid stale closures
  const onSpeechStartRef = useRef(onSpeechStart)
  const onSpeechEndRef = useRef(onSpeechEnd)
  const onSilenceDetectedRef = useRef(onSilenceDetected)

  useEffect(() => {
    onSpeechStartRef.current = onSpeechStart
    onSpeechEndRef.current = onSpeechEnd
    onSilenceDetectedRef.current = onSilenceDetected
  }, [onSpeechStart, onSpeechEnd, onSilenceDetected])

  /**
   * Cleanup all resources.
   */
  const cleanup = useCallback(() => {
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current)
      animationFrameRef.current = null
    }

    if (intervalRef.current) {
      clearInterval(intervalRef.current)
      intervalRef.current = null
    }

    if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
      audioContextRef.current.close()
    }

    audioContextRef.current = null
    analyserRef.current = null
    speechStartTimeRef.current = null
    silenceStartTimeRef.current = null
    wasSpeakingRef.current = false
    silenceEventFiredRef.current = false
  }, [])

  // Cleanup on unmount
  useEffect(() => cleanup, [cleanup])

  /**
   * Analyze audio levels.
   */
  const analyzeAudio = useCallback(() => {
    if (!analyserRef.current) return

    const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount)
    analyserRef.current.getByteFrequencyData(dataArray)

    // Calculate RMS (root mean square) for more accurate level detection
    const sum = dataArray.reduce((acc, val) => acc + val * val, 0)
    const rms = Math.sqrt(sum / dataArray.length) / 255
    setAudioLevel(rms)

    const config = configRef.current
    const now = Date.now()

    // Detect speech/silence transitions
    if (rms > config.speechThreshold) {
      // Speech detected
      if (!wasSpeakingRef.current) {
        // Transition from silence to speech
        speechStartTimeRef.current = now
        wasSpeakingRef.current = true
        silenceStartTimeRef.current = null
        silenceEventFiredRef.current = false
        setSilenceDurationMs(0)
        setIsSpeaking(true)
        onSpeechStartRef.current?.()
      }

      // Update speech duration
      if (speechStartTimeRef.current) {
        setSpeechDurationMs(now - speechStartTimeRef.current)
      }
    } else if (rms < config.silenceThreshold) {
      // Silence detected
      if (wasSpeakingRef.current) {
        // Check if speech was long enough to count
        const speechDuration = speechStartTimeRef.current
          ? now - speechStartTimeRef.current
          : 0

        if (speechDuration >= config.minSpeechDurationMs) {
          // Valid speech ended, start silence timer
          if (!silenceStartTimeRef.current) {
            silenceStartTimeRef.current = now
          }

          const silenceDuration = now - silenceStartTimeRef.current
          setSilenceDurationMs(silenceDuration)

          // Fire silence detected callback once
          if (silenceDuration >= config.silenceDelayMs && !silenceEventFiredRef.current) {
            silenceEventFiredRef.current = true
            setIsSpeaking(false)
            wasSpeakingRef.current = false
            onSilenceDetectedRef.current?.()
            onSpeechEndRef.current?.()
          }
        } else {
          // Speech was too short, ignore it
          wasSpeakingRef.current = false
          setIsSpeaking(false)
          setSpeechDurationMs(0)
          speechStartTimeRef.current = null
        }
      }
    }
  }, [])

  /**
   * Start monitoring an audio stream.
   */
  const startMonitoring = useCallback(
    (stream: MediaStream) => {
      cleanup()

      try {
        const audioContext = new AudioContext()
        const source = audioContext.createMediaStreamSource(stream)
        const analyser = audioContext.createAnalyser()

        analyser.fftSize = 256
        analyser.smoothingTimeConstant = 0.5
        source.connect(analyser)

        audioContextRef.current = audioContext
        analyserRef.current = analyser

        // Start analysis loop
        intervalRef.current = setInterval(analyzeAudio, configRef.current.analysisIntervalMs)

        setIsMonitoring(true)
      } catch (error) {
        console.error('Failed to start voice activity monitoring:', error)
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
    setIsSpeaking(false)
    setAudioLevel(0)
    setSpeechDurationMs(0)
    setSilenceDurationMs(0)
  }, [cleanup])

  /**
   * Update configuration.
   */
  const updateConfig = useCallback((newConfig: Partial<VoiceActivityConfig>) => {
    configRef.current = {
      ...configRef.current,
      ...newConfig,
    }
  }, [])

  return {
    isSpeaking,
    audioLevel,
    isMonitoring,
    speechDurationMs,
    silenceDurationMs,
    startMonitoring,
    stopMonitoring,
    updateConfig,
  }
}
