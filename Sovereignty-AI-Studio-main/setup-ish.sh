#!/bin/sh
# Sovereignty AI Studio — iSH Setup (clean, working Feb 2026)

# Pin to v3.12 FIRST — only once, Node 14 runs clean
echo "https://dl-cdn.alpinelinux.org/alpine/v3.12/main" > /etc/apk/repositories
echo "https://dl-cdn.alpinelinux.org/alpine/v3.12/community" >> /etc/apk/repositories

set -e  # Bail on any error

echo "=== Sovereignty AI Studio — iSH Setup ==="

echo "Installing deps..."
apk update && apk add --no-cache \
  python3 py3-pip \
  nodejs npm \
  redis git openssh tzdata ffmpeg gcc musl-dev curl

echo "Python setup..."
pip install --user --upgrade pip
pip install --user -r requirements.txt
pip install --user hypercorn  # ASGI server

echo "Node bridge..."
cd node-bridge && npm ci --no-audit --no-fund && cd ..

echo "=== Done ==="
echo ""
echo "Launch:"
echo "  redis-server &"
echo "  PYTHONPATH=.:./backend hypercorn weather_dashboard:app --bind 0.0.0.0:9898 &"
echo "  cd node-bridge && npm start"
echo ""
echo "All APIs on 9898: http://localhost:9898/health"
echo "Node bridge proxies on 9898: http://localhost:9898/api/weather"
echo "Type the port yourself—iSH auto-links fuck up to 0000."
echo "If crash: pkill hypercorn; rerun the hypercorn line."
