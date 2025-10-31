#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
PYTHONPATH="${PYTHONPATH:-}"
export PYTHONPATH="$PWD/📚 Enhanced RAG & Knowledge Graph:$PYTHONPATH"
export LOCAL_ST_MODEL_PATH="$PWD/models/all-MiniLM-L6-v2"
lsof -nP -iTCP:8011 -sTCP:LISTEN -t | xargs -r kill || true
exec "$PWD/.venv/bin/python" -m uvicorn "api.app:app" \
  --app-dir "📚 Enhanced RAG & Knowledge Graph" \
  --host 127.0.0.1 --port 8011 --reload
