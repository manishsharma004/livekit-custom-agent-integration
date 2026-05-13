#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
NAMESPACE="${NAMESPACE:-voice-agent-system}"
SKIP_BUILD="${SKIP_BUILD:-false}"

if ! command -v microk8s >/dev/null 2>&1; then
  echo "microk8s is not installed or not on PATH" >&2
  exit 1
fi

if [[ "$SKIP_BUILD" != "true" ]]; then
  "$ROOT_DIR/scripts/microk8s-build-image.sh"
  "$ROOT_DIR/scripts/microk8s-import-image.sh"
fi

"$ROOT_DIR/scripts/microk8s-apply-secret.sh"

microk8s kubectl apply -k "$ROOT_DIR/k8s"
microk8s kubectl rollout restart deployment/voice-agent -n "$NAMESPACE"
microk8s kubectl rollout restart deployment/voice-demo -n "$NAMESPACE"
microk8s kubectl rollout status deployment/redis -n "$NAMESPACE" --timeout=180s
microk8s kubectl rollout status deployment/livekit -n "$NAMESPACE" --timeout=180s
microk8s kubectl rollout status deployment/voice-agent -n "$NAMESPACE" --timeout=180s
microk8s kubectl rollout status deployment/voice-demo -n "$NAMESPACE" --timeout=180s
