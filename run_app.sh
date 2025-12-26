#!/bin/bash
# Script to run the Farmer CLI application

# Navigate to the project directory
cd "$(dirname "$0")"

# Activate the virtual environment if it exists
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
fi

# Ensure src layout is on PYTHONPATH for local runs
export PYTHONPATH="$(pwd)/src${PYTHONPATH:+:$PYTHONPATH}"

# Run the application
python -m farmer_cli
