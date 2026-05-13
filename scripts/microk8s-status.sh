#!/usr/bin/env bash
set -euo pipefail

NAMESPACE="${NAMESPACE:-voice-agent-system}"

microk8s kubectl get all -n "$NAMESPACE"

NODE_IP="$(microk8s kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}')"

echo
echo "Demo UI: http://${NODE_IP}:30080"
echo "LiveKit WS: ws://${NODE_IP}:7880"
