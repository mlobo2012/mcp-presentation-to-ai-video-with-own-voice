# CLAUDE.md

## Project

MCP server for converting PowerPoint presentations into narrated AI videos with voice cloning.

## Stack

- Python 3.11+
- MCP SDK (`mcp` package) for stdio server
- FastAPI (for future API server, not needed in Phase 1)
- Chatterbox TTS (local voice cloning, runs in separate venv)
- OpenAI TTS API (standard voice mode)
- LibreOffice (PPTX → PDF conversion)
- Poppler / pdf2image (PDF → PNG)
- MoviePy + FFmpeg (video assembly)

## Architecture (Phase 1 - Local)

Single MCP stdio server that runs the full pipeline locally. No remote API yet.

## Commands

```bash
# Install in development mode
pip install -e .

# Run MCP server (stdio mode - Claude Desktop/Code spawns this)
python -m mcp_presentation_video

# Run tests
pytest tests/
```

## Key Paths

- Chatterbox venv: `/Users/marco/AI Heroes website/presentation-to-ai-video-with-your-voice/.venvs/chatterbox/bin/python`
- Chatterbox script: `/Users/marco/AI Heroes website/presentation-to-ai-video-with-your-voice/scripts/chatterbox_local_tts.py`
- LibreOffice: `/Applications/LibreOffice.app/Contents/MacOS/soffice`
- Poppler: `/opt/homebrew/bin`
- Voice profiles dir: `~/.mcp-presentation-video/voices/`
- Default output dir: `~/Videos/presentations/`

## Environment Variables

```
OPENAI_API_KEY - Required for standard TTS mode
CHATTERBOX_TTS_PYTHON - Path to chatterbox venv python (defaults to the path above)
CHATTERBOX_TTS_SCRIPT - Path to chatterbox runner script (defaults to the path above)
```
