"""Core video generation pipeline orchestrating all stages."""

from __future__ import annotations

import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional

from .config import Config
from .conversion import convert_pptx_to_images
from .tts.base import TTSProvider
from .video import assemble_video


def run_pipeline(
    config: Config,
    presentation_path: str,
    narration_script: list[dict[str, Any]],
    tts_provider: TTSProvider,
    output_path: str | None = None,
    on_progress: Optional[Callable[[str], None]] = None,
) -> str:
    """Run the full presentation-to-video pipeline.

    Args:
        config: Server configuration.
        presentation_path: Path to the PPTX file.
        narration_script: List of {slide_number, narration_text} dicts.
        tts_provider: Configured TTS provider instance.
        output_path: Optional output MP4 path.
        on_progress: Optional progress callback.

    Returns:
        Path to the generated MP4 video.
    """
    pptx = Path(presentation_path)
    if not pptx.exists():
        raise FileNotFoundError(f"Presentation not found: {presentation_path}")

    # Determine output path
    if output_path:
        out = Path(output_path)
    else:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        out = config.default_output_dir / f"presentation_{timestamp}.mp4"
    out.parent.mkdir(parents=True, exist_ok=True)

    tmp_dir = Path(tempfile.mkdtemp(prefix="mcp_video_"))
    try:
        # Stage 1: Convert PPTX to slide images
        if on_progress:
            on_progress("Converting presentation to slide images...")
        slides_dir = tmp_dir / "slides"
        slide_images = convert_pptx_to_images(
            pptx_path=str(pptx),
            output_dir=slides_dir,
            libreoffice_path=config.libreoffice_path,
            poppler_path=config.poppler_path,
        )
        if on_progress:
            on_progress(f"Rendered {len(slide_images)} slides")

        # Stage 2: Synthesize audio
        audio_dir = tmp_dir / "audio"
        audio_files = tts_provider.synthesize(
            narration_script=narration_script,
            output_dir=audio_dir,
            on_progress=on_progress,
        )
        if on_progress:
            on_progress(f"Synthesized audio for {len(audio_files)} slides")

        # Stage 3: Assemble video
        assemble_video(
            slide_images=slide_images,
            audio_files=audio_files,
            output_path=out,
            on_progress=on_progress,
        )

        if on_progress:
            on_progress(f"Video saved to {out}")

        return str(out)

    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
