# MCP Presentation-to-Video with Voice Cloning

**Generate AI-narrated videos from your PowerPoint presentations — using your own voice.**

Turn any .pptx into a professional narrated MP4. Register a 30-second voice sample, and every video sounds like you gave the presentation yourself. Works with Claude Desktop, Claude Code, and Claude Cowork via MCP.

Free to use. No credit card required.

## Quick Start

### 1. Get a free API key

Sign up at [ai-heroes.co/free-tools/mcp-presentation-video](https://www.ai-heroes.co/en-gb/free-tools/mcp-presentation-video) — you'll receive your API key by email.

### 2. Install the MCP client

```bash
pip install mcp-presentation-video
```

### 3. Add to Claude

**Claude Desktop** — add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "presentation-video": {
      "command": "python",
      "args": ["-m", "mcp_presentation_video"],
      "env": {
        "MCP_API_KEY": "YOUR_API_KEY"
      }
    }
  }
}
```

**Claude Code:**

```bash
claude mcp add presentation-video -- python -m mcp_presentation_video --api-key YOUR_API_KEY
```

## First Use

1. **Register your voice:** Tell Claude _"Register my voice using the WAV file at ./my-voice-sample.wav with the name 'my-name'."_ You only need to do this once.
2. **Create a video:** Tell Claude _"Turn the deck at ./slides.pptx into a narrated video using my registered voice 'my-name'."_

That's it — Claude handles the narration script, voice synthesis, and video encoding.

## What You Can Do

| Tool | What it does |
|------|-------------|
| `generate_video_with_voice` | PowerPoint + narration script + your registered voice → MP4 narrated in your voice |
| `generate_video` | PowerPoint + narration script → MP4 with a standard AI voice |
| `register_voice` | Upload a WAV voice sample to create a reusable voice profile |
| `list_voices` | List all your registered voice profiles |

## Use Cases

- **Safety documentation** — turn safety briefings into narrated videos teams can watch asynchronously
- **Training content** — convert training decks into video modules narrated by the trainer
- **Sales decks** — send prospects a narrated walk-through instead of a static PDF
- **Onboarding** — turn onboarding slides into welcome videos narrated by a real team member
- **Product demos** — generate narrated product walk-throughs from feature decks
- **Client updates** — send clients a narrated video summary instead of another email attachment

## Setup Guides

- [MCP Presentation-to-Video Server](https://www.ai-heroes.co/en-gb/free-tools/mcp-presentation-video) — full feature overview and setup
- [Claude Code setup guide](https://www.ai-heroes.co/en-gb/free-tools/mcp-presentation-video/claude-code) — for developers and automation workflows
- [Claude Cowork setup guide](https://www.ai-heroes.co/en-gb/free-tools/mcp-presentation-video/claude-cowork) — for knowledge workers

## Advanced: Self-Hosting the Server

If you want to run the processing server yourself instead of using the hosted service:

### Prerequisites

- macOS with Apple Silicon (recommended for GPU acceleration)
- LibreOffice: `brew install --cask libreoffice`
- Poppler: `brew install poppler`
- FFmpeg: `brew install ffmpeg`
- Cloudflare Tunnel: `brew install cloudflare/cloudflare/cloudflared`
- Python 3.11+

### Install

```bash
git clone https://github.com/mlobo2012/mcp-presentation-to-ai-video-with-own-voice.git
cd mcp-presentation-to-ai-video-with-own-voice
python -m venv .venv
.venv/bin/pip install -e ".[server]"
```

### Run

```bash
# Start API server
.venv/bin/python -m uvicorn mcp_presentation_video.api.app:app --host 127.0.0.1 --port 8100

# Start Cloudflare tunnel (in another terminal)
cloudflared tunnel --url http://localhost:8100
```

### API Key Management

```bash
python scripts/manage_keys.py create --name "user-name"
python scripts/manage_keys.py list
python scripts/manage_keys.py revoke --id <key_id>
```

## Security

- **Zero open ports** — Cloudflare Tunnel makes an outbound connection only
- **API key auth** — bcrypt-hashed keys, revocable
- **Rate limiting** — 60 requests/minute per key
- **Input validation** — PPTX must be valid ZIP, audio validated
- **Isolated jobs** — each job runs in its own temp directory

## License

MIT
