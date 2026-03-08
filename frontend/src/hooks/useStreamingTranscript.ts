/**
 * Streaming transcript hook for real-time speech-to-text display.
 *
 * Provides real-time transcription feedback as the user speaks,
 * using the Web Speech API for browser-based recognition.
 */

import { useState, useCallback, useRef, useEffect } from 'react'

/**
 * Streaming transcript configuration.
 */
export interface StreamingTranscriptConfig {
  /** Language for recognition (default 'en-US') */
  language?: string
  /** Whether to use continuous recognition (default true) */
  continuous?: boolean
  /** Whether to show interim results (default true) */
  interimResults?: boolean
  /** Maximum alternatives to consider (default 1) */
  maxAlternatives?: number
}

/**
 * Transcript segment with confidence.
 */
export interface TranscriptSegment {
  /** Transcribed text */
  text: string
  /** Whether this is a final result */
  isFinal: boolean
  /** Confidence score (0-1) */
  confidence: number
  /** Timestamp when recognized */
  timestamp: number
}

/**
 * Return type for useStreamingTranscript hook.
 */
export interface UseStreamingTranscriptReturn {
  /** Current transcript text (final + interim) */
  transcript: string
  /** Only final transcript text */
  finalTranscript: string
  /** Current interim transcript text */
  interimTranscript: string
  /** Whether recognition is active */
  isListening: boolean
  /** Whether the browser supports speech recognition */
  isSupported: boolean
  /** Error message if any */
  error: string | null
  /** All transcript segments */
  segments: TranscriptSegment[]
  /** Start listening for speech */
  startListening: () => void
  /** Stop listening */
  stopListening: () => void
  /** Clear transcript */
  clearTranscript: () => void
  /** Confidence of latest recognition (0-1) */
  confidence: number
}

const DEFAULT_CONFIG: Required<StreamingTranscriptConfig> = {
  language: 'en-US',
  continuous: true,
  interimResults: true,
  maxAlternatives: 1,
}

/**
 * Check if Web Speech API is available.
 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
type SpeechRecognitionConstructor = new () => any

function getSpeechRecognition(): SpeechRecognitionConstructor | null {
  if (typeof window === 'undefined') return null

  // Check for vendor prefixes
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const win = window as any
  const RecognitionAPI = win.SpeechRecognition || win.webkitSpeechRecognition

  return RecognitionAPI || null
}

/**
 * Hook for real-time streaming speech transcription.
 *
 * Uses the Web Speech API to provide live transcription feedback
 * as the user speaks, showing interim results that update in real-time.
 *
 * @param config - Configuration options
 * @param onFinalTranscript - Callback when final transcript is available
 * @returns Streaming transcript state and controls
 *
 * @example
 * ```tsx
 * const { transcript, startListening, stopListening } = useStreamingTranscript({
 *   onFinalTranscript: (text) => console.log('Final:', text),
 * })
 *
 * // Show real-time transcript
 * <TranscriptPreview text={transcript} />
 * ```
 */
export function useStreamingTranscript(
  config: StreamingTranscriptConfig = {},
  onFinalTranscript?: (text: string) => void
): UseStreamingTranscriptReturn {
  const [transcript, setTranscript] = useState('')
  const [finalTranscript, setFinalTranscript] = useState('')
  const [interimTranscript, setInterimTranscript] = useState('')
  const [isListening, setIsListening] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [segments, setSegments] = useState<TranscriptSegment[]>([])
  const [confidence, setConfidence] = useState(0)

  // Check browser support
  const SpeechRecognitionClass = getSpeechRecognition()
  const isSupported = SpeechRecognitionClass !== null

  // Refs
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const recognitionRef = useRef<any>(null)
  const configRef = useRef<Required<StreamingTranscriptConfig>>({
    ...DEFAULT_CONFIG,
    ...config,
  })
  const onFinalTranscriptRef = useRef(onFinalTranscript)

  useEffect(() => {
    onFinalTranscriptRef.current = onFinalTranscript
  }, [onFinalTranscript])

  /**
   * Cleanup recognition instance.
   */
  const cleanup = useCallback(() => {
    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop()
      } catch {
        // Ignore errors on cleanup
      }
      recognitionRef.current = null
    }
  }, [])

  // Cleanup on unmount
  useEffect(() => cleanup, [cleanup])

  /**
   * Start listening for speech.
   */
  const startListening = useCallback(() => {
    if (!SpeechRecognitionClass) {
      setError('Speech recognition not supported in this browser')
      return
    }

    cleanup()
    setError(null)

    const recognition = new SpeechRecognitionClass()
    const cfg = configRef.current

    recognition.lang = cfg.language
    recognition.continuous = cfg.continuous
    recognition.interimResults = cfg.interimResults
    recognition.maxAlternatives = cfg.maxAlternatives

    recognition.onstart = () => {
      setIsListening(true)
      setError(null)
    }

    recognition.onend = () => {
      setIsListening(false)
      // Auto-restart if still supposed to be listening (for continuous mode)
      // This handles the browser's automatic stops
    }

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    recognition.onerror = (event: any) => {
      // Don't treat 'aborted' as an error (happens when we stop manually)
      if (event.error === 'aborted') return

      setError(event.error)
      setIsListening(false)
    }

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    recognition.onresult = (event: any) => {
      let final = ''
      let interim = ''
      let latestConfidence = 0

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const result = event.results[i]
        const text = result[0].transcript
        const resultConfidence = result[0].confidence || 0

        if (result.isFinal) {
          final += text
          latestConfidence = resultConfidence

          // Add to segments
          const segment: TranscriptSegment = {
            text,
            isFinal: true,
            confidence: resultConfidence,
            timestamp: Date.now(),
          }
          setSegments((prev) => [...prev, segment])

          // Fire callback
          onFinalTranscriptRef.current?.(text)
        } else {
          interim += text
          latestConfidence = Math.max(latestConfidence, resultConfidence)
        }
      }

      // Update state
      if (final) {
        setFinalTranscript((prev) => prev + final)
      }
      setInterimTranscript(interim)
      setTranscript((prev) => (final ? prev + final : prev.replace(/\[.*\]$/, '')) + (interim ? `[${interim}]` : ''))
      setConfidence(latestConfidence)
    }

    try {
      recognition.start()
      recognitionRef.current = recognition
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to start recognition')
    }
  }, [SpeechRecognitionClass, cleanup])

  /**
   * Stop listening.
   */
  const stopListening = useCallback(() => {
    cleanup()
    setIsListening(false)
    // Finalize any interim transcript
    if (interimTranscript) {
      setFinalTranscript((prev) => prev + interimTranscript)
      setTranscript((prev) => prev.replace(/\[.*\]$/, '') + interimTranscript)
      setInterimTranscript('')
    }
  }, [cleanup, interimTranscript])

  /**
   * Clear all transcript data.
   */
  const clearTranscript = useCallback(() => {
    setTranscript('')
    setFinalTranscript('')
    setInterimTranscript('')
    setSegments([])
    setConfidence(0)
  }, [])

  return {
    transcript: finalTranscript + (interimTranscript ? ` ${interimTranscript}` : ''),
    finalTranscript,
    interimTranscript,
    isListening,
    isSupported,
    error,
    segments,
    startListening,
    stopListening,
    clearTranscript,
    confidence,
  }
}
