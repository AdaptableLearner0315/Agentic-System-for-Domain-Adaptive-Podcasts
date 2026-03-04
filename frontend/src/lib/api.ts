/**
 * API client for the Nell Podcast Backend.
 *
 * Provides typed methods for all API endpoints with error handling.
 */

import type {
  GenerationRequest,
  JobResponse,
  JobListResponse,
  ProgressResponse,
  ResultResponse,
  FileResponse,
  FileListResponse,
  ConfigResponse,
  HealthResponse,
  ErrorResponse,
  URLExtractionRequest,
  SessionResponse,
  MessageRequest,
  MessageResponse,
  HistoryResponse,
  TranscriptionResponse,
} from '@/types'

// API base URL from environment
export const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

/**
 * Custom error class for API errors.
 */
export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public details?: Record<string, unknown>
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

/**
 * Make an API request with error handling.
 *
 * @param endpoint - API endpoint path
 * @param options - Fetch options
 * @returns Parsed response data
 * @throws ApiError on request failure
 */
async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_URL}${endpoint}`

  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  })

  if (!response.ok) {
    let errorData: ErrorResponse | null = null
    try {
      errorData = await response.json()
    } catch {
      // Response may not be JSON
    }

    throw new ApiError(
      errorData?.message || `Request failed: ${response.statusText}`,
      response.status,
      errorData?.details
    )
  }

  return response.json()
}

// =============================================================================
// Pipeline Endpoints
// =============================================================================

/**
 * Start a new podcast generation job.
 *
 * @param data - Generation request data
 * @returns Created job response
 */
export async function startGeneration(data: GenerationRequest): Promise<JobResponse> {
  return request<JobResponse>('/api/pipelines/generate', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

/**
 * Get the current status of a job.
 *
 * @param jobId - Job identifier
 * @returns Progress response
 */
export async function getJobStatus(jobId: string): Promise<ProgressResponse> {
  return request<ProgressResponse>(`/api/pipelines/${jobId}/status`)
}

/**
 * Get the result of a completed job.
 *
 * @param jobId - Job identifier
 * @returns Result response
 */
export async function getJobResult(jobId: string): Promise<ResultResponse> {
  return request<ResultResponse>(`/api/pipelines/${jobId}/result`)
}

/**
 * Get full job details.
 *
 * @param jobId - Job identifier
 * @returns Job response
 */
export async function getJob(jobId: string): Promise<JobResponse> {
  return request<JobResponse>(`/api/pipelines/${jobId}`)
}

/**
 * Cancel a running job.
 *
 * @param jobId - Job identifier
 * @returns Updated job response
 */
export async function cancelJob(jobId: string): Promise<JobResponse> {
  return request<JobResponse>(`/api/pipelines/${jobId}/cancel`, {
    method: 'POST',
  })
}

/**
 * Delete a job from history.
 *
 * @param jobId - Job identifier
 */
export async function deleteJob(jobId: string): Promise<void> {
  await request<{ message: string; id: string }>(`/api/pipelines/${jobId}`, {
    method: 'DELETE',
  })
}

/**
 * List all jobs with pagination.
 *
 * @param page - Page number
 * @param pageSize - Jobs per page
 * @param status - Optional status filter
 * @returns Job list response
 */
export async function listJobs(
  page: number = 1,
  pageSize: number = 20,
  status?: string
): Promise<JobListResponse> {
  const params = new URLSearchParams({
    page: page.toString(),
    page_size: pageSize.toString(),
  })
  if (status) {
    params.append('status', status)
  }
  return request<JobListResponse>(`/api/pipelines/?${params}`)
}

// =============================================================================
// File Endpoints
// =============================================================================

/**
 * Upload a file for content extraction.
 *
 * @param file - File to upload
 * @param description - Optional description
 * @returns File response
 */
export async function uploadFile(
  file: File,
  description?: string
): Promise<FileResponse> {
  const formData = new FormData()
  formData.append('file', file)
  if (description) {
    formData.append('description', description)
  }

  const response = await fetch(`${API_URL}/api/files/upload`, {
    method: 'POST',
    body: formData,
  })

  if (!response.ok) {
    let errorData: ErrorResponse | null = null
    try {
      errorData = await response.json()
    } catch {
      // Response may not be JSON
    }
    throw new ApiError(
      errorData?.message || 'Upload failed',
      response.status,
      errorData?.details
    )
  }

  return response.json()
}

/**
 * Extract content from a URL.
 *
 * @param data - URL extraction request
 * @returns File response
 */
export async function extractFromUrl(
  data: URLExtractionRequest
): Promise<FileResponse> {
  return request<FileResponse>('/api/files/upload-url', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

/**
 * Get file information.
 *
 * @param fileId - File identifier
 * @returns File response
 */
export async function getFile(fileId: string): Promise<FileResponse> {
  return request<FileResponse>(`/api/files/${fileId}`)
}

/**
 * Delete an uploaded file.
 *
 * @param fileId - File identifier
 */
export async function deleteFile(fileId: string): Promise<void> {
  await request<{ message: string }>(`/api/files/${fileId}`, {
    method: 'DELETE',
  })
}

/**
 * List all uploaded files.
 *
 * @returns File list response
 */
export async function listFiles(): Promise<FileListResponse> {
  return request<FileListResponse>('/api/files/')
}

// =============================================================================
// Configuration Endpoints
// =============================================================================

/**
 * Get available modes and configuration.
 *
 * @returns Config response
 */
export async function getConfig(): Promise<ConfigResponse> {
  return request<ConfigResponse>('/api/config/modes')
}

/**
 * Get available voice presets.
 *
 * @returns Voice configuration
 */
export async function getVoices(): Promise<Record<string, unknown>> {
  return request<Record<string, unknown>>('/api/config/voices')
}

/**
 * Get supported emotions.
 *
 * @returns Emotion configuration
 */
export async function getEmotions(): Promise<Record<string, unknown>> {
  return request<Record<string, unknown>>('/api/config/emotions')
}

/**
 * Get an AI-suggested podcast topic.
 *
 * @returns Object with a suggested topic string
 */
export async function suggestTopic(): Promise<{ topic: string }> {
  return request<{ topic: string }>('/api/config/suggest-topic')
}

// =============================================================================
// Health Endpoint
// =============================================================================

/**
 * Check API health status.
 *
 * @returns Health response
 */
export async function healthCheck(): Promise<HealthResponse> {
  return request<HealthResponse>('/health')
}

// =============================================================================
// Output Endpoints
// =============================================================================

/**
 * Get download URL for a job's output.
 *
 * @param jobId - Job identifier
 * @param type - File type (video, audio, script)
 * @returns Download URL
 */
export function getDownloadUrl(
  jobId: string,
  type: 'video' | 'audio' | 'script' = 'video'
): string {
  return `${API_URL}/api/outputs/download/${jobId}?file_type=${type}`
}

/**
 * Get streaming URL for a job's video.
 *
 * @param jobId - Job identifier
 * @returns Stream URL
 */
export function getStreamUrl(jobId: string): string {
  return `${API_URL}/api/outputs/stream/${jobId}`
}

// =============================================================================
// Interactive Chat Endpoints
// =============================================================================

/**
 * Start an interactive conversation session.
 *
 * @param jobId - Podcast job ID
 * @returns Session response with session ID and welcome message
 */
export async function startInteractiveSession(jobId: string): Promise<SessionResponse> {
  return request<SessionResponse>(`/api/interactive/${jobId}/session`, {
    method: 'POST',
  })
}

/**
 * Send a text message in an interactive session.
 *
 * @param jobId - Podcast job ID
 * @param data - Message request data
 * @returns Message response with user and assistant messages
 */
export async function sendInteractiveMessage(
  jobId: string,
  data: MessageRequest
): Promise<MessageResponse> {
  return request<MessageResponse>(`/api/interactive/${jobId}/message`, {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

/**
 * Send a voice message in an interactive session.
 *
 * @param jobId - Podcast job ID
 * @param audioBlob - Audio blob to upload
 * @param generateAudio - Whether to generate TTS response
 * @returns Transcription response
 */
export async function sendVoiceMessage(
  jobId: string,
  audioBlob: Blob,
  generateAudio: boolean = true
): Promise<TranscriptionResponse> {
  const formData = new FormData()
  formData.append('audio', audioBlob, 'recording.webm')

  const params = new URLSearchParams({ generate_audio: generateAudio.toString() })

  const response = await fetch(
    `${API_URL}/api/interactive/${jobId}/voice?${params}`,
    {
      method: 'POST',
      body: formData,
    }
  )

  if (!response.ok) {
    let errorData: ErrorResponse | null = null
    try {
      errorData = await response.json()
    } catch {
      // Response may not be JSON
    }
    throw new ApiError(
      errorData?.message || 'Voice upload failed',
      response.status,
      errorData?.details
    )
  }

  return response.json()
}

/**
 * Get conversation history for an interactive session.
 *
 * @param jobId - Podcast job ID
 * @returns History response with all messages
 */
export async function getInteractiveHistory(jobId: string): Promise<HistoryResponse> {
  return request<HistoryResponse>(`/api/interactive/${jobId}/history`)
}

/**
 * End an interactive session.
 *
 * @param jobId - Podcast job ID
 */
export async function endInteractiveSession(jobId: string): Promise<void> {
  await request<{ message: string; session_id: string }>(
    `/api/interactive/${jobId}/session`,
    { method: 'DELETE' }
  )
}

/**
 * Get session info for a job.
 *
 * @param jobId - Podcast job ID
 * @returns Session info or null if no active session
 */
export async function getInteractiveSessionInfo(
  jobId: string
): Promise<{ session_id: string; is_active: boolean } | null> {
  try {
    return await request<{ session_id: string; is_active: boolean }>(
      `/api/interactive/${jobId}/session`
    )
  } catch (e) {
    if (e instanceof ApiError && e.status === 404) {
      return null
    }
    throw e
  }
}
