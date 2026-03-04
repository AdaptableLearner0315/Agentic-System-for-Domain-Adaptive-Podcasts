/**
 * Tests for the Header component.
 *
 * Verifies logo rendering, navigation links, and active state highlighting.
 */

import React from 'react'
import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'
import { Header } from '../Header'

// Mock next/navigation
jest.mock('next/navigation', () => ({
  usePathname: jest.fn(),
}))

import { usePathname } from 'next/navigation'

describe('Header', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders logo and navigation', () => {
    (usePathname as jest.Mock).mockReturnValue('/')
    render(<Header />)

    expect(screen.getByText('Nell')).toBeInTheDocument()
    expect(screen.getByText('Create')).toBeInTheDocument()
    expect(screen.getByText('History')).toBeInTheDocument()
  })

  it('renders AI Podcast badge', () => {
    (usePathname as jest.Mock).mockReturnValue('/')
    render(<Header />)

    expect(screen.getByText('AI Podcast')).toBeInTheDocument()
  })

  it('highlights Create when on home page', () => {
    (usePathname as jest.Mock).mockReturnValue('/')
    render(<Header />)

    const createLink = screen.getByText('Create')
    expect(createLink.className).toContain('bg-primary/10')
    expect(createLink.className).toContain('text-primary')
  })

  it('does not highlight History when on home page', () => {
    (usePathname as jest.Mock).mockReturnValue('/')
    render(<Header />)

    const historyLink = screen.getByText('History')
    expect(historyLink.className).toContain('text-muted-foreground')
    expect(historyLink.className).not.toContain('bg-primary/10')
  })

  it('highlights History when on history page', () => {
    (usePathname as jest.Mock).mockReturnValue('/history')
    render(<Header />)

    const historyLink = screen.getByText('History')
    expect(historyLink.className).toContain('bg-primary/10')
    expect(historyLink.className).toContain('text-primary')
  })

  it('does not highlight Create when on history page', () => {
    (usePathname as jest.Mock).mockReturnValue('/history')
    render(<Header />)

    const createLink = screen.getByText('Create')
    expect(createLink.className).toContain('text-muted-foreground')
    expect(createLink.className).not.toContain('bg-primary/10')
  })

  it('Create link points to home', () => {
    (usePathname as jest.Mock).mockReturnValue('/')
    render(<Header />)

    const createLink = screen.getByText('Create').closest('a')
    expect(createLink).toHaveAttribute('href', '/')
  })

  it('History link points to /history', () => {
    (usePathname as jest.Mock).mockReturnValue('/')
    render(<Header />)

    const historyLink = screen.getByText('History').closest('a')
    expect(historyLink).toHaveAttribute('href', '/history')
  })

  it('logo links to home page', () => {
    (usePathname as jest.Mock).mockReturnValue('/')
    render(<Header />)

    const logoLink = screen.getByText('Nell').closest('a')
    expect(logoLink).toHaveAttribute('href', '/')
  })

  it('renders microphone icon in logo', () => {
    (usePathname as jest.Mock).mockReturnValue('/')
    render(<Header />)

    // Logo container should have gradient background
    const logoContainer = document.querySelector('.bg-gradient-to-br')
    expect(logoContainer).toBeInTheDocument()

    // Should contain an SVG
    const svg = logoContainer?.querySelector('svg')
    expect(svg).toBeInTheDocument()
  })
})
