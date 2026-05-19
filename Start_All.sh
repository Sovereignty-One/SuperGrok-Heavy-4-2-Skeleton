#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

echo ""
echo "=============================================="
echo "   SuperGrok Enterprise -- Start All          "
echo "=============================================="
echo ""
echo "  Port topology:"
echo "    :9897  Python Bridge (python3_bridge.py)  -- backend AI + brain memory"
echo "    :9898  KODER frontend (server_9898.js) -- HTML + WS + Coder UI"
echo "    :9899  Node.js Unified_Server.js          -- REST proxy / relay"
echo ""

# -- Load .env -------------------------------------------------

if [ -f .env ]; then
  set -a; source .env; set +a
  echo "  Config: .env loaded"
else
  echo "  WARNING: .env not found -- copy .env.example to .env and add your keys"
fi

# -- Check Python ----------------------------------------------

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

# -- 9897: Python bridge (backend AI + brain) ------------------

if [ "${HAVE_PYTHON}" = "1" ] && [ -f python3_bridge.py ]; then
  echo "  Starting Python Bridge on :9897..."
  SG_PORT=9897 python3 python3_bridge.py &
  PY_PID=$!
  echo "  Python bridge PID: $PY_PID"
else
  PY_PID=""
fi

# -- 9898: KODER frontend (server_9898.js) ---------------------

FRONTEND_JS="server_9898.js"
if [ -f "${FRONTEND_JS}" ]; then
  echo "  Starting KODER frontend on :9898..."
  PORT=9898 node "${FRONTEND_JS}" &
  FRONTEND_PID=$!
  echo "  Frontend PID: $FRONTEND_PID"
else
  FRONTEND_PID=""
  echo "  WARNING: ${FRONTEND_JS} not found -- frontend (:9898) skipped"
fi

# -- 9899: Node unified server (REST proxy / relay) ------------

echo "  Starting Unified_Server.js on :9899..."
node Unified_Server.js &
SERVER_PID=$!
echo "  Node PID: $SERVER_PID"

# -- Wait for Node health --------------------------------------

echo "  Waiting for Node server (:9899)..."
for i in $(seq 1 10); do
  if curl -sf http://127.0.0.1:9899/health >/dev/null 2>&1; then
    echo "  Health :9899: OK"
    break
  fi
  sleep 0.5
done

# -- Wait for Frontend health ----------------------------------

if [ -n "${FRONTEND_PID}" ]; then
  for i in $(seq 1 6); do
    if curl -sf http://127.0.0.1:9898/health >/dev/null 2>&1; then
      echo "  Health :9898: OK"
      break
    fi
    sleep 0.5
  done
fi

# -- Wait for Python health ------------------------------------

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
echo "  Open the dashboard in your browser:"
echo "    http://127.0.0.1:9898  <-- KODER frontend (what you see)"
echo "    http://127.0.0.1:9897  <-- Python bridge direct (AI + brain)"
echo "  Logs:  ./logs/access.jsonl"
echo ""
echo "  Features: AI Bridge + Brain Memory + Movie + Music + 3D CGI Avatar"
echo "  No Google + No Meta + 127.0.0.1 Only + a-shell/iSH Compatible"
echo "  Sentinel: active (PID $SENTINEL_PID)"
echo "  Press Ctrl+C to stop"
echo ""

wait $SERVER_PID
