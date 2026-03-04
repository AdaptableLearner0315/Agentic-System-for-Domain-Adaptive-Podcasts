/**
 * Tests for the OutputPlayer component.
 *
 * Verifies video display, download buttons, tab switching,
 * and reset functionality.
 */

import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import '@testing-library/jest-dom'
import { OutputPlayer } from '../OutputPlayer'
import type { ResultResponse } from '@/types'

// Mock window.open
const mockWindowOpen = jest.fn()
Object.defineProperty(window, 'open', { value: mockWindowOpen, writable: true })

// Mock environment variable
const originalEnv = process.env

beforeEach(() => {
  jest.clearAllMocks()
  process.env = { ...originalEnv, NEXT_PUBLIC_API_URL: 'http://localhost:8000' }
})

afterEach(() => {
  process.env = originalEnv
})

const mockResult: ResultResponse = {
  job_id: 'test-job-123',
  success: true,
  output_path: '/path/to/video.mp4',
  video_url: '/api/outputs/stream/test-job-123',
  audio_url: '/api/outputs/download/test-job-123?file_type=audio',
  duration_seconds: 120,
  script: {
    title: 'Test Podcast',
    hook: { text: 'This is the hook text' },
  },
  tts_assets: [{ id: 'tts_0', filename: 'tts.wav', path: '/path/tts.wav', type: 'tts' }],
  bgm_assets: [{ id: 'bgm_0', filename: 'bgm.wav', path: '/path/bgm.wav', type: 'bgm' }],
  image_assets: [{ id: 'img_0', filename: 'img.png', path: '/path/img.png', type: 'image' }],
}

describe('OutputPlayer', () => {
  const mockOnReset = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('Video Tab', () => {
    it('renders success header with duration', () => {
      render(<OutputPlayer result={mockResult} onReset={mockOnReset} />)
      expect(screen.getByText('Your Podcast is Ready!')).toBeInTheDocument()
      expect(screen.getByText('Duration: 2:00')).toBeInTheDocument()
    })

    it('renders video element when video_url exists', () => {
      render(<OutputPlayer result={mockResult} onReset={mockOnReset} />)
      const video = document.querySelector('video')
      expect(video).toBeInTheDocument()
      expect(video?.src).toContain('/api/outputs/stream/test-job-123')
    })

    it('shows unmute button initially', () => {
      render(<OutputPlayer result={mockResult} onReset={mockOnReset} />)
      expect(screen.getByText('Unmute')).toBeInTheDocument()
    })

    it('hides unmute button after clicking', () => {
      render(<OutputPlayer result={mockResult} onReset={mockOnReset} />)
      const unmuteButton = screen.getByText('Unmute')
      fireEvent.click(unmuteButton)
      expect(screen.queryByText('Unmute')).not.toBeInTheDocument()
    })

    it('shows fallback when no video_url', () => {
      const resultWithoutVideo = { ...mockResult, video_url: undefined }
      render(<OutputPlayer result={resultWithoutVideo} onReset={mockOnReset} />)
      expect(screen.getByText('Video preview not available')).toBeInTheDocument()
    })
  })

  describe('Download Buttons', () => {
    it('opens correct URL when Download Video clicked', () => {
      render(<OutputPlayer result={mockResult} onReset={mockOnReset} />)
      fireEvent.click(screen.getByText('Download Video'))
      expect(mockWindowOpen).toHaveBeenCalledWith(
        'http://localhost:8000/api/outputs/download/test-job-123?file_type=video',
        '_blank'
      )
    })

    it('opens correct URL when Audio Only clicked', () => {
      render(<OutputPlayer result={mockResult} onReset={mockOnReset} />)
      fireEvent.click(screen.getByText('Audio Only'))
      expect(mockWindowOpen).toHaveBeenCalledWith(
        'http://localhost:8000/api/outputs/download/test-job-123?file_type=audio',
        '_blank'
      )
    })

    it('opens correct URL when Script clicked', () => {
      render(<OutputPlayer result={mockResult} onReset={mockOnReset} />)
      fireEvent.click(screen.getByText('Script'))
      expect(mockWindowOpen).toHaveBeenCalledWith(
        'http://localhost:8000/api/outputs/download/test-job-123?file_type=script',
        '_blank'
      )
    })
  })

  describe('Details Tab', () => {
    it('shows script preview when Details tab clicked', () => {
      render(<OutputPlayer result={mockResult} onReset={mockOnReset} />)
      fireEvent.click(screen.getByText('Details'))
      expect(screen.getByText('Test Podcast')).toBeInTheDocument()
      expect(screen.getByText('This is the hook text')).toBeInTheDocument()
    })

    it('shows asset counts', () => {
      render(<OutputPlayer result={mockResult} onReset={mockOnReset} />)
      fireEvent.click(screen.getByText('Details'))
      expect(screen.getByText('Voice Clips')).toBeInTheDocument()
      expect(screen.getByText('Music Tracks')).toBeInTheDocument()
      expect(screen.getByText('Images')).toBeInTheDocument()
    })

    it('handles string hook format', () => {
      const resultWithStringHook = {
        ...mockResult,
        script: { title: 'String Hook Test', hook: 'This is a string hook' },
      }
      render(<OutputPlayer result={resultWithStringHook} onReset={mockOnReset} />)
      fireEvent.click(screen.getByText('Details'))
      expect(screen.getByText('This is a string hook')).toBeInTheDocument()
    })

    it('shows review history for Pro mode', () => {
      const resultWithReview = {
        ...mockResult,
        review_history: [{ score: 8, round: 1 }],
      }
      render(<OutputPlayer result={resultWithReview} onReset={mockOnReset} />)
      fireEvent.click(screen.getByText('Details'))
      expect(screen.getByText('Director Reviews')).toBeInTheDocument()
      expect(screen.getByText(/Round 1: Score 8/)).toBeInTheDocument()
    })
  })

  describe('Reset Button', () => {
    it('calls onReset when Create Another Podcast clicked', () => {
      render(<OutputPlayer result={mockResult} onReset={mockOnReset} />)
      fireEvent.click(screen.getByText('Create Another Podcast'))
      expect(mockOnReset).toHaveBeenCalledTimes(1)
    })
  })

  describe('Duration Formatting', () => {
    it('formats duration correctly for minutes and seconds', () => {
      render(<OutputPlayer result={mockResult} onReset={mockOnReset} />)
      expect(screen.getByText('Duration: 2:00')).toBeInTheDocument()
    })

    it('shows "Generation complete" when no duration', () => {
      const resultWithoutDuration = { ...mockResult, duration_seconds: undefined }
      render(<OutputPlayer result={resultWithoutDuration} onReset={mockOnReset} />)
      expect(screen.getByText('Generation complete')).toBeInTheDocument()
    })

    it('pads single-digit seconds with zero', () => {
      const resultWithOddDuration = { ...mockResult, duration_seconds: 65 }
      render(<OutputPlayer result={resultWithOddDuration} onReset={mockOnReset} />)
      expect(screen.getByText('Duration: 1:05')).toBeInTheDocument()
    })
  })
})
