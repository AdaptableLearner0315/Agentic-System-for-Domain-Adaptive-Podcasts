/**
 * Tests for useGeneration hook WebSocket lifecycle.
 *
 * These tests verify that the WebSocket connection is properly managed
 * and doesn't disconnect prematurely when status changes.
 */

import { renderHook, act, waitFor } from '@testing-library/react'
import { useGeneration } from '../useGeneration'

// Mock the API module
jest.mock('@/lib/api', () => ({
  startGeneration: jest.fn(),
  cancelJob: jest.fn(),
  getJobResult: jest.fn(),
  getJob: jest.fn(),
  getJobStatus: jest.fn(),
}))

// Mock WebSocket connection
const mockDisconnect = jest.fn()
const mockWs = {
  disconnect: mockDisconnect,
}

let capturedCallbacks: {
  onProgress?: (data: unknown) => void
  onComplete?: (data: unknown) => void
  onError?: (msg: string) => void
  onStateChange?: (state: string) => void
} = {}

jest.mock('@/lib/websocket', () => ({
  createProgressConnection: jest.fn((jobId: string, callbacks: typeof capturedCallbacks) => {
    capturedCallbacks = callbacks
    return mockWs
  }),
}))

import { startGeneration, getJobResult, getJob } from '@/lib/api'
import { createProgressConnection } from '@/lib/websocket'

const mockStartGeneration = startGeneration as jest.MockedFunction<typeof startGeneration>
const mockGetJobResult = getJobResult as jest.MockedFunction<typeof getJobResult>
const mockGetJob = getJob as jest.MockedFunction<typeof getJob>
const mockCreateProgressConnection = createProgressConnection as jest.MockedFunction<typeof createProgressConnection>

describe('useGeneration', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    capturedCallbacks = {}
    localStorage.clear()
  })

  afterEach(() => {
    localStorage.clear()
  })

  describe('WebSocket lifecycle', () => {
    it('should connect WebSocket when generation starts', async () => {
      mockStartGeneration.mockResolvedValue({
        id: 'test-job-123',
        status: 'pending',
        mode: 'normal',
        created_at: new Date().toISOString(),
      })

      const { result } = renderHook(() => useGeneration())

      await act(async () => {
        await result.current.startGeneration({
          prompt: 'Test prompt',
          mode: 'normal',
        })
      })

      expect(mockCreateProgressConnection).toHaveBeenCalledWith(
        'test-job-123',
        expect.any(Object)
      )
    })

    it('should NOT disconnect WebSocket when status changes to running', async () => {
      mockStartGeneration.mockResolvedValue({
        id: 'test-job-456',
        status: 'pending',
        mode: 'normal',
        created_at: new Date().toISOString(),
      })

      const { result } = renderHook(() => useGeneration())

      await act(async () => {
        await result.current.startGeneration({
          prompt: 'Test prompt',
          mode: 'normal',
        })
      })

      // Simulate status changing to 'running' via progress update
      act(() => {
        capturedCallbacks.onProgress?.({
          phase: 'scripting',
          message: 'Generating script...',
          progress_percent: 20,
        })
      })

      expect(result.current.status).toBe('running')
      // WebSocket should NOT have been disconnected
      expect(mockDisconnect).not.toHaveBeenCalled()
    })

    it('should NOT disconnect WebSocket prematurely when onComplete fires', async () => {
      mockStartGeneration.mockResolvedValue({
        id: 'test-job-789',
        status: 'pending',
        mode: 'normal',
        created_at: new Date().toISOString(),
      })

      const mockResult = {
        job_id: 'test-job-789',
        success: true,
        video_url: '/outputs/test.mp4',
        duration_seconds: 120,
      }
      mockGetJobResult.mockResolvedValue(mockResult)

      const { result } = renderHook(() => useGeneration())

      await act(async () => {
        await result.current.startGeneration({
          prompt: 'Test prompt',
          mode: 'normal',
        })
      })

      // Clear the mock to track new calls
      mockDisconnect.mockClear()

      // Simulate completion
      await act(async () => {
        await capturedCallbacks.onComplete?.({
          success: true,
          video_url: '/outputs/test.mp4',
          duration_seconds: 120,
        })
      })

      // Status should be completed
      expect(result.current.status).toBe('completed')

      // Result should be set (this was the bug - result wasn't being set)
      await waitFor(() => {
        expect(result.current.result).toEqual(mockResult)
      })

      // WebSocket should NOT have been disconnected during onComplete
      // (cleanup only happens when jobId changes or component unmounts)
      expect(mockDisconnect).not.toHaveBeenCalled()
    })

    it('should set result even if getJobResult fails', async () => {
      mockStartGeneration.mockResolvedValue({
        id: 'test-job-fallback',
        status: 'pending',
        mode: 'normal',
        created_at: new Date().toISOString(),
      })

      mockGetJobResult.mockRejectedValue(new Error('Network error'))

      const { result } = renderHook(() => useGeneration())

      await act(async () => {
        await result.current.startGeneration({
          prompt: 'Test prompt',
          mode: 'normal',
        })
      })

      // Simulate completion
      await act(async () => {
        await capturedCallbacks.onComplete?.({
          success: true,
          video_url: '/outputs/fallback.mp4',
          output_path: '/path/to/output',
          duration_seconds: 90,
        })
      })

      // Result should still be set from the onComplete data
      await waitFor(() => {
        expect(result.current.result).toEqual({
          job_id: 'test-job-fallback',
          success: true,
          video_url: '/outputs/fallback.mp4',
          output_path: '/path/to/output',
          duration_seconds: 90,
        })
      })
    })

    it('should disconnect WebSocket on reset', async () => {
      mockStartGeneration.mockResolvedValue({
        id: 'test-job-reset',
        status: 'pending',
        mode: 'normal',
        created_at: new Date().toISOString(),
      })

      const { result } = renderHook(() => useGeneration())

      await act(async () => {
        await result.current.startGeneration({
          prompt: 'Test prompt',
          mode: 'normal',
        })
      })

      mockDisconnect.mockClear()

      act(() => {
        result.current.reset()
      })

      expect(mockDisconnect).toHaveBeenCalled()
      expect(result.current.jobId).toBeNull()
      expect(result.current.status).toBeNull()
    })
  })

  describe('localStorage recovery', () => {
    it('should recover running job from localStorage', async () => {
      localStorage.setItem('nell_active_job_id', 'recovered-job-123')

      mockGetJob.mockResolvedValue({
        id: 'recovered-job-123',
        status: 'running',
        mode: 'normal',
        created_at: new Date().toISOString(),
      })

      const { result } = renderHook(() => useGeneration())

      await waitFor(() => {
        expect(result.current.jobId).toBe('recovered-job-123')
        expect(result.current.status).toBe('running')
      })

      expect(mockCreateProgressConnection).toHaveBeenCalledWith(
        'recovered-job-123',
        expect.any(Object)
      )
    })

    it('should NOT connect WebSocket for completed job from localStorage', async () => {
      localStorage.setItem('nell_active_job_id', 'completed-job-456')

      const mockResult = {
        job_id: 'completed-job-456',
        success: true,
        video_url: '/outputs/completed.mp4',
        duration_seconds: 180,
      }

      mockGetJob.mockResolvedValue({
        id: 'completed-job-456',
        status: 'completed',
        mode: 'normal',
        created_at: new Date().toISOString(),
      })
      mockGetJobResult.mockResolvedValue(mockResult)

      const { result } = renderHook(() => useGeneration())

      await waitFor(() => {
        expect(result.current.status).toBe('completed')
        expect(result.current.result).toEqual(mockResult)
      })

      // Should NOT have created a WebSocket connection for completed job
      expect(mockCreateProgressConnection).not.toHaveBeenCalled()
    })

    it('should clear localStorage for non-existent job', async () => {
      localStorage.setItem('nell_active_job_id', 'stale-job-789')

      mockGetJob.mockRejectedValue(new Error('Job not found'))

      renderHook(() => useGeneration())

      await waitFor(() => {
        expect(localStorage.getItem('nell_active_job_id')).toBeNull()
      })
    })
  })

  describe('error handling', () => {
    it('should handle WebSocket error', async () => {
      mockStartGeneration.mockResolvedValue({
        id: 'test-job-error',
        status: 'pending',
        mode: 'normal',
        created_at: new Date().toISOString(),
      })

      const { result } = renderHook(() => useGeneration())

      await act(async () => {
        await result.current.startGeneration({
          prompt: 'Test prompt',
          mode: 'normal',
        })
      })

      act(() => {
        capturedCallbacks.onError?.('Generation failed: API error')
      })

      expect(result.current.status).toBe('failed')
      expect(result.current.error).toBe('Generation failed: API error')
    })

    it('should show reconnection message on connection error', async () => {
      mockStartGeneration.mockResolvedValue({
        id: 'test-job-reconnect',
        status: 'pending',
        mode: 'normal',
        created_at: new Date().toISOString(),
      })

      const { result } = renderHook(() => useGeneration())

      await act(async () => {
        await result.current.startGeneration({
          prompt: 'Test prompt',
          mode: 'normal',
        })
      })

      act(() => {
        capturedCallbacks.onStateChange?.('error')
      })

      expect(result.current.error).toBe('Connection lost. Attempting to reconnect...')

      act(() => {
        capturedCallbacks.onStateChange?.('connected')
      })

      expect(result.current.error).toBeNull()
    })
  })
})
