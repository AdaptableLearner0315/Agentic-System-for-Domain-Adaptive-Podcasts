'use client'

/**
 * Main voice experience container component.
 *
 * Orchestrates the complete voice interaction flow including:
 * - Tap-to-talk recording
 * - Smart end-of-speech detection
 * - Real-time transcription
 * - AI response playback
 * - Interruption handling
 */

import { useState, useEffect, useCallback, useRef } from 'react'
import { useVoiceStateMachine } from '@/hooks/useVoiceStateMachine'
import { useVoiceActivity } from '@/hooks/useVoiceActivity'
import { useAdaptiveThreshold } from '@/hooks/useAdaptiveThreshold'
import { useInterruption } from '@/hooks/useInterruption'
import { useStreamingTranscript } from '@/hooks/useStreamingTranscript'
import { useVoiceRecording } from '@/hooks/useVoiceRecording'
import { VoiceButton } from './VoiceButton'
import { CountdownRing } from './CountdownRing'
import { VoiceVisualizer } from './VoiceVisualizer'
import { TranscriptPreview } from './TranscriptPreview'
import { VoiceAvatar } from './VoiceAvatar'
import { sendVoiceMessage } from '@/lib/api'
import type { VoiceState } from '@/types/interactive'

interface VoiceExperienceProps {
  /** Podcast job ID for the session */
  jobId: string
  /** Callback when a message is sent */
  onSend: (message: string) => void
  /** Callback when user starts interacting */
  onInteraction?: () => void
  /** Whether voice input is disabled */
  disabled?: boolean
  /** Whether the system is connecting (shows connecting indicator on button) */
  isConnecting?: boolean
  /** Current AI response text (for display) */
  aiResponseText?: string
  /** Whether AI is currently generating a response */
  isAiProcessing?: boolean
  /** Whether AI audio is currently playing */
  isAiSpeaking?: boolean
  /** Callback to stop AI audio */
  onStopAudio?: () => void
  /** Layout variant */
  layout?: 'compact' | 'full'
}

/**
 * Complete voice experience component.
 *
 * Provides tap-to-talk interaction with smart end-of-speech detection,
 * real-time transcription, and AI response visualization.
 *
 * @example
 * ```tsx
 * <VoiceExperience
 *   jobId={jobId}
 *   onSend={(text) => sendMessage(text)}
 *   isAiSpeaking={isPlaying}
 *   onStopAudio={() => stopPlayback()}
 * />
 * ```
 */
export function VoiceExperience({
  jobId,
  onSend,
  onInteraction,
  disabled = false,
  isConnecting = false,
  aiResponseText,
  isAiProcessing = false,
  isAiSpeaking = false,
  onStopAudio,
  layout = 'full',
}: VoiceExperienceProps) {
  // State machine for voice flow
  const {
    state,
    previousState,
    send: sendEvent,
    isUserActive,
    isAiActive,
    isInterruptible,
  } = useVoiceStateMachine({
    onStateEnter: (newState, prevState) => {
      console.log(`Voice state: ${prevState} -> ${newState}`)
    },
  })

  // Adaptive threshold learning
  const {
    silenceThresholdMs,
    countdownMs,
    recordPause,
    recordFalsePositive,
    recordSuccess,
  } = useAdaptiveThreshold()

  // Voice recording
  const {
    isRecording,
    audioLevel,
    duration,
    startRecording,
    stopRecording,
    requestPermission,
    hasPermission,
    getStream,
  } = useVoiceRecording()

  // Streaming transcription
  const {
    transcript,
    finalTranscript,
    interimTranscript,
    isListening: isTranscribing,
    isSupported: transcriptionSupported,
    startListening: startTranscript,
    stopListening: stopTranscript,
    clearTranscript,
  } = useStreamingTranscript()

  // Voice activity detection
  const streamRef = useRef<MediaStream | null>(null)
  const { audioLevel: vadLevel, startMonitoring, stopMonitoring } = useVoiceActivity(
    {
      silenceDelayMs: silenceThresholdMs,
    },
    () => sendEvent('speech_start'),
    () => sendEvent('speech_end'),
    () => sendEvent('silence_detected')
  )

  // Interruption detection
  const { startMonitoring: startInterruption, stopMonitoring: stopInterruption } =
    useInterruption({}, () => {
      if (isInterruptible) {
        onStopAudio?.()
        sendEvent('interrupt')
      }
    })

  // Countdown state
  const [countdownProgress, setCountdownProgress] = useState(0)
  const countdownStartRef = useRef<number | null>(null)
  const countdownIntervalRef = useRef<NodeJS.Timeout | null>(null)

  // Track recording audio blob
  const audioBlobRef = useRef<Blob | null>(null)

  // Sync external AI state with state machine
  useEffect(() => {
    if (isAiProcessing && state !== 'processing') {
      sendEvent('response_ready')
    }
  }, [isAiProcessing, state, sendEvent])

  useEffect(() => {
    if (isAiSpeaking && state === 'processing') {
      sendEvent('response_ready')
    }
    if (!isAiSpeaking && state === 'speaking') {
      sendEvent('speaking_complete')
    }
  }, [isAiSpeaking, state, sendEvent])

  /**
   * Handle mic button tap.
   */
  const handleTap = useCallback(async () => {
    if (disabled) return

    onInteraction?.()

    switch (state) {
      case 'idle':
        // Start listening
        if (!hasPermission) {
          const granted = await requestPermission()
          if (!granted) return
        }
        sendEvent('tap')
        break

      case 'listening':
      case 'recording':
      case 'paused':
      case 'countdown':
        // Manual send
        sendEvent('tap')
        break

      case 'speaking':
        // Stop AI
        onStopAudio?.()
        sendEvent('tap')
        break

      default:
        break
    }
  }, [
    disabled,
    state,
    hasPermission,
    requestPermission,
    sendEvent,
    onInteraction,
    onStopAudio,
  ])

  /**
   * Handle state transitions.
   */
  useEffect(() => {
    const handleStateChange = async () => {
      switch (state) {
        case 'listening':
          // Start recording and transcription
          clearTranscript()
          await startRecording()
          if (transcriptionSupported) {
            startTranscript()
          }
          // Use the same MediaStream for VAD (shared with recording)
          // Small delay to ensure stream is established after startRecording
          setTimeout(() => {
            const stream = getStream()
            if (stream) {
              streamRef.current = stream
              startMonitoring(stream)
            } else {
              console.warn('VoiceExperience: No stream available for VAD')
            }
          }, 100)
          break

        case 'recording':
          // Continue recording, VAD is already running
          break

        case 'paused':
          // Start watching for silence to trigger countdown
          break

        case 'countdown':
          // Start countdown timer
          countdownStartRef.current = Date.now()
          setCountdownProgress(0)
          countdownIntervalRef.current = setInterval(() => {
            if (countdownStartRef.current) {
              const elapsed = Date.now() - countdownStartRef.current
              const progress = Math.min(elapsed / countdownMs, 1)
              setCountdownProgress(progress)

              if (progress >= 1) {
                sendEvent('countdown_complete')
              }
            }
          }, 50)
          break

        case 'processing':
          // Stop recording and send
          if (countdownIntervalRef.current) {
            clearInterval(countdownIntervalRef.current)
            countdownIntervalRef.current = null
          }
          setCountdownProgress(0)
          countdownStartRef.current = null

          stopTranscript()
          stopMonitoring()

          // Clear ref but don't stop tracks - useVoiceRecording owns the stream
          streamRef.current = null

          const blob = await stopRecording()
          if (blob && blob.size > 0) {
            audioBlobRef.current = blob
            // Transcribe and send
            try {
              const result = await sendVoiceMessage(jobId, blob, true)
              if (result.transcription) {
                recordSuccess()
                onSend(result.transcription)
              }
            } catch (error) {
              console.error('Voice transcription failed:', error)
              sendEvent('error')
            }
          } else if (finalTranscript) {
            // Use browser transcript if no audio
            recordSuccess()
            onSend(finalTranscript)
          }
          break

        case 'speaking':
          // Start interruption detection if we have a stream
          if (streamRef.current) {
            startInterruption(streamRef.current)
          }
          break

        case 'idle':
          // Cleanup
          if (countdownIntervalRef.current) {
            clearInterval(countdownIntervalRef.current)
            countdownIntervalRef.current = null
          }
          setCountdownProgress(0)
          stopMonitoring()
          stopInterruption()
          // Clear ref but don't stop tracks - useVoiceRecording owns the stream
          streamRef.current = null
          break
      }
    }

    handleStateChange()
  }, [state])

  // Track pauses for adaptive learning
  useEffect(() => {
    if (previousState === 'recording' && state === 'paused') {
      // User paused speaking, this is a natural pause
    }
    if (previousState === 'countdown' && state === 'recording') {
      // User spoke during countdown - false positive
      recordFalsePositive()
    }
  }, [state, previousState, recordFalsePositive])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (countdownIntervalRef.current) {
        clearInterval(countdownIntervalRef.current)
      }
      // Don't stop stream tracks - useVoiceRecording owns the stream
      streamRef.current = null
    }
  }, [])

  const effectiveAudioLevel = isRecording ? audioLevel : vadLevel

  if (layout === 'compact') {
    return (
      <CountdownRing
        progress={countdownProgress}
        isActive={state === 'countdown'}
        size={56}
      >
        <VoiceButton
          state={state}
          audioLevel={effectiveAudioLevel}
          countdownProgress={countdownProgress}
          disabled={disabled}
          isConnecting={isConnecting}
          onClick={handleTap}
          size="sm"
        />
      </CountdownRing>
    )
  }

  return (
    <div className="flex flex-col items-center gap-4 p-4">
      {/* AI Response Area */}
      {(state === 'speaking' || (isAiActive && aiResponseText)) && (
        <div className="w-full mb-2">
          <VoiceAvatar
            isSpeaking={isAiSpeaking}
            text={aiResponseText}
            size="md"
          />
        </div>
      )}

      {/* Voice Button with Countdown */}
      <CountdownRing
        progress={countdownProgress}
        isActive={state === 'countdown'}
        size={96}
      >
        <VoiceButton
          state={state}
          audioLevel={effectiveAudioLevel}
          countdownProgress={countdownProgress}
          disabled={disabled}
          isConnecting={isConnecting}
          onClick={handleTap}
          size="lg"
        />
      </CountdownRing>

      {/* Visualizer */}
      {isUserActive && (
        <VoiceVisualizer
          state={state}
          audioLevel={effectiveAudioLevel}
          duration={duration}
        />
      )}

      {/* Transcript Preview */}
      {isUserActive && (
        <div className="w-full max-w-md">
          <TranscriptPreview
            finalText={finalTranscript}
            interimText={interimTranscript}
            isListening={isTranscribing}
            showConfidence={false}
          />
        </div>
      )}

      {/* Status Text */}
      <StatusText state={state} countdownProgress={countdownProgress} countdownMs={countdownMs} />
    </div>
  )
}

/**
 * Status text component for current state.
 */
function StatusText({
  state,
  countdownProgress,
  countdownMs,
}: {
  state: VoiceState
  countdownProgress: number
  countdownMs: number
}) {
  const getRemainingSeconds = () => {
    const remaining = (1 - countdownProgress) * (countdownMs / 1000)
    return Math.ceil(remaining)
  }

  switch (state) {
    case 'idle':
      return <span className="text-sm text-muted-foreground">Tap to speak</span>
    case 'listening':
      return <span className="text-sm text-primary animate-pulse">Listening...</span>
    case 'recording':
      return <span className="text-sm text-destructive">Recording...</span>
    case 'paused':
      return <span className="text-sm text-amber-500">Still listening...</span>
    case 'countdown':
      return (
        <span className="text-sm text-amber-600 font-medium">
          Sending in {getRemainingSeconds()}...
        </span>
      )
    case 'processing':
      return <span className="text-sm text-primary">Thinking...</span>
    case 'speaking':
      return <span className="text-sm text-success">Speaking... Tap to stop</span>
    default:
      return null
  }
}
