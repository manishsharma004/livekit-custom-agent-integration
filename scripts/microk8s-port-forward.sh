#!/usr/bin/env bash
set -euo pipefail

NAMESPACE="${NAMESPACE:-voice-agent-system}"
LOCAL_PORT="${LOCAL_PORT:-8000}"

echo "Direct access is available at http://<microk8s-node-ip>:30080"
echo "Starting port-forward fallback on http://127.0.0.1:${LOCAL_PORT}"

microk8s kubectl port-forward -n "$NAMESPACE" service/voice-demo "$LOCAL_PORT":8000
