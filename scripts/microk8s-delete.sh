#!/usr/bin/env bash
set -euo pipefail

NAMESPACE="${NAMESPACE:-voice-agent-system}"

microk8s kubectl delete namespace "$NAMESPACE" --ignore-not-found
