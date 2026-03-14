# MCP Presentation-to-Video with Voice Cloning

An MCP (Model Context Protocol) server that converts PowerPoint presentations into narrated AI videos. Supports voice cloning via Chatterbox TTS or standard voices via OpenAI TTS.

## Architecture

```
User's Machine                        Your Server (Mac mini)
┌─────────────────────┐               ┌────────────────────────────┐
│ Claude Desktop/Code  │               │ FastAPI + Cloudflare Tunnel│
│        │             │    HTTPS      │        │                   │
│  Thin MCP Client ────┼──────────────►│  API Server                │
│  (pip install)       │               │  ├── LibreOffice           │
│  - uploads PPTX      │               │  ├── Chatterbox TTS (GPU) │
│  - polls status      │               │  ├── OpenAI TTS            │
│  - downloads MP4     │               │  └── MoviePy + FFmpeg      │
└─────────────────────┘               └────────────────────────────┘
```

Users install a lightweight MCP package. Heavy processing runs on the server.

## Quick Start (End User)

### 1. Install

```bash
pip install mcp-presentation-video
```

### 2. Get an API key

Request one from the server admin.

### 3. Configure Claude Desktop

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "presentation-video": {
      "command": "mcp-presentation-video-remote",
      "env": {
        "PRESENTATION_VIDEO_API_KEY": "pv_live_your_key_here",
        "PRESENTATION_VIDEO_API_URL": "https://your-server.trycloudflare.com"
      }
    }
  }
}
```

### 4. Configure Claude Code

```bash
claude mcp add presentation-video \
  -e PRESENTATION_VIDEO_API_KEY="pv_live_your_key_here" \
  -e PRESENTATION_VIDEO_API_URL="https://your-server.trycloudflare.com" \
  -- mcp-presentation-video-remote
```

### 5. Use it

Tell Claude: "Register my voice using this sample" and provide a .wav file.
Then: "Turn this presentation into a video with my voice" and attach a .pptx.

## MCP Tools

| Tool | Description |
|------|-------------|
| `generate_video_with_voice` | PPTX → narrated video using your cloned voice (Chatterbox) |
| `generate_video` | PPTX → narrated video using OpenAI TTS |
| `register_voice` | Upload a voice sample for voice cloning |
| `list_voices` | List registered voice profiles |

## Server Setup

### Prerequisites

- macOS with Apple Silicon (for Chatterbox MPS acceleration)
- LibreOffice: `brew install --cask libreoffice`
- Poppler: `brew install poppler`
- FFmpeg: `brew install ffmpeg`
- Cloudflare Tunnel: `brew install cloudflare/cloudflare/cloudflared`
- Python 3.11+
- Chatterbox TTS venv (see `scripts/bootstrap_chatterbox.sh` in the original repo)

### Install

```bash
git clone https://github.com/mlobo2012/mcp-presentation-to-ai-video-with-own-voice.git
cd mcp-presentation-to-ai-video-with-own-voice
python -m venv .venv
.venv/bin/pip install -e ".[server]"
```

### Run

```bash
# Set OpenAI API key (for standard TTS mode)
export OPENAI_API_KEY=sk-...

# Start API server
.venv/bin/python -m uvicorn mcp_presentation_video.api.app:app --host 127.0.0.1 --port 8100

# Start Cloudflare tunnel (in another terminal)
cloudflared tunnel --url http://localhost:8100
```

### API Key Management

```bash
# Generate an API key
python scripts/manage_keys.py create --name "user-name"

# List keys
python scripts/manage_keys.py list

# Revoke a key
python scripts/manage_keys.py revoke --id <key_id>
```

### launchd (auto-start on boot)

See the project docs for sample launchd plist files to run the API server and tunnel as persistent services.

## Security

- **Zero open ports** — Cloudflare Tunnel makes an outbound connection only
- **API key auth** — bcrypt-hashed keys, revocable
- **Rate limiting** — 60 requests/minute per key
- **Input validation** — PPTX must be valid ZIP, audio validated
- **Isolated jobs** — each job runs in its own temp directory
- **No user input in shell commands** — all paths are server-generated

## License

MIT
