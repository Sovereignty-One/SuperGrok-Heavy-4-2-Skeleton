#!/bin/sh
# Setup script for Sovereignty-AI-Studio on iSH / Alpine Linux
# Works with iSH, Python Code Pad, and standard Alpine.

set -e

echo "=== Sovereignty AI Studio — iSH Setup ==="
echo ""

echo "[1/5] Updating package index..."
apk update

echo "[2/5] Installing system dependencies..."
apk add --no-cache \
  python3 py3-pip \
  nodejs npm \
  redis git openssh tzdata ffmpeg gcc musl-dev curl

echo "[3/5] Upgrading pip..."
pip install --upgrade pip

echo "[4/5] Installing Python dependencies..."
pip install -r requirements.txt
pip install hypercorn   # Quart ASGI server

echo "[5/5] Installing Node.js bridge..."
cd node-bridge && npm ci && cd ..

echo ""
echo "=== Setup complete ==="
echo ""
echo "Quick start:"
echo "  ./start-all.sh          # launch all services"
echo ""
echo "Or run individually:"
echo "  redis-server &"
echo "  PYTHONPATH=.:./backend hypercorn weather_dashboard:app --bind 0.0.0.0:9898 &"
echo "  cd node-bridge && npm start"
echo ""
echo "The Node bridge unifies all backends on port 3001:"
echo "  http://localhost:3001/health           – bridge health"
echo "  http://localhost:3001/api/weather      – weather API"
echo "  http://localhost:3001/api/forecast     – forecast API"
echo "  http://localhost:3001/api/v1/...       – FastAPI backend"
echo "  ws://localhost:3001/ws/alerts          – real-time alerts"