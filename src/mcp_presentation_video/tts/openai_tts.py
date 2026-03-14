"""OpenAI TTS provider for standard voice synthesis."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from openai import OpenAI

from .base import ProgressCallback, TTSError, TTSProvider

VALID_VOICES = {"alloy", "echo", "fable", "onyx", "nova", "shimmer"}


class OpenAITTSProvider(TTSProvider):
    """Text-to-speech via OpenAI's TTS API."""

    def __init__(self, api_key: str, voice: str = "nova", model: str = "tts-1"):
        if not api_key:
            raise TTSError("OPENAI_API_KEY is required for OpenAI TTS")
        if voice not in VALID_VOICES:
            raise TTSError(f"Invalid voice '{voice}'. Choose from: {', '.join(sorted(VALID_VOICES))}")

        self.client = OpenAI(api_key=api_key)
        self.voice = voice
        self.model = model

    def synthesize(
        self,
        narration_script: list[dict[str, Any]],
        output_dir: Path,
        on_progress: ProgressCallback = None,
    ) -> dict[int, Path]:
        """Synthesize audio for each slide using OpenAI TTS."""
        output_dir.mkdir(parents=True, exist_ok=True)
        audio_files: dict[int, Path] = {}
        total = len(narration_script)

        for i, entry in enumerate(narration_script, start=1):
            slide_num = entry["slide_number"]
            text = entry["narration_text"]
            output_path = output_dir / f"slide_{slide_num:03d}.wav"

            if on_progress:
                on_progress(f"Synthesizing audio for slide {slide_num} ({i}/{total})")

            try:
                response = self.client.audio.speech.create(
                    model=self.model,
                    voice=self.voice,
                    input=text,
                    response_format="wav",
                )
                response.write_to_file(str(output_path))
            except Exception as exc:
                raise TTSError(f"OpenAI TTS failed for slide {slide_num}: {exc}") from exc

            if not output_path.exists():
                raise TTSError(f"OpenAI TTS produced no output for slide {slide_num}")

            audio_files[slide_num] = output_path

        return audio_files
