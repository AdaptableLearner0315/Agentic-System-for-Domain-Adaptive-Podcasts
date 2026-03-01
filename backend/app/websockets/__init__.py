"""
WebSocket modules for real-time communication.

Provides WebSocket endpoints for:
- Progress streaming during generation
- Real-time status updates
"""

from . import progress

__all__ = ["progress"]
