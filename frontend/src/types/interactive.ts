/**
 * TypeScript type definitions for interactive podcast conversations.
 *
 * These types support the chat panel, voice input/output, and
 * WebSocket streaming for real-time conversations.
 */

// =============================================================================
// Enums
// =============================================================================

/**
 * Role of a chat message participant.
 */
export type MessageRole = 'user' | 'assistant' | 'system'

/**
 * Types of WebSocket streaming events for interactive chat.
 */
export type StreamEventType =
  | 'assistant_start'
  | 'assistant_chunk'
  | 'assistant_end'
  | 'audio_ready'
  | 'error'
  | 'session_started'
  | 'session_ended'
  | 'heartbeat'
  | 'pong'

/**
 * Types of messages sent from client to server.
 */
export type ClientMessageType = 'message' | 'ping' | 'end_session'

// =============================================================================
// Chat Message Types
// =============================================================================

/**
 * A single message in the conversation.
 */
export interface ChatMessage {
  /** Unique message identifier */
  id: string
  /** Who sent the message */
  role: MessageRole
  /** Text content of the message */
  content: string
  /** When the message was sent */
  timestamp: string
  /** TTS audio URL for playback (assistant messages only) */
  audio_url?: string
}

// =============================================================================
// Session Types
// =============================================================================

/**
 * Response after starting a session.
 */
export interface SessionResponse {
  /** Unique session identifier */
  session_id: string
  /** Associated podcast job ID */
  job_id: string
  /** Session creation time */
  created_at: string
  /** Initial greeting from assistant */
  welcome_message: ChatMessage
}

/**
 * Information about an active session.
 */
export interface SessionInfo {
  /** Session identifier */
  session_id: string
  /** Associated podcast job ID */
  job_id: string
  /** When session started */
  created_at: string
  /** Number of messages exchanged */
  message_count: number
  /** Whether session is still active */
  is_active: boolean
}

// =============================================================================
// Message Request/Response Types
// =============================================================================

/**
 * Request to send a text message.
 */
export interface MessageRequest {
  /** User's message text */
  content: string
  /** Whether to generate TTS response audio */
  generate_audio?: boolean
}

/**
 * Response to a user message (non-streaming).
 */
export interface MessageResponse {
  /** The user's message that was sent */
  user_message: ChatMessage
  /** The AI's response */
  assistant_message: ChatMessage
}

/**
 * Response from voice transcription.
 */
export interface TranscriptionResponse {
  /** Transcribed text from audio */
  transcription: string
  /** Transcription confidence score (0-1) */
  confidence: number
  /** Audio duration in seconds */
  duration_seconds?: number
}

// =============================================================================
// History Types
// =============================================================================

/**
 * Conversation history for a session.
 */
export interface HistoryResponse {
  /** Session identifier */
  session_id: string
  /** List of messages in chronological order */
  messages: ChatMessage[]
  /** Total message count */
  total: number
}

// =============================================================================
// WebSocket Stream Types
// =============================================================================

/**
 * WebSocket message for real-time streaming.
 */
export interface StreamMessage {
  /** Event type */
  type: StreamEventType
  /** Session this event belongs to */
  session_id: string
  /** Message ID (for chunk events) */
  message_id?: string
  /** Text content (for chunk events) */
  content?: string
  /** Audio URL (for audio_ready events) */
  audio_url?: string
  /** Error message (for error events) */
  error?: string
  /** Timestamp */
  timestamp?: string
}

/**
 * Message from WebSocket client to server.
 */
export interface ClientMessage {
  /** Message type */
  type: ClientMessageType
  /** Message content (for message type) */
  content?: string
  /** Whether to generate TTS */
  generate_audio?: boolean
}

// =============================================================================
// Voice Recording Types
// =============================================================================

/**
 * Voice recording state.
 */
export interface VoiceRecordingState {
  /** Whether currently recording */
  isRecording: boolean
  /** Audio level (0-1) for visualizer */
  audioLevel: number
  /** Whether microphone permission is granted */
  hasPermission: boolean
  /** Recording duration in seconds */
  duration: number
}

/**
 * Voice recording configuration.
 */
export interface VoiceRecordingConfig {
  /** Audio MIME type */
  mimeType: string
  /** Sample rate in Hz */
  sampleRate: number
  /** Enable echo cancellation */
  echoCancellation: boolean
  /** Enable noise suppression */
  noiseSuppression: boolean
}

// =============================================================================
// Audio Playback Types
// =============================================================================

/**
 * Audio playback state.
 */
export interface AudioPlaybackState {
  /** Whether audio is currently playing */
  isPlaying: boolean
  /** Current playback position in seconds */
  currentTime: number
  /** Total duration in seconds */
  duration: number
  /** ID of currently playing message */
  messageId?: string
}

/**
 * Audio queue item for sequential playback.
 */
export interface AudioQueueItem {
  /** Message ID */
  messageId: string
  /** Audio URL */
  url: string
}

// =============================================================================
// Chat Panel Types
// =============================================================================

/**
 * Chat panel display mode.
 */
export type ChatPanelMode = 'collapsed' | 'expanded' | 'fullscreen'

/**
 * Chat input state.
 */
export interface ChatInputState {
  /** Current text in input */
  text: string
  /** Whether input is disabled */
  isDisabled: boolean
  /** Whether user is currently typing */
  isTyping: boolean
}

/**
 * Message being streamed (partial content).
 */
export interface StreamingMessage {
  /** Message ID */
  id: string
  /** Accumulated content so far */
  content: string
  /** Whether streaming is complete */
  isComplete: boolean
}

// =============================================================================
// Hook Return Types
// =============================================================================

/**
 * Return type for useInteractiveChat hook.
 */
export interface UseInteractiveChatReturn {
  /** Active session ID */
  sessionId: string | null
  /** All messages in conversation */
  messages: ChatMessage[]
  /** Whether WebSocket is connected */
  isConnected: boolean
  /** Whether waiting for response */
  isLoading: boolean
  /** Current streaming message (if any) */
  streamingMessage: StreamingMessage | null
  /** Error message (if any) */
  error: string | null
  /** Start a new session */
  startSession: (jobId: string) => Promise<void>
  /** Send a text message */
  sendMessage: (text: string) => Promise<void>
  /** End the current session */
  endSession: () => Promise<void>
  /** Clear error state */
  clearError: () => void
}

/**
 * Return type for useVoiceRecording hook.
 */
export interface UseVoiceRecordingReturn {
  /** Whether currently recording */
  isRecording: boolean
  /** Audio level (0-1) for visualizer */
  audioLevel: number
  /** Whether microphone permission is granted */
  hasPermission: boolean
  /** Recording duration in seconds */
  duration: number
  /** Start recording */
  startRecording: () => Promise<void>
  /** Stop recording and return audio blob */
  stopRecording: () => Promise<Blob | null>
  /** Request microphone permission */
  requestPermission: () => Promise<boolean>
  /** Error message (if any) */
  error: string | null
}

/**
 * Return type for useAudioPlayback hook.
 */
export interface UseAudioPlaybackReturn {
  /** Whether audio is currently playing */
  isPlaying: boolean
  /** ID of currently playing message */
  currentMessageId: string | null
  /** Play audio for a message */
  play: (url: string, messageId: string) => void
  /** Stop playback */
  stop: () => void
  /** Add to playback queue */
  queue: (url: string, messageId: string) => void
  /** Clear the queue */
  clearQueue: () => void
}

// =============================================================================
// API Response Types
// =============================================================================

/**
 * Generic API error response.
 */
export interface InteractiveErrorResponse {
  error: string
  message: string
  details?: Record<string, unknown>
}
