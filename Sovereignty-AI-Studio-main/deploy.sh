#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# --- Check for .env file ---
if [ ! -f .env ]; then
    echo "ERROR: .env file not found."
    echo "Copy .env.example to .env and fill in the required values:"
    echo "  cp .env.example .env"
    exit 1
fi

# --- Validate required env vars ---
source .env
for var in POSTGRES_PASSWORD SECRET_KEY; do
    if [ -z "${!var:-}" ]; then
        echo "ERROR: $var is not set in .env"
        exit 1
    fi
done

echo "==> Building and starting services..."
docker compose build
docker compose up -d

echo "==> Waiting for services to be healthy..."
docker compose ps

echo "==> Deployment complete."
echo "  Backend:  http://localhost:9898"
echo "  Frontend: http://localhost:3000"