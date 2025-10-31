#!/usr/bin/env bash
# Prepare an offline bundle on a machine WITH Internet access.
# Produces: offline_bundle.tar.gz containing wheels/requirements.txt and optional model folder

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
OUT_DIR="$ROOT_DIR/offline_bundle"
WHEEL_DIR="$OUT_DIR/wheels"
REQ_FILE="$OUT_DIR/requirements.txt"

mkdir -p "$WHEEL_DIR"

echo "Preparing offline bundle in $OUT_DIR"

# Base required packages (tweak as needed for your platform)
cat > "$REQ_FILE" <<'REQ'
sentence-transformers
transformers
huggingface-hub
numpy
faiss-cpu
torch
fastapi
uvicorn[standard]
requests
REQ

echo "Using pip to download wheels into $WHEEL_DIR"


# Use a domestic PyPI mirror if desired. Uncomment and edit the --index-url line.
# For example, use TUNA (Tsinghua) mirror: https://pypi.tuna.tsinghua.edu.cn/simple
PIP_EXTRA_ARGS=()
# Example to use TUNA mirror:
# PIP_EXTRA_ARGS=(--index-url "https://pypi.tuna.tsinghua.edu.cn/simple")

# Expand safely even when array is empty
if [ ${#PIP_EXTRA_ARGS[@]} -gt 0 ]; then
  python3 -m pip download -r "$REQ_FILE" -d "$WHEEL_DIR" "${PIP_EXTRA_ARGS[@]}"
else
  python3 -m pip download -r "$REQ_FILE" -d "$WHEEL_DIR"
fi

# Platform-specific helper: if you have pre-downloaded wheels (torch/faiss) or
# have direct wheel URLs, set TORCH_WHEEL_URL and/or FAISS_WHEEL_URL env vars
# before running this script. This is helpful on macOS where torch wheels can be
# platform-specific.
if [ -n "${TORCH_WHEEL_URL:-}" ]; then
  echo "Downloading torch wheel from TORCH_WHEEL_URL"
  curl -fSL "$TORCH_WHEEL_URL" -o "$WHEEL_DIR/$(basename $TORCH_WHEEL_URL)"
fi

if [ -n "${FAISS_WHEEL_URL:-}" ]; then
  echo "Downloading faiss wheel from FAISS_WHEEL_URL"
  curl -fSL "$FAISS_WHEEL_URL" -o "$WHEEL_DIR/$(basename $FAISS_WHEEL_URL)"
fi

# Small platform detection note (for user's convenience)
UNAME_S=$(uname -s)
UNAME_M=$(uname -m)
echo "Platform detected: $UNAME_S / $UNAME_M"

echo "Optional: download sentence-transformers model files to include in bundle"
echo "If you want to include the model, set MODEL_NAME (eg: all-MiniLM-L6-v2) and run this script again."

if [ -n "${MODEL_NAME:-}" ]; then
  MODEL_DIR="$OUT_DIR/models/$MODEL_NAME"
  mkdir -p "$MODEL_DIR"
  echo "Downloading SentenceTransformer model: $MODEL_NAME"
  python3 - <<PY
from sentence_transformers import SentenceTransformer
import os
name = os.environ.get('MODEL_NAME')
m = SentenceTransformer(name)
m.save('$MODEL_DIR')
print('Saved model to $MODEL_DIR')
PY
fi

echo "Creating archive offline_bundle.tar.gz"
cd "$OUT_DIR/.."
tar czf offline_bundle.tar.gz "$(basename "$OUT_DIR")"

echo "Offline bundle created: $OUT_DIR/../offline_bundle.tar.gz"
echo "Transfer this file to the offline target machine and run scripts/offline_install.sh there."
