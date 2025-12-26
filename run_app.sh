#!/bin/bash
# Script to run the Farmer CLI application

# Navigate to the project directory
cd "$(dirname "$0")"

# Activate the virtual environment if it exists
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
fi

# Run the application
python src/cli.py
