/**
 * Tests for the ProgressTracker component.
 *
 * Verifies the client-side elapsed timer ticks independently
 * and stops on terminal phases (complete/error).
 */

import React from 'react'
import { render, screen, act } from '@testing-library/react'
import '@testing-library/jest-dom'
import { ProgressTracker } from '../ProgressTracker'
import { ProgressResponse } from '@/types'

// Mock timers for deterministic testing
beforeEach(() => {
  jest.useFakeTimers()
})

afterEach(() => {
  jest.useRealTimers()
})

function makeProgress(overrides: Partial<ProgressResponse> = {}): ProgressResponse {
  return {
    job_id: 'test-123',
    phase: 'scripting',
    message: 'Enhancing script...',
    progress_percent: 25,
    current_step: 1,
    total_steps: 4,
    elapsed_seconds: 5,
    ...overrides,
  }
}

describe('ProgressTracker elapsed timer', () => {
  it('ticks independently after receiving server elapsed', () => {
    const progress = makeProgress({ elapsed_seconds: 5 })
    render(<ProgressTracker progress={progress} />)

    // Should initially show ~0:05
    expect(screen.getByText(/Elapsed:/)).toHaveTextContent('0:05')

    // Advance 3 seconds
    act(() => {
      jest.advanceTimersByTime(3000)
    })

    // Should now show ~0:08
    expect(screen.getByText(/Elapsed:/)).toHaveTextContent('0:08')
  })

  it('stops ticking when phase is complete', () => {
    const { rerender } = render(
      <ProgressTracker progress={makeProgress({ elapsed_seconds: 10 })} />
    )

    // Advance a bit to show timer is working
    act(() => {
      jest.advanceTimersByTime(2000)
    })
    expect(screen.getByText(/Elapsed:/)).toHaveTextContent('0:12')

    // Switch to complete phase
    rerender(
      <ProgressTracker
        progress={makeProgress({ phase: 'complete', elapsed_seconds: 12 })}
      />
    )

    // Advance more time - timer should NOT increase
    act(() => {
      jest.advanceTimersByTime(5000)
    })
    expect(screen.getByText(/Elapsed:/)).toHaveTextContent('0:12')
  })

  it('stops ticking when phase is error', () => {
    const { rerender } = render(
      <ProgressTracker progress={makeProgress({ elapsed_seconds: 8 })} />
    )

    // Switch to error phase
    rerender(
      <ProgressTracker
        progress={makeProgress({ phase: 'error', elapsed_seconds: 8 })}
      />
    )

    // Advance time - timer should NOT increase
    act(() => {
      jest.advanceTimersByTime(5000)
    })
    expect(screen.getByText(/Elapsed:/)).toHaveTextContent('0:08')
  })

  it('starts from 0 when no server elapsed provided', () => {
    render(<ProgressTracker progress={makeProgress({ elapsed_seconds: 0 })} />)

    expect(screen.getByText(/Elapsed:/)).toHaveTextContent('0:00')

    // Timer should still tick from 0
    act(() => {
      jest.advanceTimersByTime(3000)
    })
    expect(screen.getByText(/Elapsed:/)).toHaveTextContent('0:03')
  })
})
