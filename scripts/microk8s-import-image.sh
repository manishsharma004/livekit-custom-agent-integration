#!/usr/bin/env bash
set -euo pipefail

IMAGE_NAME="${IMAGE_NAME:-livekit-integration:dev}"

if ! command -v microk8s >/dev/null 2>&1; then
  echo "microk8s is not installed or not on PATH" >&2
  exit 1
fi

docker image inspect "$IMAGE_NAME" >/dev/null
docker save "$IMAGE_NAME" | microk8s ctr image import -
