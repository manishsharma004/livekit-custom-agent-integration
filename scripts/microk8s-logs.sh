#!/usr/bin/env bash
set -euo pipefail

NAMESPACE="${NAMESPACE:-voice-agent-system}"
TARGET="${1:-voice-agent}"

case "$TARGET" in
  agent)
    TARGET="voice-agent"
    ;;
  demo)
    TARGET="voice-demo"
    ;;
  livekit)
    TARGET="livekit"
    ;;
  redis)
    TARGET="redis"
    ;;
esac

microk8s kubectl logs deployment/"$TARGET" -n "$NAMESPACE" --follow
