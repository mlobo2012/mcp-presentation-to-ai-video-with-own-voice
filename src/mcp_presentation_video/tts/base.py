"""Abstract base class for TTS providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Callable, Optional


ProgressCallback = Optional[Callable[[str], None]]


class TTSError(Exception):
    """Error during TTS synthesis."""


class TTSProvider(ABC):
    """Base class for text-to-speech providers."""

    @abstractmethod
    def synthesize(
        self,
        narration_script: list[dict[str, Any]],
        output_dir: Path,
        on_progress: ProgressCallback = None,
    ) -> dict[int, Path]:
        """Synthesize audio for each slide.

        Args:
            narration_script: List of {slide_number, narration_text} dicts.
            output_dir: Directory to write audio files.
            on_progress: Optional callback for progress reporting.

        Returns:
            Mapping of slide_number to audio file path.
        """
