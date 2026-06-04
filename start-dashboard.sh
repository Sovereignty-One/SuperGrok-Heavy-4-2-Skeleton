#!/bin/sh
# SuperGrok Heavy 4.2 - Dashboard Launcher
# Runs the standalone dashboard server on port 9898.
# Works on iSH (Alpine Linux / iOS), macOS, and Linux.
# No Node.js required.

PORT="${PORT:-9898}"
BRIDGE="bridge/serve_dashboard.py"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "SuperGrok Heavy 4.2 - Dashboard Launcher"
echo ""

# Check Python 3
if ! command -v python3 >/dev/null 2>&1; then
    echo "ERROR: python3 not found."
    echo "  iSH:    apk add python3"
    echo "  macOS:  brew install python3"
    echo "  Debian: apt-get install python3"
    exit 1
fi
echo "+ $(python3 --version)"

# Locate bridge script
if [ ! -f "$SCRIPT_DIR/$BRIDGE" ]; then
    echo "ERROR: $BRIDGE not found in $SCRIPT_DIR"
    exit 1
fi
echo "+ $BRIDGE found"

echo ""
echo "  Open Safari:   http://127.0.0.1:$PORT"
echo "  Health check:  http://127.0.0.1:$PORT/api/health"
echo "  WebSocket:     none in this mode"
echo ""
echo "  Optional API keys:"
echo "    export ANTHROPIC_API_KEY=sk-ant-..."
echo "    export OPENAI_API_KEY=sk-..."
echo "    export GROK_API_KEY=xai-..."
echo ""
echo "Press Ctrl+C to stop."
echo ""

cd "$SCRIPT_DIR"
export PORT
exec python3 "$BRIDGE"
