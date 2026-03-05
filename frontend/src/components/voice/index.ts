/**
 * Voice experience components for Nell.
 *
 * Provides a complete voice interaction system with:
 * - Tap-to-talk recording
 * - Smart end-of-speech detection
 * - Real-time transcription
 * - AI response visualization
 * - Interruption handling
 * - Memory consent management
 */

export { VoiceExperience } from './VoiceExperience'
export { VoiceButton } from './VoiceButton'
export { VoiceVisualizer } from './VoiceVisualizer'
export { VoiceAvatar, SpeakingIndicator } from './VoiceAvatar'
export { TranscriptPreview, TranscriptInline } from './TranscriptPreview'
export { CountdownRing } from './CountdownRing'
export { MemoryConsentModal, useMemoryConsent, hasAskedConsent } from './MemoryConsentModal'
