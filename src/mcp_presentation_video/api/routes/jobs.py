"""Job management API routes."""

from __future__ import annotations

import json
import shutil
import tempfile
import uuid
import zipfile
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from ..auth import require_api_key
from ..job_store import create_job, get_job, job_output_path, list_jobs
from ..models import JobCreateResponse, JobListItem, JobStatus
from ..worker import enqueue

router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])


@router.post("", response_model=JobCreateResponse)
async def create_video_job(
    pptx_file: UploadFile = File(...),
    narration_script: str = Form(...),
    mode: str = Form("standard"),
    voice_name: str | None = Form(None),
    tts_voice: str = Form("nova"),
    key: dict[str, Any] = Depends(require_api_key),
) -> JobCreateResponse:
    """Create a new video generation job."""
    # Validate mode
    if mode not in ("standard", "voice_clone"):
        raise HTTPException(status_code=400, detail="mode must be 'standard' or 'voice_clone'")

    if mode == "voice_clone" and not voice_name:
        raise HTTPException(status_code=400, detail="voice_name required for voice_clone mode")

    # Validate PPTX is a valid ZIP
    contents = await pptx_file.read()
    try:
        import io
        zipfile.ZipFile(io.BytesIO(contents))
    except zipfile.BadZipFile:
        raise HTTPException(status_code=400, detail="Uploaded file is not a valid PPTX")

    # Parse narration script
    try:
        script = json.loads(narration_script)
        if not isinstance(script, list):
            raise ValueError("Must be a JSON array")
    except (json.JSONDecodeError, ValueError) as e:
        raise HTTPException(status_code=400, detail=f"Invalid narration_script JSON: {e}")

    # Save PPTX to temp file
    tmp_dir = tempfile.mkdtemp(prefix="mcp_upload_")
    pptx_path = Path(tmp_dir) / "presentation.pptx"
    pptx_path.write_bytes(contents)

    # Create job
    job_id = uuid.uuid4().hex[:12]
    key_id = key["key_id"]
    create_job(job_id=job_id, key_id=key_id, mode=mode, voice_name=voice_name, tts_voice=tts_voice)

    # Enqueue for background processing
    enqueue(
        job_id=job_id,
        pptx_path=str(pptx_path),
        narration_script=script,
        mode=mode,
        key_id=key_id,
        voice_name=voice_name,
        tts_voice=tts_voice,
    )

    return JobCreateResponse(job_id=job_id, status="pending")


@router.get("", response_model=list[JobListItem])
async def list_user_jobs(
    key: dict[str, Any] = Depends(require_api_key),
) -> list[JobListItem]:
    """List the user's recent jobs."""
    jobs = list_jobs(key["key_id"])
    return [
        JobListItem(
            job_id=j["job_id"],
            status=j["status"],
            created_at=j["created_at"],
            updated_at=j["updated_at"],
        )
        for j in jobs
    ]


@router.get("/{job_id}", response_model=JobStatus)
async def get_job_status(
    job_id: str,
    key: dict[str, Any] = Depends(require_api_key),
) -> JobStatus:
    """Get the status of a job."""
    job = get_job(job_id)
    if job is None or job.get("key_id") != key["key_id"]:
        raise HTTPException(status_code=404, detail="Job not found")

    video_url = None
    if job["status"] == "completed":
        video_url = f"/api/v1/jobs/{job_id}/download"

    return JobStatus(
        job_id=job["job_id"],
        status=job["status"],
        progress=job.get("progress", ""),
        video_url=video_url,
        error=job.get("error"),
        created_at=job["created_at"],
        updated_at=job["updated_at"],
    )


@router.get("/{job_id}/download")
async def download_video(
    job_id: str,
    key: dict[str, Any] = Depends(require_api_key),
) -> FileResponse:
    """Download the finished MP4 video."""
    job = get_job(job_id)
    if job is None or job.get("key_id") != key["key_id"]:
        raise HTTPException(status_code=404, detail="Job not found")

    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail=f"Job not ready (status: {job['status']})")

    output = job_output_path(job_id)
    if not output.exists():
        raise HTTPException(status_code=404, detail="Video file not found")

    return FileResponse(
        path=str(output),
        media_type="video/mp4",
        filename=f"{job_id}.mp4",
    )
