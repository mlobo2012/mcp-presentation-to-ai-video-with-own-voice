#!/bin/bash
# Watches the cloudflared tunnel log for new URLs and updates Claude Code MCP config.
# Run via launchd or cron after tunnel restart.

set -euo pipefail

TUNNEL_LOG="/Users/marco/.mcp-presentation-video/logs/tunnel.err"
CLAUDE_CONFIG="/Users/marco/.claude.json"
MCP_NAME="presentation-video-remote"

get_tunnel_url() {
    grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' "$TUNNEL_LOG" 2>/dev/null | tail -1
}

get_current_url() {
    python3 -c "
import json
with open('$CLAUDE_CONFIG') as f:
    d = json.load(f)
server = d.get('mcpServers', {}).get('$MCP_NAME', {})
print(server.get('env', {}).get('PRESENTATION_VIDEO_API_URL', ''))
" 2>/dev/null
}

update_url() {
    local new_url="$1"
    python3 -c "
import json
path = '$CLAUDE_CONFIG'
with open(path) as f:
    d = json.load(f)
if '$MCP_NAME' in d.get('mcpServers', {}):
    d['mcpServers']['$MCP_NAME']['env']['PRESENTATION_VIDEO_API_URL'] = '$new_url'
    with open(path, 'w') as f:
        json.dump(d, f, indent=2)
    print(f'Updated MCP URL to: $new_url')
else:
    print('MCP server not found in config')
"
}

# Wait for tunnel to be ready
for i in $(seq 1 30); do
    URL=$(get_tunnel_url)
    if [ -n "$URL" ]; then
        break
    fi
    sleep 2
done

if [ -z "$URL" ]; then
    echo "ERROR: Could not find tunnel URL after 60 seconds"
    exit 1
fi

CURRENT=$(get_current_url)

if [ "$URL" != "$CURRENT" ]; then
    echo "Tunnel URL changed: $CURRENT -> $URL"
    update_url "$URL"
else
    echo "Tunnel URL unchanged: $URL"
fi
