"""
API route modules for the Nell Podcast API.

Each module handles a specific resource:
- pipelines: Generation job management
- files: File upload and management
- config: System configuration
- outputs: Output file access
"""

from . import pipelines, files, config, outputs

__all__ = ["pipelines", "files", "config", "outputs"]
