"""Background job processor using threading."""

from __future__ import annotations

import json
import logging
import threading
from pathlib import Path
from typing import Any

from ..config import Config
from ..pipeline import run_pipeline
from ..tts.chatterbox import ChatterboxProvider
from ..tts.openai_tts import OpenAITTSProvider
from ..voices import get_voice
from . import job_store

logger = logging.getLogger(__name__)

_queue: list[dict[str, Any]] = []
_queue_lock = threading.Lock()
_worker_thread: threading.Thread | None = None
_stop_event = threading.Event()


def enqueue(
    job_id: str,
    pptx_path: str,
    narration_script: list[dict[str, Any]],
    mode: str,
    key_id: str,
    voice_name: str | None = None,
    tts_voice: str = "nova",
) -> None:
    """Add a job to the processing queue."""
    task = {
        "job_id": job_id,
        "pptx_path": pptx_path,
        "narration_script": narration_script,
        "mode": mode,
        "key_id": key_id,
        "voice_name": voice_name,
        "tts_voice": tts_voice,
    }
    with _queue_lock:
        _queue.append(task)
    _ensure_worker()


def _ensure_worker() -> None:
    """Start the worker thread if not already running."""
    global _worker_thread
    if _worker_thread is None or not _worker_thread.is_alive():
        _stop_event.clear()
        _worker_thread = threading.Thread(target=_worker_loop, daemon=True)
        _worker_thread.start()


def _worker_loop() -> None:
    """Process jobs one at a time from the queue."""
    while not _stop_event.is_set():
        task = None
        with _queue_lock:
            if _queue:
                task = _queue.pop(0)
        if task is None:
            _stop_event.wait(timeout=1)
            continue
        _process_job(task)


def _process_job(task: dict[str, Any]) -> None:
    """Process a single job using the existing pipeline."""
    job_id = task["job_id"]
    try:
        job_store.update_job(job_id, status="processing", progress="Starting...")
        config = Config.load()
        output_path = str(job_store.job_output_path(job_id))

        def on_progress(msg: str) -> None:
            job_store.update_job(job_id, progress=msg)

        # Build TTS provider
        if task["mode"] == "voice_clone":
            voices_dir = Path.home() / ".mcp-presentation-video" / "voices" / task["key_id"]
            voice = get_voice(voices_dir, task["voice_name"])
            provider = ChatterboxProvider(
                voice_sample_path=voice["sample_path"],
                python_path=config.chatterbox_python,
                script_path=config.chatterbox_script,
            )
        else:
            provider = OpenAITTSProvider(
                api_key=config.openai_api_key,
                voice=task.get("tts_voice", "nova"),
            )

        result_path = run_pipeline(
            config=config,
            presentation_path=task["pptx_path"],
            narration_script=task["narration_script"],
            tts_provider=provider,
            output_path=output_path,
            on_progress=on_progress,
        )

        job_store.update_job(
            job_id,
            status="completed",
            progress="Done",
        )
        logger.info("Job %s completed: %s", job_id, result_path)

    except Exception as exc:
        logger.exception("Job %s failed", job_id)
        job_store.update_job(
            job_id,
            status="failed",
            progress="Failed",
            error=str(exc),
        )


def stop_worker() -> None:
    """Signal the worker thread to stop."""
    _stop_event.set()
