"""Thin MCP stdio server that delegates all processing to the remote API."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import mcp.server.stdio
import mcp.types as types
from mcp.server import Server

from .api_client import APIClient
from .config import get_api_key, get_api_url, get_download_dir

server = Server("mcp-presentation-video-remote")


def _client() -> APIClient:
    return APIClient(base_url=get_api_url(), api_key=get_api_key())


def _download_path(job_id: str) -> Path:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    return get_download_dir() / f"presentation_{ts}_{job_id}.mp4"


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="generate_video_with_voice",
            description=(
                "Generate a narrated video from a PowerPoint presentation using voice cloning "
                "(Chatterbox TTS) via the remote API server. Requires a registered voice profile."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "presentation_path": {
                        "type": "string",
                        "description": "Absolute path to the PPTX file",
                    },
                    "narration_script": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "slide_number": {"type": "integer"},
                                "narration_text": {"type": "string"},
                            },
                            "required": ["slide_number", "narration_text"],
                        },
                        "description": "Narration text for each slide",
                    },
                    "voice_name": {
                        "type": "string",
                        "description": "Name of a registered voice profile",
                    },
                },
                "required": ["presentation_path", "narration_script", "voice_name"],
            },
        ),
        types.Tool(
            name="generate_video",
            description=(
                "Generate a narrated video from a PowerPoint presentation using OpenAI TTS "
                "via the remote API server."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "presentation_path": {
                        "type": "string",
                        "description": "Absolute path to the PPTX file",
                    },
                    "narration_script": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "slide_number": {"type": "integer"},
                                "narration_text": {"type": "string"},
                            },
                            "required": ["slide_number", "narration_text"],
                        },
                        "description": "Narration text for each slide",
                    },
                    "tts_voice": {
                        "type": "string",
                        "description": "OpenAI voice: alloy, echo, fable, onyx, nova, shimmer",
                        "default": "nova",
                    },
                },
                "required": ["presentation_path", "narration_script"],
            },
        ),
        types.Tool(
            name="register_voice",
            description="Upload a voice sample to the remote server for voice cloning.",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Unique name for this voice profile",
                    },
                    "voice_sample_path": {
                        "type": "string",
                        "description": "Absolute path to a voice sample audio file (WAV preferred)",
                    },
                    "description": {
                        "type": "string",
                        "description": "Optional description of the voice",
                    },
                },
                "required": ["name", "voice_sample_path"],
            },
        ),
        types.Tool(
            name="list_voices",
            description="List all registered voice profiles on the remote server.",
            inputSchema={"type": "object", "properties": {}},
        ),
    ]


@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent]:
    args = arguments or {}
    try:
        if name == "generate_video_with_voice":
            return await _generate_video_with_voice(args)
        elif name == "generate_video":
            return await _generate_video(args)
        elif name == "register_voice":
            return _register_voice(args)
        elif name == "list_voices":
            return _list_voices()
        else:
            return [types.TextContent(type="text", text=f"Unknown tool: {name}")]
    except Exception as exc:
        return [types.TextContent(type="text", text=f"Error: {exc}")]


async def _generate_video_with_voice(args: dict) -> list[types.TextContent]:
    client = _client()

    # Create job
    result = client.create_job(
        pptx_path=args["presentation_path"],
        narration_script=args["narration_script"],
        mode="voice_clone",
        voice_name=args["voice_name"],
    )
    job_id = result["job_id"]

    # Poll until done
    progress_msgs = []
    def on_progress(msg: str) -> None:
        progress_msgs.append(msg)

    client.poll_until_done(job_id, on_progress=on_progress)

    # Download
    dest = _download_path(job_id)
    client.download_video(job_id, dest)

    return [types.TextContent(type="text", text=f"Video generated and downloaded: {dest}")]


async def _generate_video(args: dict) -> list[types.TextContent]:
    client = _client()

    result = client.create_job(
        pptx_path=args["presentation_path"],
        narration_script=args["narration_script"],
        mode="standard",
        tts_voice=args.get("tts_voice", "nova"),
    )
    job_id = result["job_id"]

    progress_msgs = []
    def on_progress(msg: str) -> None:
        progress_msgs.append(msg)

    client.poll_until_done(job_id, on_progress=on_progress)

    dest = _download_path(job_id)
    client.download_video(job_id, dest)

    return [types.TextContent(type="text", text=f"Video generated and downloaded: {dest}")]


def _register_voice(args: dict) -> list[types.TextContent]:
    client = _client()
    result = client.upload_voice(
        audio_path=args["voice_sample_path"],
        name=args["name"],
        description=args.get("description", ""),
    )
    return [types.TextContent(type="text", text=f"Voice '{result['name']}' registered on remote server.")]


def _list_voices() -> list[types.TextContent]:
    client = _client()
    voices = client.list_voices()
    if not voices:
        return [types.TextContent(type="text", text="No voice profiles registered yet.")]
    return [types.TextContent(type="text", text=json.dumps(voices, indent=2))]


def main():
    """Run the thin MCP client via stdio transport."""
    import asyncio
    from mcp.server import NotificationOptions
    from mcp.server.models import InitializationOptions

    async def _run() -> None:
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="mcp-presentation-video-remote",
                    server_version="0.1.0",
                    capabilities=server.get_capabilities(
                        NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )

    asyncio.run(_run())
