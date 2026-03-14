"""Voice profile management for persistent voice sample storage."""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _voices_dir(base: Path) -> Path:
    base.mkdir(parents=True, exist_ok=True)
    return base


def register_voice(
    voices_dir: Path,
    name: str,
    voice_sample_path: str,
    description: str = "",
) -> dict[str, Any]:
    """Register a voice profile by copying the sample and storing metadata."""
    sample = Path(voice_sample_path)
    if not sample.exists():
        raise FileNotFoundError(f"Voice sample not found: {voice_sample_path}")

    profile_dir = _voices_dir(voices_dir) / name
    profile_dir.mkdir(parents=True, exist_ok=True)

    dest = profile_dir / f"sample{sample.suffix}"
    shutil.copy2(sample, dest)

    meta = {
        "name": name,
        "description": description,
        "sample_path": str(dest),
        "registered_at": datetime.now(timezone.utc).isoformat(),
    }
    meta_file = profile_dir / "meta.json"
    with open(meta_file, "w") as f:
        json.dump(meta, f, indent=2)

    return meta


def list_voices(voices_dir: Path) -> list[dict[str, Any]]:
    """List all registered voice profiles."""
    base = _voices_dir(voices_dir)
    voices = []
    for meta_file in sorted(base.glob("*/meta.json")):
        with open(meta_file) as f:
            voices.append(json.load(f))
    return voices


def get_voice(voices_dir: Path, name: str) -> dict[str, Any]:
    """Get a specific voice profile by name."""
    meta_file = voices_dir / name / "meta.json"
    if not meta_file.exists():
        raise FileNotFoundError(
            f"Voice profile '{name}' not found. Use list_voices to see available voices."
        )
    with open(meta_file) as f:
        return json.load(f)
