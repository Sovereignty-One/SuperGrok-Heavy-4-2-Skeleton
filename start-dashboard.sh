#!/bin/sh
# SuperGrok Heavy 4.2 - Dashboard Launcher
# Runs python3_bridge.py on port 9897.
# Works on iSH (Alpine Linux / iOS), macOS, and Linux.
# No Node.js required.

SG_PORT="${SG_PORT:-9897}"
BRIDGE="python3_bridge.py"
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

# Locate dashboard HTML and stage in HOME for bridge auto-discovery
HTML=""
for candidate in \
    "$SCRIPT_DIR/Sghv119-local.html" \
    "$HOME/Sghv119-local.html" \
    "$SCRIPT_DIR/SGHv119.html" \
    "$HOME/SGHv119.html"; do
    if [ -f "$candidate" ]; then
        HTML="$candidate"
        break
    fi
done
if [ -z "$HTML" ]; then
    for f in "$SCRIPT_DIR"/Sgh*.html "$HOME"/Sgh*.html \
             "$SCRIPT_DIR"/SGH*.html "$HOME"/SGH*.html \
             "$SCRIPT_DIR"/SuperGrok*.html "$HOME"/SuperGrok*.html; do
        if [ -f "$f" ]; then
            HTML="$f"
            break
        fi
    done
fi
if [ -n "$HTML" ]; then
    echo "+ Dashboard: $HTML"
    if [ "$HTML" != "$HOME/SGHv119.html" ] && [ -w "$HOME" ]; then
        cp "$HTML" "$HOME/SGHv119.html" 2>/dev/null || true
    fi
else
    echo "WARNING: No dashboard HTML found - bridge will show status page."
    echo "  Copy SGHv119.html to $HOME/ and rerun."
fi

echo ""
echo "  Open Safari:   http://127.0.0.1:$SG_PORT"
echo "  Health check:  http://127.0.0.1:$SG_PORT/api/health"
echo "  WebSocket:     ws://127.0.0.1:$SG_PORT"
echo ""
echo "  Optional API keys:"
echo "    export ANTHROPIC_API_KEY=sk-ant-..."
echo "    export OPENAI_API_KEY=sk-..."
echo "    export GROK_API_KEY=xai-..."
echo ""
echo "Press Ctrl+C to stop."
echo ""

cd "$SCRIPT_DIR"
export SG_PORT
exec python3 "$BRIDGE"
