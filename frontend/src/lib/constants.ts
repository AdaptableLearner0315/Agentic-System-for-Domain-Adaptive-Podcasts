/**
 * Application-wide constants for the Nell frontend.
 */

/**
 * Storage keys used for localStorage and sessionStorage.
 * Centralized here to prevent typos and make refactoring easier.
 */
export const STORAGE_KEYS = {
  /** Active job ID for recovery across page refreshes */
  ACTIVE_JOB_ID: 'nell_active_job_id',
  /** Job data to reuse when navigating from history to create page */
  REUSE_JOB: 'nell_reuse_job',
} as const
