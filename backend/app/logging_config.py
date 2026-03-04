"""
Logging configuration for the Nell backend.

Provides a consistent logging setup across all modules.
"""

import logging
import sys
from typing import Optional


def setup_logging(debug: bool = False, name: str = "nell") -> logging.Logger:
    """
    Configure and return a logger for the application.

    Args:
        debug: Enable debug level logging.
        name: Logger name (default: "nell").

    Returns:
        Configured logger instance.
    """
    level = logging.DEBUG if debug else logging.INFO

    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    return logging.getLogger(name)


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance.

    Args:
        name: Logger name. If None, returns the root nell logger.

    Returns:
        Logger instance.
    """
    if name:
        return logging.getLogger(f"nell.{name}")
    return logging.getLogger("nell")
