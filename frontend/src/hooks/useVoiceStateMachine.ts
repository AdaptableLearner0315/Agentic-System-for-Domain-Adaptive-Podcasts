/**
 * Voice state machine hook for orchestrating the voice experience.
 *
 * Manages transitions between states: idle, listening, recording, paused,
 * countdown, processing, and speaking.
 */

import { useState, useCallback, useRef, useEffect } from 'react'

/**
 * Voice experience states.
 */
export type VoiceState =
  | 'idle'
  | 'listening'
  | 'recording'
  | 'paused'
  | 'countdown'
  | 'processing'
  | 'speaking'

/**
 * Events that trigger state transitions.
 */
export type VoiceEvent =
  | 'tap'
  | 'speech_start'
  | 'speech_end'
  | 'silence_detected'
  | 'countdown_complete'
  | 'response_ready'
  | 'speaking_complete'
  | 'interrupt'
  | 'cancel'
  | 'error'

/**
 * Voice state machine configuration.
 */
export interface VoiceStateMachineConfig {
  /** Callback when entering a state */
  onStateEnter?: (state: VoiceState, previousState: VoiceState) => void
  /** Callback when a transition fails */
  onTransitionError?: (event: VoiceEvent, currentState: VoiceState) => void
  /** Initial state */
  initialState?: VoiceState
}

/**
 * State machine transition table.
 */
const TRANSITIONS: Record<VoiceState, Partial<Record<VoiceEvent, VoiceState>>> = {
  idle: {
    tap: 'listening',
  },
  listening: {
    speech_start: 'recording',
    tap: 'idle',
    cancel: 'idle',
    error: 'idle',
  },
  recording: {
    speech_end: 'paused',
    tap: 'processing', // Manual send
    cancel: 'idle',
    error: 'idle',
  },
  paused: {
    speech_start: 'recording', // User continued speaking
    silence_detected: 'countdown',
    tap: 'processing', // Manual send
    cancel: 'idle',
    error: 'idle',
  },
  countdown: {
    speech_start: 'recording', // User spoke again, cancel countdown
    countdown_complete: 'processing',
    tap: 'processing', // Manual send
    cancel: 'idle',
    error: 'idle',
  },
  processing: {
    response_ready: 'speaking',
    error: 'idle',
    cancel: 'idle',
  },
  speaking: {
    interrupt: 'listening', // User interrupted AI
    speaking_complete: 'listening', // Continue conversation
    tap: 'idle', // User tapped to stop
    cancel: 'idle',
    error: 'idle',
  },
}

/**
 * Return type for useVoiceStateMachine hook.
 */
export interface UseVoiceStateMachineReturn {
  /** Current state */
  state: VoiceState
  /** Previous state */
  previousState: VoiceState | null
  /** Send an event to the state machine */
  send: (event: VoiceEvent) => boolean
  /** Check if a transition is valid */
  canTransition: (event: VoiceEvent) => boolean
  /** Reset to initial state */
  reset: () => void
  /** Whether the user is actively speaking/recording */
  isUserActive: boolean
  /** Whether the AI is processing or speaking */
  isAiActive: boolean
  /** Whether the system is in an interruptible state */
  isInterruptible: boolean
}

/**
 * Hook for managing voice experience state transitions.
 *
 * Implements a finite state machine for the voice interaction flow,
 * ensuring valid transitions between states.
 *
 * @param config - Configuration options
 * @returns State machine controls and current state
 *
 * @example
 * ```tsx
 * const { state, send, isUserActive } = useVoiceStateMachine({
 *   onStateEnter: (state) => console.log(`Entered ${state}`),
 * })
 *
 * // Handle mic button tap
 * const handleTap = () => send('tap')
 *
 * // Handle speech detection
 * const onSpeechStart = () => send('speech_start')
 * ```
 */
export function useVoiceStateMachine(
  config: VoiceStateMachineConfig = {}
): UseVoiceStateMachineReturn {
  const { onStateEnter, onTransitionError, initialState = 'idle' } = config

  const [state, setState] = useState<VoiceState>(initialState)
  const [previousState, setPreviousState] = useState<VoiceState | null>(null)

  // Use ref for callback to avoid stale closures
  const onStateEnterRef = useRef(onStateEnter)
  const onTransitionErrorRef = useRef(onTransitionError)

  useEffect(() => {
    onStateEnterRef.current = onStateEnter
    onTransitionErrorRef.current = onTransitionError
  }, [onStateEnter, onTransitionError])

  /**
   * Check if a transition is valid from current state.
   */
  const canTransition = useCallback(
    (event: VoiceEvent): boolean => {
      return TRANSITIONS[state]?.[event] !== undefined
    },
    [state]
  )

  /**
   * Send an event to trigger a state transition.
   */
  const send = useCallback(
    (event: VoiceEvent): boolean => {
      const nextState = TRANSITIONS[state]?.[event]

      if (!nextState) {
        onTransitionErrorRef.current?.(event, state)
        return false
      }

      setPreviousState(state)
      setState(nextState)
      onStateEnterRef.current?.(nextState, state)

      return true
    },
    [state]
  )

  /**
   * Reset to initial state.
   */
  const reset = useCallback(() => {
    setPreviousState(state)
    setState(initialState)
  }, [state, initialState])

  // Derived state helpers
  const isUserActive = state === 'listening' || state === 'recording' || state === 'paused' || state === 'countdown'
  const isAiActive = state === 'processing' || state === 'speaking'
  const isInterruptible = state === 'speaking'

  return {
    state,
    previousState,
    send,
    canTransition,
    reset,
    isUserActive,
    isAiActive,
    isInterruptible,
  }
}
