"""Client configuration from environment variables."""

from __future__ import annotations

import os
from pathlib import Path


def get_api_key() -> str:
    key = os.environ.get("PRESENTATION_VIDEO_API_KEY", "")
    if not key:
        raise RuntimeError(
            "PRESENTATION_VIDEO_API_KEY environment variable is required. "
            "Get one from your API server admin."
        )
    return key


def get_api_url() -> str:
    return os.environ.get("PRESENTATION_VIDEO_API_URL", "http://localhost:8000")


def get_download_dir() -> Path:
    d = Path(os.environ.get(
        "PRESENTATION_VIDEO_DOWNLOAD_DIR",
        str(Path.home() / "Downloads" / "presentation-videos"),
    ))
    d.mkdir(parents=True, exist_ok=True)
    return d
