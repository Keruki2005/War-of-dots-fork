#!/bin/bash

# War of Dots - Dependency Installation Script
# This script installs all required Python 3 dependencies and sets up the game

set -e

echo "================================"
echo "War of Dots - Setup Script"
echo "================================"
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed. Please install Python 3.9 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo "✓ Found Python 3: $PYTHON_VERSION"
echo ""

# Check Python version meets minimum requirement (3.9+)
REQUIRED_VERSION="3.9"
if ! python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)"; then
    echo "ERROR: Python 3.9 or higher is required. You have $PYTHON_VERSION"
    exit 1
fi

echo "✓ Python version meets requirements (3.9+)"
echo ""

# Update pip, setuptools, and wheel
echo "Updating pip, setuptools, and wheel..."
python3 -m pip install --upgrade pip setuptools wheel
echo "✓ Updated pip, setuptools, and wheel"
echo ""

# Install dependencies
echo "Installing War of Dots dependencies..."
echo "  - pygame-ce (Community Edition)"
echo "  - orjson"
echo "  - perlin-noise"
echo "  - numpy"
echo ""

python3 -m pip install pygame-ce orjson perlin-noise numpy

if [ $? -eq 0 ]; then
    echo ""
    echo "✓ All dependencies installed successfully!"
    echo ""
    echo "================================"
    echo "Setup Complete!"
    echo "================================"
    echo ""
    echo "To play War of Dots:"
    echo "  1. Start the server:  python3 wod_server.py"
    echo "  2. Start clients:     python3 wod_client.py (on each player's machine)"
    echo "  3. Configure the server with number of players and port"
    echo "  4. Connect clients using server IP and port"
    echo "  5. Press 'p' to unpause and start playing!"
    echo ""
    echo "For more information, see README.md"
    echo ""
else
    echo ""
    echo "ERROR: Failed to install dependencies"
    exit 1
fi
