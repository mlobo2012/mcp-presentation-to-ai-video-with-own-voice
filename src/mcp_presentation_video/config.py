"""Configuration loading for the MCP presentation video server."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path


_CONFIG_DIR = Path.home() / ".mcp-presentation-video"
_DEFAULT_OUTPUT_DIR = Path.home() / "Videos" / "presentations"


@dataclass
class Config:
    """Server configuration loaded from env vars and optional config file."""

    openai_api_key: str = ""
    chatterbox_python: str = (
        "/Users/marco/AI Heroes website/"
        "presentation-to-ai-video-with-your-voice/.venvs/chatterbox/bin/python"
    )
    chatterbox_script: str = (
        "/Users/marco/AI Heroes website/"
        "presentation-to-ai-video-with-your-voice/scripts/chatterbox_local_tts.py"
    )
    libreoffice_path: str = "/Applications/LibreOffice.app/Contents/MacOS/soffice"
    poppler_path: str = "/opt/homebrew/bin"
    voices_dir: Path = field(default_factory=lambda: _CONFIG_DIR / "voices")
    default_output_dir: Path = field(default_factory=lambda: _DEFAULT_OUTPUT_DIR)

    @classmethod
    def load(cls) -> Config:
        """Load config from env vars, then overlay optional JSON config file."""
        cfg = cls()

        # JSON config file
        config_file = _CONFIG_DIR / "config.json"
        if config_file.exists():
            with open(config_file) as f:
                data = json.load(f)
            for key, val in data.items():
                if hasattr(cfg, key):
                    field_val = getattr(cfg, key)
                    if isinstance(field_val, Path):
                        setattr(cfg, key, Path(val))
                    else:
                        setattr(cfg, key, val)

        # Env vars override everything
        env_map = {
            "OPENAI_API_KEY": "openai_api_key",
            "CHATTERBOX_TTS_PYTHON": "chatterbox_python",
            "CHATTERBOX_TTS_SCRIPT": "chatterbox_script",
            "LIBREOFFICE_PATH": "libreoffice_path",
            "POPPLER_PATH": "poppler_path",
            "MCP_VOICES_DIR": "voices_dir",
            "MCP_OUTPUT_DIR": "default_output_dir",
        }
        for env_key, attr in env_map.items():
            val = os.environ.get(env_key)
            if val:
                field_val = getattr(cfg, attr)
                if isinstance(field_val, Path):
                    setattr(cfg, attr, Path(val))
                else:
                    setattr(cfg, attr, val)

        return cfg
