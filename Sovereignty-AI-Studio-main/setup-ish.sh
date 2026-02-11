#!/bin/sh

# Setup script for Sovereignty-AI-Studio on iSH Alpine Linux
echo "Updating package index..."
apk update

echo "Installing system dependencies..."
apk add --no-cache python3 py3-pip redis git openssh tzdata ffmpeg gcc musl-dev

echo "Upgrading pip..."
pip install --upgrade pip

echo "Installing Python dependencies..."
pip install -r requirements.txt

echo "Setup complete."
echo "To run the application:"
echo "1. Start Redis: redis-server"
echo "2. Run the app: python .devcontainer/Sovereignty_Gate.py"