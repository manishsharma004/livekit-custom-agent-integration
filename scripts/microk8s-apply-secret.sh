#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SECRET_FILE="${SECRET_FILE:-$ROOT_DIR/k8s/agent-secret.yaml}"

if [[ ! -f "$SECRET_FILE" ]]; then
  echo "secret file not found: $SECRET_FILE" >&2
  exit 1
fi

microk8s kubectl apply -f "$SECRET_FILE"
