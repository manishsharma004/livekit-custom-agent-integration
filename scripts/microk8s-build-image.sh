#!/usr/bin/env bash
set -euo pipefail

IMAGE_NAME="${IMAGE_NAME:-livekit-integration:dev}"

cd "$(dirname "$0")/.."
docker build -t "$IMAGE_NAME" .
