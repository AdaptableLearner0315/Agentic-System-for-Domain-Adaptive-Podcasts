import type { Metadata } from 'next'
import { DM_Sans } from 'next/font/google'
import './globals.css'

const dmSans = DM_Sans({ subsets: ['latin'] })

/**
 * Application metadata for SEO and browser display.
 */
export const metadata: Metadata = {
  title: 'Nell - AI Podcast Generator',
  description: 'Transform your content into engaging video podcasts with AI',
  keywords: ['podcast', 'AI', 'video', 'content generation', 'TTS'],
}

/**
 * Root layout component.
 *
 * Provides the base HTML structure and applies global styles.
 * All pages are rendered as children of this layout.
 *
 * @param children - Child components to render
 */
export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="dark">
      <body className={dmSans.className}>
        <div className="min-h-screen bg-ambient">
          {children}
        </div>
      </body>
    </html>
  )
}
