#!/usr/bin/env bash
# Start the FastAPI server and a cloudflared quick tunnel.
# Usage: ./scripts/start_server.sh

set -euo pipefail

cleanup() {
    echo ""
    echo "Shutting down..."
    # Kill child processes
    if [[ -n "${SERVER_PID:-}" ]]; then
        kill "$SERVER_PID" 2>/dev/null || true
    fi
    if [[ -n "${TUNNEL_PID:-}" ]]; then
        kill "$TUNNEL_PID" 2>/dev/null || true
    fi
    wait 2>/dev/null
    echo "Done."
}
trap cleanup SIGINT SIGTERM EXIT

echo "=== Presentation Video API Server ==="
echo ""

# Start FastAPI server
echo "Starting API server on http://0.0.0.0:8000 ..."
python -m mcp_presentation_video.api.app &
SERVER_PID=$!

# Wait a moment for server to start
sleep 2

# Check if server is running
if ! kill -0 "$SERVER_PID" 2>/dev/null; then
    echo "ERROR: Server failed to start"
    exit 1
fi

echo "API server running (PID: $SERVER_PID)"
echo ""

# Start cloudflared tunnel
if command -v cloudflared &>/dev/null; then
    echo "Starting cloudflared tunnel..."
    cloudflared tunnel --url http://localhost:8000 &
    TUNNEL_PID=$!
    echo "Tunnel running (PID: $TUNNEL_PID)"
    echo ""
    echo "Wait for the tunnel URL to appear above ^^^"
else
    echo "cloudflared not found — skipping tunnel."
    echo "Install with: brew install cloudflare/cloudflare/cloudflared"
    echo ""
    echo "Server is available locally at: http://localhost:8000"
fi

echo ""
echo "Admin key location: ~/.mcp-presentation-video/admin_key.txt"
echo "Press Ctrl+C to stop."
echo ""

# Wait for any child to exit
wait
