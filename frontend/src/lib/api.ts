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
} from '@/types'

// API base URL from environment
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

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
