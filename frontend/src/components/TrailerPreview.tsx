/**
 * TrailerPreview - Shows a looping preview trailer while full podcast generates.
 *
 * Displays playable content at ~55s into generation, giving users something
 * to engage with while the full podcast (90s+) continues generating.
 */

interface TrailerPreviewProps {
  /** URL to the trailer video/audio */
  trailerUrl: string
  /** Duration of the trailer in seconds */
  duration: number
  /** Whether the full podcast is ready */
  isFullReady: boolean
  /** Callback when user wants to view full result */
  onViewFull: () => void
}

export function TrailerPreview({
  trailerUrl,
  duration,
  isFullReady,
  onViewFull,
}: TrailerPreviewProps) {
  // Determine if this is video or audio based on URL or content type
  const isVideo = trailerUrl.endsWith('.mp4') || !trailerUrl.includes('.mp3')

  return (
    <div className="card border-2 border-primary/30 bg-primary/5 animate-in">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-primary text-primary-foreground">
            Preview Ready
          </span>
          {!isFullReady && (
            <span className="text-sm text-muted-foreground">
              Full podcast generating...
            </span>
          )}
        </div>
        {duration > 0 && (
          <span className="text-xs text-muted-foreground">
            {Math.round(duration)}s preview
          </span>
        )}
      </div>

      {/* Media Player */}
      {isVideo ? (
        <video
          className="w-full rounded-lg bg-black"
          src={trailerUrl}
          controls
          autoPlay
          loop
          playsInline
        >
          Your browser does not support the video tag.
        </video>
      ) : (
        <div className="bg-gray-800 rounded-lg p-4">
          <audio
            className="w-full"
            src={trailerUrl}
            controls
            autoPlay
            loop
          >
            Your browser does not support the audio tag.
          </audio>
          <p className="text-xs text-muted-foreground mt-2 text-center">
            Audio preview - video generating...
          </p>
        </div>
      )}

      {/* Full Podcast Ready Button */}
      {isFullReady && (
        <button
          className="btn-primary w-full mt-4 flex items-center justify-center gap-2"
          onClick={onViewFull}
        >
          <svg
            className="w-5 h-5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"
            />
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          Full Podcast Ready - Watch Now
        </button>
      )}

      {/* Generating indicator */}
      {!isFullReady && (
        <div className="flex items-center justify-center gap-2 mt-4 text-sm text-muted-foreground">
          <svg
            className="animate-spin h-4 w-4"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
          <span>Full version generating in background...</span>
        </div>
      )}
    </div>
  )
}

export default TrailerPreview
