'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'

/**
 * Application header with navigation.
 *
 * Displays the Nell logo with warm gradient icon and Create/History nav tabs.
 */
export function Header() {
  const pathname = usePathname()

  const isCreate = pathname === '/'
  const isHistory = pathname === '/history'

  return (
    <header className="border-b border-border bg-card/50 backdrop-blur-lg sticky top-0 z-50">
      <div className="container mx-auto px-4 h-14 flex items-center justify-between">
        {/* Logo */}
        <div className="flex items-center gap-3">
          <Link href="/" className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-accent flex items-center justify-center">
              <svg
                className="w-5 h-5 text-white"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"
                />
              </svg>
            </div>
            <span className="text-xl font-bold">Nell</span>
          </Link>
          <span className="badge-primary hidden sm:inline-flex">AI Podcast</span>
        </div>

        {/* Navigation */}
        <nav className="flex items-center gap-1">
          <Link
            href="/"
            className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
              isCreate
                ? 'bg-primary/10 text-primary'
                : 'text-muted-foreground hover:text-foreground hover:bg-muted/50'
            }`}
          >
            Create
          </Link>
          <Link
            href="/history"
            className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
              isHistory
                ? 'bg-primary/10 text-primary'
                : 'text-muted-foreground hover:text-foreground hover:bg-muted/50'
            }`}
          >
            History
          </Link>
        </nav>
      </div>
    </header>
  )
}
