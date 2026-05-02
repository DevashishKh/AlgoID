#!/usr/bin/env bash
set -e

echo "==> Installing Python dependencies..."
pip install -r requirements.txt

echo "==> Initialising database..."
python database_setup.py

echo "==> Build complete."
