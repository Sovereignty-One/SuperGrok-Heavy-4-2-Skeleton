#!/usr/bin/env bash
set -euo pipefail
cd “$(dirname “$0”)”

echo “”
echo “╔══════════════════════════════════════════════╗”
echo “║   SuperGrok Enterprise — Start All          ║”
echo “╚══════════════════════════════════════════════╝”
echo “”

# ── Check Node ────────────────────────────────────────

if ! command -v node &>/dev/null; then
echo “ERROR: Node.js not found. Install Node 18+”; exit 1
fi
NODE_V=$(node -e “process.stdout.write(process.version)”)
echo “  Node:   $NODE_V”

# ── Install ws if needed ──────────────────────────────

if [ ! -d node_modules/ws ]; then
echo “  Installing ws…”
npm install –omit=dev –silent 2>/dev/null || npm install ws –silent
fi

# ── Load .env ─────────────────────────────────────────

if [ -f .env ]; then
set -a; source .env; set +a
echo “  Config: .env loaded”
else
echo “  WARNING: .env not found — copy .env.example to .env and add your keys”
fi

# ── Start unified server ──────────────────────────────

echo “  Starting unified_server.js…”
node unified_server.js &
SERVER_PID=$!
echo “  PID: $SERVER_PID”

# ── Wait for health ───────────────────────────────────

echo “  Waiting for server…”
for i in $(seq 1 10); do
if curl -sf http://127.0.0.1:9000/health >/dev/null 2>&1; then
echo “  Health: OK”
break
fi
sleep 0.5
done

echo “”
echo “  Open SuperGrok_v13_COMPLETE.html in your browser”
echo “  Ports: 9000 (primary) 9898 (bridge) 8443 (auth)”
echo “  Logs:  ./logs/access.jsonl”
echo “”
echo “  Press Ctrl+C to stop”
echo “”

wait $SERVER_PID
