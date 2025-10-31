#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
echo "Hello KG: test@example.com https://example.com Example email domain." > /tmp/a.txt
curl -s -X POST "http://127.0.0.1:8011/rag/ingest" -H "Content-Type: application/json" -d '{"path":"/tmp/a.txt","save_index":true}' | { command -v jq >/dev/null && jq . || cat; }
curl -s "http://127.0.0.1:8011/rag/search?query=example%20email&mode=hybrid&alpha=0.6&top_k=3" | { command -v jq >/dev/null && jq '.items[0]' || cat; }
curl -s http://127.0.0.1:8011/index/info | { command -v jq >/dev/null && jq . || cat; }
