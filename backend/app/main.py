"""FastAPI application entry point."""
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.config import settings
from app.database import init_db, close_db
from app.redis import close_redis


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager.

    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting Adminory application...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")

    # Initialize database
    await init_db()
    logger.info("Database initialized")

    yield

    # Shutdown
    logger.info("Shutting down Adminory application...")
    await close_db()
    await close_redis()
    logger.info("Cleanup complete")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="Universal Admin Control Plane Framework",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Workspace context middleware
from app.middleware.workspace import workspace_context_middleware
app.middleware("http")(workspace_context_middleware)


@app.get("/")
async def root() -> dict:
    """Root endpoint."""
    return {
        "name": settings.APP_NAME,
        "version": "0.1.0",
        "environment": settings.ENVIRONMENT,
        "status": "running",
    }


@app.get("/health")
async def health() -> dict:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
    }


# Include API routers
from app.api import auth
from app.api.external import workspace
from app.api.internal import tray as tray_router

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(workspace.router, prefix="/api/external", tags=["workspace"])
app.include_router(tray_router.router, prefix="/api/internal/tray", tags=["tray"])

# TODO: Include additional routers when ready
# from app.api import sso
# from app.api.internal import system, users, workspaces, audit, jobs, feature_flags
# from app.api.external import workspace, members, usage, api_keys, integrations, billing, support
#
# app.include_router(sso.router, prefix="/api/sso", tags=["sso"])
# app.include_router(system.router, prefix="/api/internal/system", tags=["internal-system"])
# ... etc
