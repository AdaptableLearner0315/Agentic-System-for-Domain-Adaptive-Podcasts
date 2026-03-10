'use client'

/**
 * Memory consent modal for first-time voice users.
 *
 * Asks users if they want Nell to remember their conversations
 * and preferences across sessions.
 */

import { useState, useCallback, useEffect } from 'react'
import { updateMemoryConsent, getMemoryConsent } from '@/lib/api'

interface MemoryConsentModalProps {
  /** Whether the modal is open */
  isOpen: boolean
  /** Callback when modal is closed */
  onClose: () => void
  /** Callback when consent is given */
  onConsent: (granted: boolean) => void
  /** User ID (optional) */
  userId?: string
}

/**
 * Storage key for tracking if consent has been asked.
 */
const CONSENT_ASKED_KEY = 'nell_consent_asked'

/**
 * Check if consent has already been asked.
 */
export function hasAskedConsent(): boolean {
  if (typeof window === 'undefined') return true
  return localStorage.getItem(CONSENT_ASKED_KEY) === 'true'
}

/**
 * Mark consent as having been asked.
 */
export function markConsentAsked(): void {
  if (typeof window === 'undefined') return
  localStorage.setItem(CONSENT_ASKED_KEY, 'true')
}

/**
 * Memory consent modal component.
 *
 * Shows a friendly prompt asking users if they want Nell to
 * remember their conversations for personalized responses.
 *
 * @example
 * ```tsx
 * <MemoryConsentModal
 *   isOpen={showConsent}
 *   onClose={() => setShowConsent(false)}
 *   onConsent={(granted) => handleConsent(granted)}
 * />
 * ```
 */
export function MemoryConsentModal({
  isOpen,
  onClose,
  onConsent,
  userId,
}: MemoryConsentModalProps) {
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  /**
   * Handle consent choice.
   */
  const handleChoice = useCallback(
    async (granted: boolean) => {
      setIsLoading(true)
      setError(null)

      try {
        await updateMemoryConsent(granted, undefined, userId)
        markConsentAsked()
        onConsent(granted)
        onClose()
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Failed to save preference')
        setIsLoading(false)
      }
    },
    [userId, onConsent, onClose]
  )

  /**
   * Handle closing without choice (treat as declined for now).
   */
  const handleClose = useCallback(() => {
    markConsentAsked()
    onConsent(false)
    onClose()
  }, [onConsent, onClose])

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={handleClose}
      />

      {/* Modal */}
      <div className="relative bg-background border border-border rounded-2xl shadow-xl max-w-md w-full overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        {/* Header with avatar */}
        <div className="bg-gradient-to-br from-primary/10 to-success/10 px-6 pt-6 pb-4 text-center">
          <div className="w-16 h-16 mx-auto mb-3 rounded-full bg-primary/20 flex items-center justify-center border-2 border-primary/30">
            <span className="text-3xl font-bold text-primary">N</span>
          </div>
          <h2 className="text-xl font-semibold text-foreground">
            Hi! I'm Nell
          </h2>
        </div>

        {/* Content */}
        <div className="px-6 py-4">
          <p className="text-sm text-muted-foreground mb-4 text-center">
            Would you like me to remember our conversations?
          </p>

          <p className="text-xs text-muted-foreground/80 mb-6 text-center">
            This helps me give you better, more personalized responses over time.
            I'll remember your preferences, topics you're interested in, and
            our past conversations.
          </p>

          {/* Benefits list */}
          <div className="space-y-2 mb-6">
            <BenefitItem
              icon="brain"
              text="Personalized responses based on your interests"
            />
            <BenefitItem
              icon="history"
              text="Reference past conversations naturally"
            />
            <BenefitItem
              icon="settings"
              text="Adapt to your communication style"
            />
          </div>

          {error && (
            <div className="text-xs text-destructive mb-4 text-center">
              {error}
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-3">
            <button
              className="flex-1 px-4 py-2.5 rounded-lg border border-border text-sm font-medium text-muted-foreground hover:bg-secondary transition-colors disabled:opacity-50"
              onClick={() => handleChoice(false)}
              disabled={isLoading}
            >
              No thanks
            </button>
            <button
              className="flex-1 px-4 py-2.5 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition-colors disabled:opacity-50"
              onClick={() => handleChoice(true)}
              disabled={isLoading}
            >
              {isLoading ? 'Saving...' : 'Yes, remember me'}
            </button>
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-3 bg-secondary/30 border-t border-border">
          <p className="text-[10px] text-muted-foreground/60 text-center">
            You can change this anytime in settings. Your data stays private.
          </p>
        </div>
      </div>
    </div>
  )
}

/**
 * Benefit list item component.
 */
function BenefitItem({ icon, text }: { icon: string; text: string }) {
  const renderIcon = () => {
    switch (icon) {
      case 'brain':
        return (
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
              d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
            />
          </svg>
        )
      case 'history':
        return (
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
              d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
        )
      case 'settings':
        return (
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
              d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
            />
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
            />
          </svg>
        )
      default:
        return null
    }
  }

  return (
    <div className="flex items-center gap-3 text-sm">
      <div className="w-8 h-8 rounded-lg bg-primary/10 text-primary flex items-center justify-center flex-shrink-0">
        {renderIcon()}
      </div>
      <span className="text-muted-foreground">{text}</span>
    </div>
  )
}

/**
 * Hook for managing memory consent state.
 */
export function useMemoryConsent(userId?: string) {
  const [showModal, setShowModal] = useState(false)
  const [hasConsent, setHasConsent] = useState<boolean | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  // Check consent status on mount
  useEffect(() => {
    const checkConsent = async () => {
      try {
        const response = await getMemoryConsent(userId)
        setHasConsent(response.granted)

        // Show modal if consent hasn't been asked yet
        if (!hasAskedConsent() && !response.granted) {
          setShowModal(true)
        }
      } catch {
        // If API fails, assume no consent
        setHasConsent(false)
      } finally {
        setIsLoading(false)
      }
    }

    checkConsent()
  }, [userId])

  const handleConsent = useCallback((granted: boolean) => {
    setHasConsent(granted)
    setShowModal(false)
  }, [])

  return {
    showModal,
    setShowModal,
    hasConsent,
    isLoading,
    handleConsent,
  }
}
