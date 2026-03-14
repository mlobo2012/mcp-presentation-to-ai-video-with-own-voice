"""HTTP client for the remote presentation-video API."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Callable, Optional

import httpx


class APIClient:
    """Thin HTTP client wrapping the presentation-video API."""

    def __init__(self, base_url: str, api_key: str, timeout: float = 300.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._headers = {"Authorization": f"Bearer {api_key}"}
        self._timeout = timeout

    # --- Jobs ---

    def create_job(
        self,
        pptx_path: str,
        narration_script: list[dict[str, Any]],
        mode: str = "standard",
        voice_name: str | None = None,
        tts_voice: str = "nova",
    ) -> dict[str, Any]:
        """Upload PPTX and create a video generation job."""
        with open(pptx_path, "rb") as f:
            files = {"pptx_file": ("presentation.pptx", f, "application/octet-stream")}
            data = {
                "narration_script": json.dumps(narration_script),
                "mode": mode,
                "tts_voice": tts_voice,
            }
            if voice_name:
                data["voice_name"] = voice_name

            with httpx.Client(timeout=self._timeout) as client:
                resp = client.post(
                    f"{self._base_url}/api/v1/jobs",
                    headers=self._headers,
                    files=files,
                    data=data,
                )
                resp.raise_for_status()
                return resp.json()

    def get_job_status(self, job_id: str) -> dict[str, Any]:
        with httpx.Client(timeout=30) as client:
            resp = client.get(
                f"{self._base_url}/api/v1/jobs/{job_id}",
                headers=self._headers,
            )
            resp.raise_for_status()
            return resp.json()

    def poll_until_done(
        self,
        job_id: str,
        interval: float = 5.0,
        on_progress: Optional[Callable[[str], None]] = None,
    ) -> dict[str, Any]:
        """Poll job status until completed or failed."""
        last_progress = ""
        while True:
            status = self.get_job_status(job_id)
            progress = status.get("progress", "")
            if progress != last_progress and on_progress:
                on_progress(progress)
                last_progress = progress

            if status["status"] == "completed":
                return status
            if status["status"] == "failed":
                raise RuntimeError(f"Job failed: {status.get('error', 'unknown error')}")

            time.sleep(interval)

    def download_video(self, job_id: str, dest: Path) -> Path:
        """Download the completed video to a local path."""
        dest.parent.mkdir(parents=True, exist_ok=True)
        with httpx.Client(timeout=self._timeout) as client:
            with client.stream(
                "GET",
                f"{self._base_url}/api/v1/jobs/{job_id}/download",
                headers=self._headers,
            ) as resp:
                resp.raise_for_status()
                with open(dest, "wb") as f:
                    for chunk in resp.iter_bytes(chunk_size=8192):
                        f.write(chunk)
        return dest

    # --- Voices ---

    def upload_voice(
        self, audio_path: str, name: str, description: str = ""
    ) -> dict[str, Any]:
        """Upload a voice sample."""
        with open(audio_path, "rb") as f:
            files = {"audio_file": (Path(audio_path).name, f, "application/octet-stream")}
            data = {"name": name, "description": description}
            with httpx.Client(timeout=self._timeout) as client:
                resp = client.post(
                    f"{self._base_url}/api/v1/voices",
                    headers=self._headers,
                    files=files,
                    data=data,
                )
                resp.raise_for_status()
                return resp.json()

    def list_voices(self) -> list[dict[str, Any]]:
        with httpx.Client(timeout=30) as client:
            resp = client.get(
                f"{self._base_url}/api/v1/voices",
                headers=self._headers,
            )
            resp.raise_for_status()
            return resp.json()

    def delete_voice(self, name: str) -> dict[str, Any]:
        with httpx.Client(timeout=30) as client:
            resp = client.delete(
                f"{self._base_url}/api/v1/voices/{name}",
                headers=self._headers,
            )
            resp.raise_for_status()
            return resp.json()
