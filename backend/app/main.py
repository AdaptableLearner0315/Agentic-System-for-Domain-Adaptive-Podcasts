"""
FastAPI application entry point for the Nell Podcast API.

This module creates and configures the FastAPI application,
including CORS, lifespan events, and route mounting.

Usage:
    uvicorn app.main:app --reload

Author: Sarath
"""

import sys
from pathlib import Path
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse

# Add parent directory to path for importing existing modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from .config import get_settings, Settings
from .routes import pipelines, files, config, outputs, trailer, interactive, memory, quality, series
from .websockets import progress, interactive as interactive_ws
from .models.responses import HealthResponse, ErrorResponse
from .database.connection import init_db, close_db
from .dependencies import get_job_manager
from .logging_config import setup_logging, get_logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.

    Handles startup and shutdown events:
    - Startup: Initialize database, load job history, create directories
    - Shutdown: Persist jobs, close database connection

    Args:
        app: FastAPI application instance.
    """
    # Startup
    settings = get_settings()
    logger = setup_logging(debug=settings.debug)

    # Ensure upload and output directories exist
    settings.upload_path.mkdir(parents=True, exist_ok=True)
    settings.output_path.mkdir(parents=True, exist_ok=True)

    # Initialize database
    logger.info("Initializing database...")
    await init_db()
    logger.info("Database ready: %s", settings.database_path.absolute())

    # Enable persistence and load job history
    job_manager = get_job_manager()
    job_manager.enable_persistence()
    loaded = await job_manager.load_jobs_from_db(days=settings.job_cache_days)
    logger.info("Loaded %d jobs from history", loaded)

    # Validate API keys
    api_keys = settings.validate_api_keys()
    missing_keys = [k for k, v in api_keys.items() if not v]
    if missing_keys:
        logger.warning("Missing API keys: %s", ", ".join(missing_keys))
        logger.warning("Some features may not work correctly.")

    logger.info("%s v%s starting...", settings.app_name, settings.app_version)
    logger.info("Upload directory: %s", settings.upload_path.absolute())
    logger.info("Output directory: %s", settings.output_path.absolute())

    yield

    # Shutdown
    logger.info("Shutting down Nell Podcast API...")

    # Persist any pending jobs
    persisted = await job_manager.persist_all_jobs()
    if persisted > 0:
        logger.info("Persisted %d jobs to database", persisted)

    # Close database connection
    await close_db()
    logger.info("Database connection closed")


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application instance.
    """
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="""
        Nell Podcast Enhancement System API

        Transform raw content into engaging, multi-sensory video podcasts using AI.

        ## Features
        - **Normal Mode**: Fast generation (~2 minutes)
        - **Pro Mode**: High-quality generation (~6 minutes)
        - **Multiple Input Formats**: Text, PDF, Word, audio, video, URLs
        - **Real-time Progress**: WebSocket progress streaming
        - **Three Input Modes**: Generation, Enhancement, Hybrid

        ## Getting Started
        1. Upload a file or provide a prompt
        2. Select Normal or Pro mode
        3. Start generation and track progress
        4. Download your finished podcast video
        """,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount routes
    app.include_router(
        pipelines.router,
        prefix=f"{settings.api_prefix}/pipelines",
        tags=["Pipelines"]
    )
    app.include_router(
        files.router,
        prefix=f"{settings.api_prefix}/files",
        tags=["Files"]
    )
    app.include_router(
        config.router,
        prefix=f"{settings.api_prefix}/config",
        tags=["Configuration"]
    )
    app.include_router(
        outputs.router,
        prefix=f"{settings.api_prefix}/outputs",
        tags=["Outputs"]
    )
    app.include_router(
        trailer.router,
        prefix=f"{settings.api_prefix}/trailer",
        tags=["Trailer"]
    )
    app.include_router(
        interactive.router,
        prefix=f"{settings.api_prefix}/interactive",
        tags=["Interactive"]
    )
    app.include_router(
        memory.router,
        tags=["User Memory"]
    )
    app.include_router(
        quality.router,
        prefix=f"{settings.api_prefix}/quality",
        tags=["Quality"]
    )
    app.include_router(
        series.router,
        prefix=f"{settings.api_prefix}/series",
        tags=["Series"]
    )

    # Mount WebSocket routes
    app.include_router(
        progress.router,
        prefix=f"{settings.api_prefix}/ws",
        tags=["WebSocket"]
    )
    app.include_router(
        interactive_ws.router,
        prefix=f"{settings.api_prefix}/ws/interactive",
        tags=["WebSocket"]
    )

    return app


# Create the application instance
app = create_app()


@app.get("/", include_in_schema=False)
async def root():
    """Redirect root to API documentation."""
    return RedirectResponse(url="/docs")


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Health check endpoint.

    Returns the service status and version information.
    Use this endpoint for load balancer health checks.

    Returns:
        HealthResponse with status, version, and timestamp.
    """
    settings = get_settings()
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        timestamp=datetime.utcnow()
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler for unhandled errors.

    Catches all unhandled exceptions and returns a standardized
    error response format.

    Args:
        request: The incoming request.
        exc: The exception that was raised.

    Returns:
        JSONResponse with error details.
    """
    settings = get_settings()

    error_response = ErrorResponse(
        error="internal_server_error",
        message=str(exc) if settings.debug else "An unexpected error occurred",
        details={"type": type(exc).__name__} if settings.debug else None
    )

    return JSONResponse(
        status_code=500,
        content=error_response.model_dump()
    )


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )
