"""MCP stdio server with tool definitions for presentation-to-video generation."""

from __future__ import annotations

import mcp.server.stdio
import mcp.types as types
from mcp.server import Server

from .config import Config
from .pipeline import run_pipeline
from .tts.chatterbox import ChatterboxProvider
from .tts.openai_tts import OpenAITTSProvider
from .voices import get_voice, list_voices, register_voice

server = Server("mcp-presentation-video")


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """Return the list of available tools."""
    return [
        types.Tool(
            name="generate_video_with_voice",
            description=(
                "Generate a narrated video from a PowerPoint presentation using voice cloning "
                "(Chatterbox TTS). Requires a registered voice profile. The narration script "
                "must be provided - this tool does NOT generate narration."
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
                    "accent": {
                        "type": "string",
                        "description": "Optional accent guidance (e.g., 'british', 'australian')",
                    },
                    "output_path": {
                        "type": "string",
                        "description": "Optional output MP4 file path",
                    },
                },
                "required": ["presentation_path", "narration_script", "voice_name"],
            },
        ),
        types.Tool(
            name="generate_video",
            description=(
                "Generate a narrated video from a PowerPoint presentation using OpenAI TTS. "
                "Uses standard AI voices (no voice cloning). Requires OPENAI_API_KEY. "
                "The narration script must be provided - this tool does NOT generate narration."
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
                    "output_path": {
                        "type": "string",
                        "description": "Optional output MP4 file path",
                    },
                },
                "required": ["presentation_path", "narration_script"],
            },
        ),
        types.Tool(
            name="register_voice",
            description=(
                "Register a voice profile for use with voice-cloned video generation. "
                "Copies the voice sample to persistent storage for reuse."
            ),
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
            description="List all registered voice profiles available for voice-cloned video generation.",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
    ]


@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent]:
    """Handle tool invocations."""
    args = arguments or {}
    config = Config.load()

    try:
        if name == "generate_video_with_voice":
            return await _generate_video_with_voice(config, args)
        elif name == "generate_video":
            return await _generate_video(config, args)
        elif name == "register_voice":
            return _register_voice(config, args)
        elif name == "list_voices":
            return _list_voices(config)
        else:
            return [types.TextContent(type="text", text=f"Unknown tool: {name}")]
    except Exception as exc:
        return [types.TextContent(type="text", text=f"Error: {exc}")]


async def _generate_video_with_voice(
    config: Config, args: dict
) -> list[types.TextContent]:
    """Handle generate_video_with_voice tool call."""
    voice_name = args["voice_name"]
    voice = get_voice(config.voices_dir, voice_name)

    provider = ChatterboxProvider(
        voice_sample_path=voice["sample_path"],
        python_path=config.chatterbox_python,
        script_path=config.chatterbox_script,
        accent=args.get("accent"),
    )

    output = run_pipeline(
        config=config,
        presentation_path=args["presentation_path"],
        narration_script=args["narration_script"],
        tts_provider=provider,
        output_path=args.get("output_path"),
    )
    return [types.TextContent(type="text", text=f"Video generated: {output}")]


async def _generate_video(
    config: Config, args: dict
) -> list[types.TextContent]:
    """Handle generate_video tool call."""
    provider = OpenAITTSProvider(
        api_key=config.openai_api_key,
        voice=args.get("tts_voice", "nova"),
    )

    output = run_pipeline(
        config=config,
        presentation_path=args["presentation_path"],
        narration_script=args["narration_script"],
        tts_provider=provider,
        output_path=args.get("output_path"),
    )
    return [types.TextContent(type="text", text=f"Video generated: {output}")]


def _register_voice(config: Config, args: dict) -> list[types.TextContent]:
    """Handle register_voice tool call."""
    meta = register_voice(
        voices_dir=config.voices_dir,
        name=args["name"],
        voice_sample_path=args["voice_sample_path"],
        description=args.get("description", ""),
    )
    return [
        types.TextContent(
            type="text",
            text=f"Voice '{meta['name']}' registered. Sample stored at: {meta['sample_path']}",
        )
    ]


def _list_voices(config: Config) -> list[types.TextContent]:
    """Handle list_voices tool call."""
    import json

    voices = list_voices(config.voices_dir)
    if not voices:
        return [types.TextContent(type="text", text="No voice profiles registered yet.")]

    return [types.TextContent(type="text", text=json.dumps(voices, indent=2))]


def main():
    """Run the MCP server via stdio transport."""
    import asyncio
    from mcp.server import NotificationOptions
    from mcp.server.models import InitializationOptions

    async def _run() -> None:
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="mcp-presentation-video",
                    server_version="0.1.0",
                    capabilities=server.get_capabilities(
                        NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )

    asyncio.run(_run())
