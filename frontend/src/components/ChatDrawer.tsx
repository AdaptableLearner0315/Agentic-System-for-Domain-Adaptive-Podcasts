'use client'

import { useEffect } from 'react'

interface ChatDrawerProps {
  isOpen: boolean
  onClose: () => void
  children: React.ReactNode
}

/**
 * Right-side sliding drawer with backdrop overlay.
 *
 * Always mounted in DOM for smooth CSS transitions.
 * Locks body scroll when open.
 *
 * @param isOpen - Whether the drawer is visible
 * @param onClose - Callback when backdrop is clicked
 * @param children - Drawer content (ChatPanel)
 */
export function ChatDrawer({ isOpen, onClose, children }: ChatDrawerProps) {
  // Lock body scroll when drawer is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = ''
    }
    return () => {
      document.body.style.overflow = ''
    }
  }, [isOpen])

  return (
    <>
      {/* Backdrop */}
      <div
        className={`fixed inset-0 z-50 bg-black/50 transition-opacity duration-300 ${
          isOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'
        }`}
        onClick={onClose}
      />

      {/* Drawer panel - slides from right */}
      <div
        className={`fixed top-0 right-0 z-50 h-full w-full sm:w-[400px] bg-background border-l border-border shadow-xl transition-transform duration-300 ${
          isOpen ? 'translate-x-0' : 'translate-x-full'
        }`}
      >
        {children}
      </div>
    </>
  )
}
