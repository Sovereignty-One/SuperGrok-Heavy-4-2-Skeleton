#!/bin/bash

# SuperGrok Heavy 4.2 - Dashboard Launcher
# Starts Unified_Server.js on port 9898 with FullDashboard.html

set -e

echo "╔══════════════════════════════════════════════════╗"
echo "║  SuperGrok Heavy 4.2 - Dashboard Launcher        ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ ERROR: Node.js is not installed"
    echo "   Please install Node.js 18+ first"
    exit 1
fi

NODE_VERSION=$(node --version)
echo "✓ Node.js: $NODE_VERSION"

# Check if files exist
if [ ! -f "Unified_Server.js" ]; then
    echo "❌ ERROR: Unified_Server.js not found"
    echo "   Run this script from the project root directory"
    exit 1
fi

if [ ! -f "FullDashboard.html" ]; then
    echo "❌ ERROR: FullDashboard.html not found"
    echo "   Dashboard file is missing from project root"
    exit 1
fi

echo "✓ Unified_Server.js found"
echo "✓ FullDashboard.html found"

# Check if dependencies are installed
if [ ! -d "node_modules" ]; then
    echo ""
    echo "📦 Installing dependencies..."
    npm install
fi

# Create logs directory if it doesn't exist
mkdir -p logs

echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║  Starting Server on Port 9898                    ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""
echo "Dashboard will be available at:"
echo "  • http://127.0.0.1:9898/"
echo "  • http://127.0.0.1:9898/dashboard"
echo "  • http://127.0.0.1:9898/FullDashboard.html"
echo ""
echo "API Endpoints:"
echo "  • http://127.0.0.1:9898/health"
echo "  • http://127.0.0.1:9898/api/*"
echo ""
echo "WebSocket:"
echo "  • ws://127.0.0.1:9898"
echo ""
echo "Press Ctrl+C to stop the server"
echo "═══════════════════════════════════════════════════"
echo ""

# Start the server
node Unified_Server.js
