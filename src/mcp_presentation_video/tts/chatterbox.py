"""Chatterbox TTS provider - shells out to separate venv for voice cloning."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any

from .base import ProgressCallback, TTSError, TTSProvider


class ChatterboxProvider(TTSProvider):
    """Voice cloning TTS via Chatterbox, running in a separate Python venv."""

    def __init__(
        self,
        voice_sample_path: str,
        python_path: str,
        script_path: str,
        accent: str | None = None,
    ):
        self.voice_sample_path = voice_sample_path
        self.python_path = python_path
        self.script_path = script_path
        self.accent = accent

        if not Path(voice_sample_path).exists():
            raise TTSError(f"Voice sample not found: {voice_sample_path}")

    def synthesize(
        self,
        narration_script: list[dict[str, Any]],
        output_dir: Path,
        on_progress: ProgressCallback = None,
    ) -> dict[int, Path]:
        """Synthesize audio for each slide using Chatterbox voice cloning."""
        output_dir.mkdir(parents=True, exist_ok=True)
        audio_files: dict[int, Path] = {}
        total = len(narration_script)

        for i, entry in enumerate(narration_script, start=1):
            slide_num = entry["slide_number"]
            text = entry["narration_text"]
            output_path = output_dir / f"slide_{slide_num:03d}.wav"

            if on_progress:
                on_progress(f"Synthesizing audio for slide {slide_num} ({i}/{total})")

            cmd = [
                self.python_path,
                self.script_path,
                "--text", text,
                "--voice", self.voice_sample_path,
                "--output", str(output_path),
            ]
            if self.accent:
                cmd.extend(["--accent", self.accent])

            model_path = os.environ.get("CHATTERBOX_TTS_MODEL")
            if model_path:
                cmd.extend(["--model", model_path])

            extra_args = os.environ.get("CHATTERBOX_TTS_EXTRA_ARGS")
            if extra_args:
                cmd.extend(extra_args.split())

            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=300
            )
            if result.returncode != 0:
                raise TTSError(
                    f"Chatterbox TTS failed for slide {slide_num}: {result.stderr}"
                )

            if not output_path.exists() or output_path.stat().st_size < 1000:
                raise TTSError(
                    f"Chatterbox produced invalid audio for slide {slide_num}"
                )

            audio_files[slide_num] = output_path

        return audio_files
