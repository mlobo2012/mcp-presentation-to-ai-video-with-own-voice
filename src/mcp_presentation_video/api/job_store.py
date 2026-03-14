"""Simple JSON-file-based job storage with file-lock thread safety."""

from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_JOBS_DIR = Path.home() / ".mcp-presentation-video" / "jobs"
_lock = threading.Lock()


def _job_dir(job_id: str) -> Path:
    d = _JOBS_DIR / job_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def _job_file(job_id: str) -> Path:
    return _job_dir(job_id) / "job.json"


def create_job(
    job_id: str,
    key_id: str,
    mode: str,
    voice_name: str | None = None,
    tts_voice: str = "nova",
) -> dict[str, Any]:
    """Create a new job record."""
    now = datetime.now(timezone.utc).isoformat()
    job = {
        "job_id": job_id,
        "key_id": key_id,
        "status": "pending",
        "progress": "Queued",
        "mode": mode,
        "voice_name": voice_name,
        "tts_voice": tts_voice,
        "error": None,
        "created_at": now,
        "updated_at": now,
    }
    with _lock:
        with open(_job_file(job_id), "w") as f:
            json.dump(job, f, indent=2)
    return job


def update_job(job_id: str, **fields: Any) -> dict[str, Any]:
    """Update specific fields on a job."""
    with _lock:
        jf = _job_file(job_id)
        with open(jf) as f:
            job = json.load(f)
        job.update(fields)
        job["updated_at"] = datetime.now(timezone.utc).isoformat()
        with open(jf, "w") as f:
            json.dump(job, f, indent=2)
    return job


def get_job(job_id: str) -> dict[str, Any] | None:
    """Get a job by ID."""
    jf = _JOBS_DIR / job_id / "job.json"
    if not jf.exists():
        return None
    with _lock:
        with open(jf) as f:
            return json.load(f)


def list_jobs(key_id: str, limit: int = 20) -> list[dict[str, Any]]:
    """List jobs for a given API key, most recent first."""
    if not _JOBS_DIR.exists():
        return []
    jobs = []
    with _lock:
        for jf in _JOBS_DIR.glob("*/job.json"):
            with open(jf) as f:
                job = json.load(f)
            if job.get("key_id") == key_id:
                jobs.append(job)
    jobs.sort(key=lambda j: j.get("updated_at", ""), reverse=True)
    return jobs[:limit]


def job_output_path(job_id: str) -> Path:
    """Return the path where the output MP4 should be written."""
    return _job_dir(job_id) / "output.mp4"
