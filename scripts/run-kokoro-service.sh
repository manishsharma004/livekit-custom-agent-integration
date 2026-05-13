#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
HOST="${KOKORO_SERVICE_HOST:-127.0.0.1}"
PORT="${KOKORO_SERVICE_PORT:-18080}"

cd "$ROOT_DIR"
python -m uvicorn voice_agent.kokoro_service:app --host "$HOST" --port "$PORT"
