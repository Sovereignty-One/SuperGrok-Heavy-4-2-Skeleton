#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check for required environment
if [ ! -f .env ]; then
  echo "Error: .env file not found. Copy .env.example to .env and configure it."
  echo "  cp .env.example .env"
  exit 1
fi

echo "=== Sovereignty AI Studio - Deployment ==="
echo "Building and starting all services..."

# Build and start services
docker compose build
docker compose up -d

echo ""
echo "=== Services started ==="
echo "Backend:  http://localhost:${BACKEND_PORT:-9898}"
echo "Frontend: http://localhost:${FRONTEND_PORT:-3000}"
echo ""
echo "View logs:   docker compose logs -f"
echo "Stop:        docker compose down"