/**
 * TypeScript type definitions for the Nell Podcast Frontend.
 *
 * These types mirror the backend API models for type safety.
 */

// =============================================================================
// Enums
// =============================================================================

/**
 * Status of a generation job.
 */
export type JobStatus =
  | 'pending'
  | 'running'
  | 'completed'
  | 'failed'
  | 'cancelled'

/**
 * Pipeline execution mode.
 */
export type PipelineMode = 'normal' | 'pro'

/**
 * Duration option value for the duration selector.
 * 'auto' means duration is extracted from prompt or uses default.
 */
export type DurationOption = 'auto' | 3 | 5 | 10 | 15 | 20

/**
 * Current phase of the generation process.
 */
export type GenerationPhase =
  | 'initializing'
  | 'analyzing'
  | 'scripting'
  | 'generating_tts'
  | 'generating_bgm'
  | 'generating_images'
  | 'generating_assets'
  | 'mixing_audio'
  | 'assembling_video'
  | 'complete'
  | 'error'

// =============================================================================
// Request Types
// =============================================================================

/**
 * Request to start a podcast generation job.
 */
export interface GenerationRequest {
  /** Topic or prompt for content generation */
  prompt?: string
  /** List of uploaded file IDs to use as input */
  file_ids?: string[]
  /** Additional instructions for generation style */
  guidance?: string
  /** Pipeline mode: 'normal' (fast) or 'pro' (quality) */
  mode: PipelineMode
  /** Target podcast duration in minutes (1-30). Auto-detected from prompt if not specified. */
  target_duration_minutes?: number
  /** Pro mode configuration overrides */
  config?: ProConfig
}

/**
 * Pro mode configuration options.
 */
export interface ProConfig {
  director_review?: boolean
  max_review_rounds?: number
  approval_threshold?: number
  voice_preset?: string
  apply_voice_styles?: boolean
  custom_pronunciations?: Record<string, string>
  music_genre?: string
  bgm_segments?: number
  daisy_chain?: boolean
  image_count?: number
  image_style?: string
  speaker_format?: string
  manual_speakers?: Record<string, string>
  emotion_voice_sync?: boolean
  emotion_image_alignment?: boolean
  emotion_validation?: boolean
}

/**
 * Request to extract content from a URL.
 */
export interface URLExtractionRequest {
  url: string
  description?: string
}

// =============================================================================
// Response Types
// =============================================================================

/**
 * Real-time progress update for a generation job.
 */
export interface ProgressResponse {
  job_id: string
  phase: GenerationPhase
  message: string
  progress_percent: number
  current_step: number
  total_steps: number
  eta_seconds?: number
  preview?: string
  elapsed_seconds: number
  details?: Record<string, unknown>
}

/**
 * Information about a generated asset.
 */
export interface AssetInfo {
  id: string
  filename: string
  path: string
  type: string
  duration_seconds?: number
  metadata?: Record<string, unknown>
}

/**
 * Final result of a completed generation job.
 */
export interface ResultResponse {
  job_id: string
  success: boolean
  output_path?: string
  video_url?: string
  audio_url?: string
  duration_seconds?: number
  script?: ScriptData
  tts_assets?: AssetInfo[]
  bgm_assets?: AssetInfo[]
  image_assets?: AssetInfo[]
  review_history?: ReviewEntry[]
  config_used?: ProConfig
  error?: string
}

/**
 * Information about a generation job.
 */
export interface JobResponse {
  id: string
  status: JobStatus
  mode: PipelineMode
  created_at: string
  started_at?: string
  completed_at?: string
  prompt?: string
  file_ids?: string[]
  guidance?: string
  progress?: ProgressResponse
  result?: ResultResponse
  error?: string
}

/**
 * List of generation jobs.
 */
export interface JobListResponse {
  jobs: JobResponse[]
  total: number
  page: number
  page_size: number
}

/**
 * Information about an uploaded file.
 */
export interface FileResponse {
  id: string
  filename: string
  content_type?: string
  size_bytes: number
  uploaded_at: string
  source_type: string
  extracted_text?: string
}

/**
 * List of uploaded files.
 */
export interface FileListResponse {
  files: FileResponse[]
  total: number
}

/**
 * Health check response.
 */
export interface HealthResponse {
  status: string
  version: string
  timestamp: string
}

/**
 * Standard error response.
 */
export interface ErrorResponse {
  error: string
  message: string
  details?: Record<string, unknown>
}

// =============================================================================
// Script Types
// =============================================================================

/**
 * Enhanced script data structure.
 */
export interface ScriptData {
  title?: string
  hook?: HookData | string
  modules?: ModuleData[]
  review_history?: ReviewEntry[]
  final_status?: FinalStatus
}

/**
 * Hook section of the script.
 */
export interface HookData {
  text: string
  emotion?: string
  duration_estimate_seconds?: number
}

/**
 * Module section of the script.
 */
export interface ModuleData {
  id: number
  title: string
  emotion_arc?: string
  chunks: ChunkData[]
}

/**
 * Individual chunk within a module.
 */
export interface ChunkData {
  text: string
  emotion?: string
  tension_level?: number
  keywords?: string[]
  visual_cues?: string[]
  audio_cues?: string[]
}

/**
 * Director review entry.
 */
export interface ReviewEntry {
  score?: number
  feedback?: string
  round?: number
}

/**
 * Final status of script review.
 */
export interface FinalStatus {
  approved: boolean
  total_rounds: number
  final_score: number
}

// =============================================================================
// WebSocket Types
// =============================================================================

/**
 * WebSocket message types.
 */
export type WebSocketMessageType =
  | 'progress'
  | 'complete'
  | 'error'
  | 'cancelled'
  | 'cancelling'
  | 'heartbeat'
  | 'ping'
  | 'pong'
  | 'trailer_ready'

/**
 * WebSocket message structure.
 */
export interface WebSocketMessage {
  type: WebSocketMessageType
  job_id?: string
  phase?: GenerationPhase
  message?: string
  progress_percent?: number
  current_step?: number
  total_steps?: number
  eta_seconds?: number
  preview?: string
  elapsed_seconds?: number
  success?: boolean
  output_path?: string
  video_url?: string
  duration_seconds?: number
  details?: Record<string, unknown>
  error?: string
  // Trailer-specific fields
  trailer_url?: string
}

/**
 * Trailer preview data.
 */
export interface TrailerData {
  url: string
  duration_seconds: number
}

/**
 * Phase timing data included in progress details.
 */
export interface PhaseTimings {
  phase_timings: Record<string, number>
  current_phase_elapsed: number
}

/**
 * Sub-progress for parallel asset generation.
 */
export interface ParallelStatus {
  tts: { done: number; total: number; elapsed_s?: number }
  bgm: { done: number; total: number; elapsed_s?: number }
  images: { done: number; total: number; elapsed_s?: number }
}

/**
 * Asset timing breakdown from the pipeline.
 */
export interface AssetTimings {
  tts: number
  bgm: number
  images: number
  mixing: number
  video_assembly: number
}

// =============================================================================
// Configuration Types
// =============================================================================

/**
 * Mode configuration details.
 */
export interface ModeConfig {
  name: string
  description: string
  features: string[]
  estimated_duration: string
}

/**
 * System configuration response.
 */
export interface ConfigResponse {
  modes: Record<string, ModeConfig>
  supported_formats: string[]
  max_file_size_mb: number
}

/**
 * Available voice preset.
 */
export interface VoicePreset {
  id: string
  description: string
}

/**
 * Voice configuration response.
 */
export interface VoiceConfigResponse {
  voices: Record<string, VoicePreset>
  default: string
}

// =============================================================================
// Interactive Chat Types (re-exported)
// =============================================================================

export * from './interactive'
