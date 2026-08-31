#!/bin/bash
# LeoCode TUI Launcher
# Launches the TypeScript frontend with the Python backend

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$SCRIPT_DIR"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
fi

# Build if needed
if [ ! -d "dist" ] || [ "src/index.tsx" -nt "dist/index.js" ]; then
    echo "Building..."
    npm run build
fi

# Launch the TUI
exec node dist/index.js "$@"
