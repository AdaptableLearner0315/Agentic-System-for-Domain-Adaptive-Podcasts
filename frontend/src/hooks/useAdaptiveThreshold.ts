/**
 * Adaptive threshold hook for learning user's speaking patterns.
 *
 * Tracks pause durations and adjusts silence thresholds to match
 * the user's natural speech rhythm.
 */

import { useState, useCallback, useRef, useEffect } from 'react'

/**
 * Storage key for persisting learned thresholds.
 */
const STORAGE_KEY = 'nell_voice_thresholds'

/**
 * Maximum number of samples to keep for averaging.
 */
const MAX_SAMPLES = 50

/**
 * Adaptive threshold configuration.
 */
export interface AdaptiveThresholdConfig {
  /** Default silence threshold in milliseconds */
  defaultSilenceMs?: number
  /** Minimum allowed silence threshold */
  minSilenceMs?: number
  /** Maximum allowed silence threshold */
  maxSilenceMs?: number
  /** Countdown duration in milliseconds */
  countdownMs?: number
  /** Whether to persist thresholds across sessions */
  persistThresholds?: boolean
  /** Learning rate (0-1, how much to weight new samples) */
  learningRate?: number
}

/**
 * Threshold data structure.
 */
interface ThresholdData {
  /** Computed silence threshold in milliseconds */
  silenceThresholdMs: number
  /** Historical pause durations */
  pauseSamples: number[]
  /** Number of false positives (user spoke after countdown started) */
  falsePositives: number
  /** Total interactions for calculating rate */
  totalInteractions: number
  /** Last updated timestamp */
  lastUpdated: number
}

/**
 * Return type for useAdaptiveThreshold hook.
 */
export interface UseAdaptiveThresholdReturn {
  /** Current silence threshold in milliseconds */
  silenceThresholdMs: number
  /** Countdown duration in milliseconds */
  countdownMs: number
  /** Record a pause duration sample */
  recordPause: (durationMs: number) => void
  /** Record a false positive (user spoke during countdown) */
  recordFalsePositive: () => void
  /** Record a successful send (no false positive) */
  recordSuccess: () => void
  /** Get false positive rate (0-1) */
  falsePositiveRate: number
  /** Reset learned thresholds */
  resetThresholds: () => void
  /** Whether thresholds have been personalized */
  isPersonalized: boolean
}

const DEFAULT_CONFIG: Required<AdaptiveThresholdConfig> = {
  defaultSilenceMs: 1500,
  minSilenceMs: 800,
  maxSilenceMs: 3000,
  countdownMs: 2000,
  persistThresholds: true,
  learningRate: 0.2,
}

/**
 * Load threshold data from storage.
 */
function loadThresholds(): ThresholdData | null {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored) {
      return JSON.parse(stored)
    }
  } catch {
    // Storage not available or invalid data
  }
  return null
}

/**
 * Save threshold data to storage.
 */
function saveThresholds(data: ThresholdData): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data))
  } catch {
    // Storage not available
  }
}

/**
 * Calculate optimal threshold from pause samples.
 */
function calculateOptimalThreshold(
  samples: number[],
  config: Required<AdaptiveThresholdConfig>
): number {
  if (samples.length < 5) {
    return config.defaultSilenceMs
  }

  // Sort samples and remove outliers (top/bottom 10%)
  const sorted = [...samples].sort((a, b) => a - b)
  const trimStart = Math.floor(sorted.length * 0.1)
  const trimEnd = Math.ceil(sorted.length * 0.9)
  const trimmed = sorted.slice(trimStart, trimEnd)

  if (trimmed.length === 0) {
    return config.defaultSilenceMs
  }

  // Calculate median (more robust than mean)
  const mid = Math.floor(trimmed.length / 2)
  const median =
    trimmed.length % 2 !== 0
      ? trimmed[mid]
      : (trimmed[mid - 1] + trimmed[mid]) / 2

  // Add a buffer (user's typical pause + 20%)
  const withBuffer = median * 1.2

  // Clamp to allowed range
  return Math.max(config.minSilenceMs, Math.min(config.maxSilenceMs, withBuffer))
}

/**
 * Hook for adaptive silence threshold learning.
 *
 * Tracks the user's natural pause patterns and adjusts detection
 * thresholds to reduce false positives while maintaining responsiveness.
 *
 * @param config - Configuration options
 * @returns Adaptive threshold state and controls
 *
 * @example
 * ```tsx
 * const { silenceThresholdMs, recordPause, recordFalsePositive } = useAdaptiveThreshold()
 *
 * // Update VAD config with learned threshold
 * voiceActivity.updateConfig({ silenceDelayMs: silenceThresholdMs })
 *
 * // When user pauses naturally (but continues)
 * recordPause(pauseDuration)
 *
 * // When countdown was interrupted
 * recordFalsePositive()
 * ```
 */
export function useAdaptiveThreshold(
  config: AdaptiveThresholdConfig = {}
): UseAdaptiveThresholdReturn {
  const mergedConfig = useRef<Required<AdaptiveThresholdConfig>>({
    ...DEFAULT_CONFIG,
    ...config,
  })

  // Initialize state from storage or defaults
  const [thresholdData, setThresholdData] = useState<ThresholdData>(() => {
    if (mergedConfig.current.persistThresholds) {
      const stored = loadThresholds()
      if (stored) {
        return stored
      }
    }
    return {
      silenceThresholdMs: mergedConfig.current.defaultSilenceMs,
      pauseSamples: [],
      falsePositives: 0,
      totalInteractions: 0,
      lastUpdated: Date.now(),
    }
  })

  // Persist changes
  useEffect(() => {
    if (mergedConfig.current.persistThresholds) {
      saveThresholds(thresholdData)
    }
  }, [thresholdData])

  /**
   * Record a pause duration sample.
   */
  const recordPause = useCallback((durationMs: number) => {
    if (durationMs < 100 || durationMs > 10000) {
      // Ignore unrealistic values
      return
    }

    setThresholdData((prev) => {
      const newSamples = [...prev.pauseSamples, durationMs]
      // Keep only recent samples
      if (newSamples.length > MAX_SAMPLES) {
        newSamples.shift()
      }

      const newThreshold = calculateOptimalThreshold(newSamples, mergedConfig.current)

      // Blend with current threshold using learning rate
      const blendedThreshold =
        prev.silenceThresholdMs * (1 - mergedConfig.current.learningRate) +
        newThreshold * mergedConfig.current.learningRate

      return {
        ...prev,
        pauseSamples: newSamples,
        silenceThresholdMs: Math.round(blendedThreshold),
        lastUpdated: Date.now(),
      }
    })
  }, [])

  /**
   * Record a false positive (user spoke during countdown).
   */
  const recordFalsePositive = useCallback(() => {
    setThresholdData((prev) => {
      // Increase threshold slightly when we get false positives
      const adjustedThreshold = Math.min(
        prev.silenceThresholdMs * 1.1,
        mergedConfig.current.maxSilenceMs
      )

      return {
        ...prev,
        falsePositives: prev.falsePositives + 1,
        totalInteractions: prev.totalInteractions + 1,
        silenceThresholdMs: Math.round(adjustedThreshold),
        lastUpdated: Date.now(),
      }
    })
  }, [])

  /**
   * Record a successful send (no false positive).
   */
  const recordSuccess = useCallback(() => {
    setThresholdData((prev) => ({
      ...prev,
      totalInteractions: prev.totalInteractions + 1,
      lastUpdated: Date.now(),
    }))
  }, [])

  /**
   * Reset learned thresholds.
   */
  const resetThresholds = useCallback(() => {
    const newData: ThresholdData = {
      silenceThresholdMs: mergedConfig.current.defaultSilenceMs,
      pauseSamples: [],
      falsePositives: 0,
      totalInteractions: 0,
      lastUpdated: Date.now(),
    }
    setThresholdData(newData)
    if (mergedConfig.current.persistThresholds) {
      saveThresholds(newData)
    }
  }, [])

  // Calculate false positive rate
  const falsePositiveRate =
    thresholdData.totalInteractions > 0
      ? thresholdData.falsePositives / thresholdData.totalInteractions
      : 0

  // Determine if thresholds are personalized
  const isPersonalized = thresholdData.pauseSamples.length >= 5

  return {
    silenceThresholdMs: thresholdData.silenceThresholdMs,
    countdownMs: mergedConfig.current.countdownMs,
    recordPause,
    recordFalsePositive,
    recordSuccess,
    falsePositiveRate,
    resetThresholds,
    isPersonalized,
  }
}
