#!/usr/bin/env bash
# One command: creates a virtual environment, installs the free dependencies, starts DocOcto.
set -e
cd "$(dirname "$0")"
if [ ! -d .venv ]; then python3 -m venv .venv || { echo "Run: sudo apt install python3-venv python3-pip"; exit 1; }; fi
. .venv/bin/activate
pip install -q -r requirements.txt
python scripts/get_vendor.py || true
python app.py
