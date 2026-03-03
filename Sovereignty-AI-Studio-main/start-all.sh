#!/bin/sh
# start-all.sh — Launch every service for Sovereignty AI Studio
# Works on iSH, Linux, macOS, and CI.

set -e

BRIDGE_PORT="${NODE_BRIDGE_PORT:-9898}"
WEATHER_PORT="${WEATHER_PORT:-9898}"
BACKEND_PORT="${BACKEND_PORT:-9898}"

cleanup() {
  echo ""
  echo "[stop] shutting down..."
  [ -n "$REDIS_PID" ]   && kill "$REDIS_PID"   2>/dev/null
  [ -n "$WEATHER_PID" ] && kill "$WEATHER_PID" 2>/dev/null
  [ -n "$BRIDGE_PID" ]  && kill "$BRIDGE_PID"  2>/dev/null
  exit 0
}
trap cleanup INT TERM

# --- Redis (optional — skip if already running) ---
if command -v redis-server >/dev/null 2>&1; then
  if ! redis-cli ping >/dev/null 2>&1; then
    echo "[start] redis on port 6379"
    redis-server --daemonize yes
    REDIS_PID=$(cat /var/run/redis.pid 2>/dev/null || echo "")
  else
    echo "[skip]  redis already running"
  fi
else
  echo "[skip]  redis not installed"
fi

# --- Quart weather dashboard ---
echo "[start] weather dashboard on port $WEATHER_PORT"
PYTHONPATH=.:./backend hypercorn weather_dashboard:app \
  --bind "0.0.0.0:$WEATHER_PORT" &
WEATHER_PID=$!
sleep 2

# --- Node.js bridge ---
echo "[start] node-bridge on port $BRIDGE_PORT"
cd node-bridge
WEATHER_URL="http://localhost:$WEATHER_PORT" \
BACKEND_URL="http://localhost:$BACKEND_PORT" \
NODE_BRIDGE_PORT="$BRIDGE_PORT" \
  node server.js &
BRIDGE_PID=$!
cd ..
sleep 1

echo ""
echo "=== All services running ==="
echo "  Bridge:   http://localhost:$BRIDGE_PORT/health"
echo "  Weather:  http://localhost:$WEATHER_PORT/api/weather?city=London"
echo "  WS:       ws://localhost:$BRIDGE_PORT/ws/alerts"
echo ""
echo "Press Ctrl+C to stop all services."

# Keep the script alive
wait
