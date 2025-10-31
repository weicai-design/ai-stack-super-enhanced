#!/usr/bin/env bash
# Run on the OFFLINE target machine after copying offline_bundle.tar.gz into the repo root.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
BUNDLE="$ROOT_DIR/offline_bundle.tar.gz"
TMP_DIR="$ROOT_DIR/offline_bundle_tmp"

if [ ! -f "$BUNDLE" ]; then
  echo "offline_bundle.tar.gz not found in $ROOT_DIR"
  exit 1
fi

echo "Extracting bundle..."
rm -rf "$TMP_DIR"
mkdir -p "$TMP_DIR"
tar xzf "$BUNDLE" -C "$TMP_DIR"

WHEEL_DIR="$TMP_DIR/offline_bundle/wheels"
MODEL_SRC_DIR="$TMP_DIR/offline_bundle/models"

echo "Installing wheels from $WHEEL_DIR"
# Create and use a venv in .venv to avoid touching system site-packages
VENV_DIR="$ROOT_DIR/.venv"
if [ ! -d "$VENV_DIR" ]; then
  echo "Creating virtual environment at $VENV_DIR"
  python3 -m venv "$VENV_DIR"
fi
# shellcheck disable=SC1090
source "$VENV_DIR/bin/activate"

# Use --no-index to enforce offline install
pip install --no-index --find-links "$WHEEL_DIR" --upgrade $(ls "$WHEEL_DIR"/*.whl 2>/dev/null || true)

echo "Installed packages into venv at $VENV_DIR (activate with: source $VENV_DIR/bin/activate)"

if [ -d "$MODEL_SRC_DIR" ]; then
  echo "Installing model files to ./models"
  mkdir -p "$ROOT_DIR/models"
  cp -R "$MODEL_SRC_DIR"/* "$ROOT_DIR/models/"
  echo "Models copied to $ROOT_DIR/models"
fi

echo "Offline install complete."
echo "If you included a sentence-transformers model, set environment variable LOCAL_ST_MODEL_PATH to point to ./models/<model-name> and restart the service."
