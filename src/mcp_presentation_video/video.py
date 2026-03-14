"""Video assembly using MoviePy - combines slide images with audio narration."""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional

from moviepy import AudioFileClip, ImageClip, concatenate_videoclips


def assemble_video(
    slide_images: list[Path],
    audio_files: dict[int, Path],
    output_path: Path,
    fps: int = 24,
    on_progress: Optional[Callable[[str], None]] = None,
) -> Path:
    """Assemble slide images and audio into a narrated MP4 video.

    Args:
        slide_images: Ordered list of slide image paths.
        audio_files: Mapping of slide_number (1-based) to audio file path.
        output_path: Path for the output MP4 file.
        fps: Video frame rate.
        on_progress: Optional progress callback.

    Returns:
        Path to the output MP4 file.
    """
    if on_progress:
        on_progress("Assembling video...")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    video_clips = []
    try:
        for i, slide_path in enumerate(slide_images, start=1):
            if i not in audio_files:
                continue

            audio_clip = AudioFileClip(str(audio_files[i]))
            img_clip = (
                ImageClip(str(slide_path))
                .with_duration(audio_clip.duration)
                .with_audio(audio_clip)
            )
            video_clips.append(img_clip)

        if not video_clips:
            raise RuntimeError("No video clips to assemble - check slide/audio alignment")

        final = concatenate_videoclips(video_clips, method="compose")
        final.write_videofile(
            str(output_path),
            fps=fps,
            codec="libx264",
            audio_codec="aac",
            logger=None,
        )
    finally:
        # Close all clips to release file handles
        for clip in video_clips:
            try:
                clip.close()
            except Exception:
                pass

    if on_progress:
        on_progress("Video assembly complete")

    return output_path
