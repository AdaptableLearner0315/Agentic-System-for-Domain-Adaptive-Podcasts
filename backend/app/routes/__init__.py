"""
API route modules for the Nell Podcast API.

Each module handles a specific resource:
- pipelines: Generation job management
- files: File upload and management
- config: System configuration
- outputs: Output file access
- interactive: Interactive chat sessions
- trailer: Trailer generation
- memory: User memory and personalization
"""

from . import pipelines, files, config, outputs, trailer, interactive, memory

__all__ = ["pipelines", "files", "config", "outputs", "trailer", "interactive", "memory"]
