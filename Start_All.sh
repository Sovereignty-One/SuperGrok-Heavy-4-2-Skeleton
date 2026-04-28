#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

echo ""
echo "=============================================="
echo "   SuperGrok Enterprise -- Start All          "
echo "=============================================="
echo ""

# -- Load .env -------------------------------------------------

if [ -f .env ]; then
  set -a; source .env; set +a
  echo "  Config: .env loaded"
else
  echo "  WARNING: .env not found -- copy .env.example to .env and add your keys"
fi

# -- Check Python (optional — for Python bridge on :9897) ------

if command -v python3 &>/dev/null; then
  PY_V=$(python3 --version 2>&1)
  echo "  Python: $PY_V"
  HAVE_PYTHON=1
else
  echo "  Python: not found -- Python bridge (:9897) will be skipped"
  HAVE_PYTHON=0
fi

# -- Check Node ------------------------------------------------

if ! command -v node &>/dev/null; then
  echo "ERROR: Node.js not found. Install Node 18+"; exit 1
fi
NODE_V=$(node -e "process.stdout.write(process.version)")
echo "  Node:   $NODE_V"

# -- Install ws if needed --------------------------------------

if [ ! -d node_modules/ws ]; then
  echo "  Installing ws..."
  npm install --omit=dev --silent 2>/dev/null || npm install ws --silent
fi

# -- Start security sentinel -----------------------------------

echo "  Starting security sentinel..."
python3 security_sentinel.py --daemon &
SENTINEL_PID=$!
echo "  Sentinel PID: $SENTINEL_PID"

# -- Start Python bridge on :9897 (optional) -------------------

if [ "${HAVE_PYTHON}" = "1" ] && [ -f python3_bridge.py ]; then
  echo "  Starting Python bridge on :9897..."
  SG_PORT=9897 python3 python3_bridge.py &
  PY_PID=$!
  echo "  Python bridge PID: $PY_PID"
else
  PY_PID=""
fi

# -- Start Node unified server on :9899 ------------------------

echo "  Starting Unified_Server.js on :9899..."
node Unified_Server.js &
SERVER_PID=$!
echo "  Node PID: $SERVER_PID"

# -- Wait for Node health --------------------------------------

echo "  Waiting for Node server..."
for i in $(seq 1 10); do
  if curl -sf http://127.0.0.1:9899/health >/dev/null 2>&1; then
    echo "  Health :9899: OK"
    break
  fi
  sleep 0.5
done

# -- Wait for Python health (if started) -----------------------

if [ -n "${PY_PID}" ]; then
  for i in $(seq 1 6); do
    if curl -sf http://127.0.0.1:9897/api/health >/dev/null 2>&1; then
      echo "  Health :9897: OK"
      break
    fi
    sleep 0.5
  done
fi

echo ""
echo "  Port topology:"
echo "    :9897  Python bridge (python3_bridge.py) -- AI WS + brain memory"
echo "    :9898  KODER iOS file server              -- start from KODER app"
echo "    :9899  Node.js unified server             -- REST + WS relay"
echo ""
echo "  Open SGHv119.html via:  http://127.0.0.1:9897"
echo "  Or dashboard:           http://127.0.0.1:9899"
echo "  Logs:  ./logs/access.jsonl"
echo ""
echo "  Features: AI Bridge + Brain Memory + Movie + Music + 3D CGI Avatar"
echo "  No Google + No Meta + 127.0.0.1 Only + a-shell/iSH Compatible"
echo "  Sentinel: active (PID $SENTINEL_PID)"
echo "  Press Ctrl+C to stop"
echo ""

wait $SERVER_PID
