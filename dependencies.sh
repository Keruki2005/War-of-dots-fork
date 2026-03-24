#!/bin/bash
# Create a Python virtual environment named venv

if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "Virtual environment 'venv' created."
else
    echo "Virtual environment 'venv' already exists."
fi

# Activate the virtual environment
# On macOS/Linux
if [ "$OSTYPE" = "darwin" ] || [ "$OSTYPE" = "linux-gnu" ]; then
    source venv/bin/activate
elif [ "$OSTYPE" = "cygwin" ] || [ "$OSTYPE" = "msys" ] || [ "$OSTYPE" = "win32" ]; then
    # On Windows
    venv\Scripts\activate
else
    echo "Unsupported OS: $OSTYPE"
    exit 1
fi

# Upgrade pip, setuptools, and wheel
pip install --upgrade pip setuptools wheel

# Install dependencies
pip install pygame-ce orjson perlin-noise numpy

# Instructions for usage
echo "
To activate the virtual environment after creating it, use the following command:
 - For macOS/Linux: source venv/bin/activate
 - For Windows: venv\Scripts\activate
"