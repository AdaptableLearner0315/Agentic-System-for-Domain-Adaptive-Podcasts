/**
 * React hook for file upload management.
 *
 * Provides state management for file uploads with progress tracking.
 */

import { useState, useCallback } from 'react'
import { uploadFile, deleteFile as apiDeleteFile } from '@/lib/api'
import type { FileResponse } from '@/types'

/**
 * Uploaded file with local state.
 */
interface UploadedFile extends FileResponse {
  /** Local upload progress (0-100) */
  uploadProgress?: number
  /** Whether upload is in progress */
  isUploading?: boolean
  /** Upload error if any */
  uploadError?: string
}

/**
 * Return type for the useFileUpload hook.
 */
interface UseFileUploadReturn {
  /** List of uploaded files */
  files: UploadedFile[]
  /** Whether any upload is in progress */
  isUploading: boolean
  /** Upload error if any */
  error: string | null
  /** Upload a file */
  upload: (file: File) => Promise<FileResponse>
  /** Upload multiple files */
  uploadMultiple: (files: FileList | File[]) => Promise<FileResponse[]>
  /** Remove a file */
  remove: (fileId: string) => Promise<void>
  /** Clear all files */
  clear: () => void
  /** Get file IDs for API requests */
  getFileIds: () => string[]
}

/**
 * Hook for managing file uploads.
 *
 * @returns File upload state and control functions
 *
 * @example
 * ```tsx
 * const { files, upload, remove, getFileIds } = useFileUpload()
 *
 * const handleDrop = async (fileList: FileList) => {
 *   await uploadMultiple(fileList)
 * }
 *
 * // Use file IDs in generation request
 * startGeneration({ file_ids: getFileIds(), mode: 'normal' })
 * ```
 */
export function useFileUpload(): UseFileUploadReturn {
  const [files, setFiles] = useState<UploadedFile[]>([])
  const [isUploading, setIsUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  /**
   * Upload a single file.
   */
  const upload = useCallback(async (file: File): Promise<FileResponse> => {
    setIsUploading(true)
    setError(null)

    try {
      const response = await uploadFile(file)

      setFiles((prev) => [
        ...prev,
        {
          ...response,
          isUploading: false,
        },
      ])

      return response
    } catch (e) {
      const errorMsg = e instanceof Error ? e.message : 'Upload failed'
      setError(errorMsg)
      throw e
    } finally {
      setIsUploading(false)
    }
  }, [])

  /**
   * Upload multiple files.
   */
  const uploadMultiple = useCallback(
    async (fileList: FileList | File[]): Promise<FileResponse[]> => {
      const filesArray = Array.from(fileList)
      const results: FileResponse[] = []

      setIsUploading(true)
      setError(null)

      for (const file of filesArray) {
        try {
          const response = await uploadFile(file)
          results.push(response)

          setFiles((prev) => [
            ...prev,
            {
              ...response,
              isUploading: false,
            },
          ])
        } catch (e) {
          const errorMsg = e instanceof Error ? e.message : `Failed to upload ${file.name}`
          setError(errorMsg)
          // Continue with other files
        }
      }

      setIsUploading(false)
      return results
    },
    []
  )

  /**
   * Remove a file.
   */
  const remove = useCallback(async (fileId: string): Promise<void> => {
    try {
      await apiDeleteFile(fileId)
      setFiles((prev) => prev.filter((f) => f.id !== fileId))
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to delete file')
      throw e
    }
  }, [])

  /**
   * Clear all files.
   */
  const clear = useCallback(() => {
    // Delete all files from server
    files.forEach((file) => {
      apiDeleteFile(file.id).catch(() => {
        // Ignore errors during cleanup
      })
    })
    setFiles([])
    setError(null)
  }, [files])

  /**
   * Get file IDs for API requests.
   */
  const getFileIds = useCallback((): string[] => {
    return files.map((f) => f.id)
  }, [files])

  return {
    files,
    isUploading,
    error,
    upload,
    uploadMultiple,
    remove,
    clear,
    getFileIds,
  }
}
