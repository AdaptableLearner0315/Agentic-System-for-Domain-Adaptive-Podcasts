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
  UserMemoryPreferences,
  AdaptiveThresholdData,
  JobLogs,
  // Series types
  CreateSeriesRequest,
  ApproveOutlineRequest,
  GenerateEpisodeRequest,
  Series,
  Episode,
  SeriesListResponse,
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
      errorData?.detail || errorData?.message || `Request failed: ${response.statusText}`,
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

/**
 * Get execution logs for a job.
 *
 * @param jobId - Job identifier
 * @returns Job logs response
 */
export async function getJobLogs(jobId: string): Promise<JobLogs> {
  return request<JobLogs>(`/api/pipelines/${jobId}/logs`)
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
      errorData?.detail || errorData?.message || 'Upload failed',
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
      errorData?.detail || errorData?.message || 'Voice upload failed',
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

// =============================================================================
// User Memory Endpoints
// =============================================================================

/**
 * Memory consent response from the API.
 */
interface ConsentResponse {
  user_id: string
  granted: boolean
  granted_at: string | null
  scope: string[]
}

/**
 * User profile response from the API.
 */
interface ProfileResponse {
  user_id: string
  display_name: string | null
  communication_style: {
    verbosity: 'concise' | 'balanced' | 'detailed'
    tone: 'casual' | 'professional' | 'friendly'
    use_analogies: boolean
    technical_depth: 'beginner' | 'intermediate' | 'expert'
  }
  interests: string[]
  expertise_areas: string[]
  created_at: string
  updated_at: string
}

/**
 * Thresholds response from the API.
 */
interface ThresholdsResponse {
  user_id: string
  silence_threshold_ms: number
  false_positive_rate: number
  total_interactions: number
  is_personalized: boolean
}

/**
 * Get memory consent status for a user.
 *
 * @param userId - Optional user ID
 * @returns Consent response
 */
export async function getMemoryConsent(userId?: string): Promise<ConsentResponse> {
  const params = userId ? `?user_id=${userId}` : ''
  return request<ConsentResponse>(`/api/user/consent${params}`)
}

/**
 * Update memory consent for a user.
 *
 * @param granted - Whether consent is granted
 * @param scope - Types of memory allowed
 * @param userId - Optional user ID
 * @returns Updated consent response
 */
export async function updateMemoryConsent(
  granted: boolean,
  scope?: string[],
  userId?: string
): Promise<ConsentResponse> {
  const params = userId ? `?user_id=${userId}` : ''
  return request<ConsentResponse>(`/api/user/consent${params}`, {
    method: 'POST',
    body: JSON.stringify({ granted, scope }),
  })
}

/**
 * Get user profile.
 *
 * @param userId - Optional user ID
 * @returns Profile response
 */
export async function getUserProfile(userId?: string): Promise<ProfileResponse> {
  const params = userId ? `?user_id=${userId}` : ''
  return request<ProfileResponse>(`/api/user/profile${params}`)
}

/**
 * Update user profile.
 *
 * @param updates - Profile fields to update
 * @param userId - Optional user ID
 * @returns Updated profile response
 */
export async function updateUserProfile(
  updates: Partial<{
    display_name: string
    communication_style: ProfileResponse['communication_style']
    interests: string[]
    expertise_areas: string[]
  }>,
  userId?: string
): Promise<ProfileResponse> {
  const params = userId ? `?user_id=${userId}` : ''
  return request<ProfileResponse>(`/api/user/profile${params}`, {
    method: 'PATCH',
    body: JSON.stringify(updates),
  })
}

/**
 * Get adaptive voice thresholds.
 *
 * @param userId - Optional user ID
 * @returns Thresholds response
 */
export async function getVoiceThresholds(userId?: string): Promise<ThresholdsResponse> {
  const params = userId ? `?user_id=${userId}` : ''
  return request<ThresholdsResponse>(`/api/user/thresholds${params}`)
}

/**
 * Update adaptive voice thresholds.
 *
 * @param updates - Threshold updates
 * @param userId - Optional user ID
 * @returns Updated thresholds response
 */
export async function updateVoiceThresholds(
  updates: {
    silence_threshold_ms?: number
    pause_sample?: number
    false_positive?: boolean
  },
  userId?: string
): Promise<ThresholdsResponse> {
  const params = userId ? `?user_id=${userId}` : ''
  return request<ThresholdsResponse>(`/api/user/thresholds${params}`, {
    method: 'POST',
    body: JSON.stringify(updates),
  })
}

/**
 * Clear all user memory.
 *
 * @param userId - Optional user ID
 */
export async function clearUserMemory(userId?: string): Promise<void> {
  const params = userId ? `?user_id=${userId}` : ''
  await request<{ message: string }>(`/api/user/memory${params}`, {
    method: 'DELETE',
  })
}

// =============================================================================
// Series Endpoints
// =============================================================================

/**
 * Create a new podcast series.
 *
 * The system analyzes your prompt to detect genre, era, and style,
 * then generates a complete series outline with episode summaries.
 *
 * @param data - Series creation request
 * @returns Created series in 'draft' status
 */
export async function createSeries(data: CreateSeriesRequest): Promise<Series> {
  return request<Series>('/api/series', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

/**
 * Get series details by ID.
 *
 * @param seriesId - Series identifier
 * @returns Full series information
 */
export async function getSeries(seriesId: string): Promise<Series> {
  return request<Series>(`/api/series/${seriesId}`)
}

/**
 * Approve or modify a series outline.
 *
 * On approval, series audio assets are generated and status changes to 'in_progress'.
 *
 * @param seriesId - Series identifier
 * @param data - Approval request with optional modifications
 * @returns Updated series
 */
export async function approveSeriesOutline(
  seriesId: string,
  data: ApproveOutlineRequest
): Promise<Series> {
  return request<Series>(`/api/series/${seriesId}/approve`, {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

/**
 * Generate the next episode in a series.
 *
 * @param seriesId - Series identifier
 * @param data - Optional episode generation request
 * @returns Generation status with job tracking info
 */
export async function generateSeriesEpisode(
  seriesId: string,
  data?: GenerateEpisodeRequest
): Promise<{
  job_id: string
  series_id: string
  episode_number: number
  episode_id: string
  status: string
  previously_on?: string
  guidance?: string
  cliffhanger_type?: string
  message: string
}> {
  return request(`/api/series/${seriesId}/generate`, {
    method: 'POST',
    body: JSON.stringify(data || {}),
  })
}

/**
 * Get details of a specific episode.
 *
 * @param seriesId - Series identifier
 * @param episodeNumber - Episode number
 * @returns Episode details
 */
export async function getSeriesEpisode(
  seriesId: string,
  episodeNumber: number
): Promise<Episode> {
  return request<Episode>(`/api/series/${seriesId}/episodes/${episodeNumber}`)
}

/**
 * Delete/cancel a series.
 *
 * Episodes already generated are preserved.
 *
 * @param seriesId - Series identifier
 */
export async function deleteSeries(seriesId: string): Promise<void> {
  await request(`/api/series/${seriesId}`, {
    method: 'DELETE',
  })
}

/**
 * List all series with pagination.
 *
 * @param page - Page number
 * @param pageSize - Items per page
 * @param status - Optional status filter
 * @returns Series list response
 */
export async function listSeries(
  page: number = 1,
  pageSize: number = 20,
  status?: string
): Promise<SeriesListResponse> {
  const params = new URLSearchParams({
    page: page.toString(),
    page_size: pageSize.toString(),
  })
  if (status) {
    params.append('status', status)
  }
  return request<SeriesListResponse>(`/api/series?${params}`)
}
