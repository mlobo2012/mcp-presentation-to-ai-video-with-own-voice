"""Voice management API routes."""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from ...voices import get_voice, list_voices, register_voice
from ..auth import require_api_key
from ..models import VoiceCreateResponse, VoiceInfo

router = APIRouter(prefix="/api/v1/voices", tags=["voices"])

_VOICES_BASE = Path.home() / ".mcp-presentation-video" / "voices"


def _user_voices_dir(key_id: str) -> Path:
    d = _VOICES_BASE / key_id
    d.mkdir(parents=True, exist_ok=True)
    return d


@router.post("", response_model=VoiceCreateResponse)
async def upload_voice(
    audio_file: UploadFile = File(...),
    name: str = Form(...),
    description: str = Form(""),
    key: dict[str, Any] = Depends(require_api_key),
) -> VoiceCreateResponse:
    """Upload a voice sample for voice cloning."""
    # Validate audio file has a reasonable extension
    if audio_file.filename:
        ext = Path(audio_file.filename).suffix.lower()
        if ext not in (".wav", ".mp3", ".m4a", ".flac", ".ogg", ".aac"):
            raise HTTPException(status_code=400, detail=f"Unsupported audio format: {ext}")

    # Save to temp file first
    contents = await audio_file.read()
    if len(contents) < 1000:
        raise HTTPException(status_code=400, detail="Audio file too small")

    suffix = Path(audio_file.filename or "sample.wav").suffix
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.write(contents)
    tmp.close()

    try:
        voices_dir = _user_voices_dir(key["key_id"])
        meta = register_voice(
            voices_dir=voices_dir,
            name=name,
            voice_sample_path=tmp.name,
            description=description,
        )
        return VoiceCreateResponse(name=meta["name"], message="Voice registered successfully")
    finally:
        Path(tmp.name).unlink(missing_ok=True)


@router.get("", response_model=list[VoiceInfo])
async def list_user_voices(
    key: dict[str, Any] = Depends(require_api_key),
) -> list[VoiceInfo]:
    """List the user's registered voices."""
    voices_dir = _user_voices_dir(key["key_id"])
    voices = list_voices(voices_dir)
    return [
        VoiceInfo(
            name=v["name"],
            description=v.get("description", ""),
            registered_at=v.get("registered_at", ""),
        )
        for v in voices
    ]


@router.delete("/{name}")
async def delete_voice(
    name: str,
    key: dict[str, Any] = Depends(require_api_key),
) -> dict[str, str]:
    """Delete a registered voice profile."""
    voices_dir = _user_voices_dir(key["key_id"])
    voice_dir = voices_dir / name
    if not voice_dir.exists():
        raise HTTPException(status_code=404, detail=f"Voice '{name}' not found")
    shutil.rmtree(voice_dir)
    return {"message": f"Voice '{name}' deleted"}
