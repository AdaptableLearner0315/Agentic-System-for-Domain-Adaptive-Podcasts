"""
Application configuration using Pydantic settings.

Loads configuration from environment variables and .env file.
All settings can be overridden via environment variables.
"""

import os
from typing import Optional
from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Environment variables take precedence over .env file values.
    All settings have sensible defaults for development.

    Attributes:
        app_name: Application name for display
        app_version: Current API version
        debug: Enable debug mode
        api_prefix: Prefix for all API routes
        cors_origins: Allowed CORS origins
        upload_dir: Directory for uploaded files
        output_dir: Directory for generated outputs
        max_upload_size_mb: Maximum file upload size
        fal_key: Fal AI API key (also used for MiniMax TTS via fal.ai)
        anthropic_api_key: Anthropic API key
    """

    # Application settings
    app_name: str = "Nell Podcast API"
    app_version: str = "1.0.0"
    debug: bool = False

    # API settings
    api_prefix: str = "/api"
    # Allow common dev ports (3000-3010) for flexibility when ports are in use
    cors_origins: str = ",".join([
        f"http://localhost:{port}" for port in range(3000, 3011)
    ] + [
        f"http://127.0.0.1:{port}" for port in range(3000, 3011)
    ])

    # File settings
    upload_dir: str = "uploads"
    output_dir: str = str(Path(__file__).parent.parent.parent / "Output")
    max_upload_size_mb: int = 100

    # API Keys (loaded from .env)
    fal_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None

    # Job settings
    max_concurrent_jobs: int = 3
    job_timeout_seconds: int = 1800  # 30 minutes
    normal_mode_timeout_seconds: int = 300   # 5 minutes
    pro_mode_timeout_seconds: int = 480      # 8 minutes
    subprocess_timeout_seconds: int = 120    # 2 min per FFmpeg call

    # Database settings
    database_url: str = "sqlite+aiosqlite:///./data/nell.db"
    db_echo: bool = False  # Log SQL statements (debug)
    job_cache_days: int = 30  # Days to keep completed jobs

    def get_job_timeout(self, mode: str) -> int:
        """Get timeout in seconds for the given pipeline mode."""
        if mode == "pro":
            return self.pro_mode_timeout_seconds
        return self.normal_mode_timeout_seconds

    @property
    def cors_origins_list(self) -> list[str]:
        """Get CORS origins as a list."""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def upload_path(self) -> Path:
        """Get upload directory as Path object."""
        return Path(self.upload_dir)

    @property
    def output_path(self) -> Path:
        """Get output directory as Path object."""
        return Path(self.output_dir)

    @property
    def max_upload_size_bytes(self) -> int:
        """Get maximum upload size in bytes."""
        return self.max_upload_size_mb * 1024 * 1024

    @property
    def database_path(self) -> Path:
        """Get database file path from URL."""
        # Extract path from sqlite URL (e.g., sqlite+aiosqlite:///./data/nell.db -> ./data/nell.db)
        if self.database_url.startswith("sqlite"):
            path = self.database_url.split("///")[-1]
            return Path(path)
        return Path("./data/nell.db")

    def validate_api_keys(self) -> dict[str, bool]:
        """
        Check which API keys are configured.

        Returns:
            Dictionary mapping key names to their configured status.
        """
        return {
            "fal_key": bool(self.fal_key),
            "anthropic_api_key": bool(self.anthropic_api_key),
        }

    class Config:
        """Pydantic settings configuration."""
        env_file_encoding = "utf-8"
        case_sensitive = False
        # Look for .env in project root (parent of backend/)
        env_file = str(Path(__file__).parent.parent.parent / ".env")


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Uses LRU cache to ensure settings are only loaded once.
    Call get_settings.cache_clear() to reload settings.

    Returns:
        Settings instance with loaded configuration.
    """
    return Settings()


# Convenience function for accessing settings
settings = get_settings()
