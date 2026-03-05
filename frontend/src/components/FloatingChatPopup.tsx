'use client'

import { useEffect } from 'react'

interface FloatingChatPopupProps {
  isOpen: boolean
  onClose: () => void
  children: React.ReactNode
}

/**
 * Floating chat popup positioned in the bottom-right corner.
 * Provides a less intrusive chat experience compared to full-height drawers.
 */
export function FloatingChatPopup({ isOpen, onClose, children }: FloatingChatPopupProps) {
  // Close on Escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) onClose()
    }
    document.addEventListener('keydown', handleEscape)
    return () => document.removeEventListener('keydown', handleEscape)
  }, [isOpen, onClose])

  if (!isOpen) return null

  return (
    <>
      {/* Backdrop - subtle, click to close */}
      <div
        className="fixed inset-0 z-40 bg-black/20"
        onClick={onClose}
      />

      {/* Floating popup - bottom right */}
      <div className="fixed bottom-4 right-4 z-50 w-[380px] h-[500px] bg-background border border-border rounded-xl shadow-2xl overflow-hidden flex flex-col animate-in slide-in-from-bottom-4 duration-200">
        {children}
      </div>
    </>
  )
}
