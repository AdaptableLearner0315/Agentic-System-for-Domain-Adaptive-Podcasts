'use client'

import { useState, useCallback, useRef } from 'react'
import { uploadFile, deleteFile } from '@/lib/api'

interface FileUploadProps {
  /** Callback when a file is successfully uploaded */
  onFileUploaded: (fileId: string) => void
  /** Callback when a file is removed */
  onFileRemoved: (fileId: string) => void
  /** List of currently uploaded file IDs */
  uploadedFiles: string[]
  /** Whether upload is disabled */
  disabled?: boolean
}

interface UploadedFile {
  id: string
  name: string
  size: number
  type: string
}

/**
 * Compact file upload component.
 *
 * Compact button-style drop zone with uploaded files shown as chips.
 *
 * @param onFileUploaded - Callback when file is uploaded
 * @param onFileRemoved - Callback when file is removed
 * @param uploadedFiles - List of uploaded file IDs
 * @param disabled - Whether upload is disabled
 */
export function FileUpload({
  onFileUploaded,
  onFileRemoved,
  uploadedFiles,
  disabled = false,
}: FileUploadProps) {
  const [isDragging, setIsDragging] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [files, setFiles] = useState<UploadedFile[]>([])
  const fileInputRef = useRef<HTMLInputElement>(null)

  /**
   * Handle file drop or selection.
   */
  const handleFiles = useCallback(
    async (fileList: FileList) => {
      if (disabled) return

      setError(null)
      setIsUploading(true)

      for (const file of Array.from(fileList)) {
        try {
          const response = await uploadFile(file)
          const uploadedFile: UploadedFile = {
            id: response.id,
            name: file.name,
            size: file.size,
            type: response.source_type,
          }
          setFiles((prev) => [...prev, uploadedFile])
          onFileUploaded(response.id)
        } catch (err) {
          setError(err instanceof Error ? err.message : 'Upload failed')
        }
      }

      setIsUploading(false)
    },
    [disabled, onFileUploaded]
  )

  const handleDragOver = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault()
      if (!disabled) setIsDragging(true)
    },
    [disabled]
  )

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }, [])

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault()
      setIsDragging(false)
      if (e.dataTransfer.files.length > 0) {
        handleFiles(e.dataTransfer.files)
      }
    },
    [handleFiles]
  )

  const handleInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      if (e.target.files && e.target.files.length > 0) {
        handleFiles(e.target.files)
      }
    },
    [handleFiles]
  )

  const handleRemoveFile = useCallback(
    async (fileId: string) => {
      try {
        await deleteFile(fileId)
        setFiles((prev) => prev.filter((f) => f.id !== fileId))
        onFileRemoved(fileId)
      } catch {
        setError('Failed to remove file')
      }
    },
    [onFileRemoved]
  )

  const formatSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  return (
    <div className="space-y-3">
      {/* Compact Drop Zone */}
      <div
        className={`
          relative border border-dashed rounded-lg p-4 text-center
          transition-colors cursor-pointer
          ${isDragging ? 'border-primary bg-primary/5' : 'border-border'}
          ${disabled ? 'opacity-50 cursor-not-allowed' : 'hover:border-muted-foreground'}
        `}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => !disabled && fileInputRef.current?.click()}
      >
        <input
          ref={fileInputRef}
          type="file"
          className="hidden"
          onChange={handleInputChange}
          disabled={disabled}
          multiple
          accept=".txt,.md,.pdf,.docx,.doc,.mp3,.wav,.m4a,.mp4,.mov,.avi,.mkv"
        />

        {isUploading ? (
          <div className="flex items-center justify-center gap-2">
            <span className="spinner h-4 w-4 text-primary" />
            <span className="text-sm text-muted-foreground">Uploading...</span>
          </div>
        ) : (
          <div className="flex items-center justify-center gap-2">
            <svg
              className="w-5 h-5 text-muted-foreground"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
              />
            </svg>
            <span className="text-sm text-muted-foreground">
              <span className="text-primary font-medium">Upload</span> or drag files
            </span>
            <span className="text-xs text-muted-foreground hidden sm:inline">
              (PDF, Word, Audio, Video)
            </span>
          </div>
        )}
      </div>

      {/* Error Message */}
      {error && (
        <p className="text-sm text-destructive flex items-center gap-2">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          {error}
        </p>
      )}

      {/* Uploaded Files as Compact Chips */}
      {files.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {files.map((file) => (
            <div
              key={file.id}
              className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-secondary text-sm"
            >
              <span className="truncate max-w-[150px]">{file.name}</span>
              <span className="text-xs text-muted-foreground">{formatSize(file.size)}</span>
              <button
                className="text-muted-foreground hover:text-destructive transition-colors"
                onClick={(e) => {
                  e.stopPropagation()
                  handleRemoveFile(file.id)
                }}
                disabled={disabled}
                aria-label="Remove file"
              >
                <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
