"""
Application constants for the Nell backend.

Centralizes magic numbers and configuration values that are used
across multiple modules.
"""

# Job identifier length (truncated UUID)
JOB_ID_LENGTH = 8

# Chunk size for streaming file responses (1MB)
STREAM_CHUNK_SIZE = 1024 * 1024
