"""FastAPI application for the presentation-to-video API server."""

from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .auth import get_admin_key
from .models import HealthResponse
from .routes.admin import router as admin_router
from .routes.jobs import router as jobs_router
from .routes.voices import router as voices_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Presentation Video API",
    description="Convert PowerPoint presentations into narrated AI videos",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(jobs_router)
app.include_router(voices_router)
app.include_router(admin_router)


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    return HealthResponse()


@app.on_event("startup")
async def startup() -> None:
    admin_key = get_admin_key()
    logger.info("Admin key ready (stored in ~/.mcp-presentation-video/admin_key.txt)")
    logger.info("Server started on http://0.0.0.0:8000")


def run_server() -> None:
    """Entry point: run the API server with uvicorn."""
    import os
    import uvicorn

    port = int(os.environ.get("API_PORT", "8100"))
    host = os.environ.get("API_HOST", "0.0.0.0")
    uvicorn.run(
        "mcp_presentation_video.api.app:app",
        host=host,
        port=port,
        log_level="info",
    )


if __name__ == "__main__":
    run_server()
