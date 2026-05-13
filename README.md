# LiveKit Integration

This project is a demo voice agent system for local Kubernetes development with LiveKit.

## Architecture

- `voice-agent`: Python LiveKit Agents service using LiveKit Inference for STT, a host-side Kokoro service for TTS, and local Ollama for LLM inference.
- `livekit`: self-hosted LiveKit server deployed in the cluster for local development.
- `redis`: backing store required by LiveKit server.
- `voice-demo`: a lightweight FastAPI app that serves a browser demo and creates room tokens.
- `kokoro-service`: a standalone FastAPI service you run on the host so it can use your local ROCm/PyTorch setup.

The expected local flow is:

1. Run a local Kubernetes cluster.
2. Deploy Redis and LiveKit into that cluster.
3. Build the voice-agent image locally.
4. Update the agent secret manifest with your deployment values.
5. Deploy the agent workload.
6. Open the demo web app, join a room, and talk to the agent from your browser.

## Repository layout

- `src/voice_agent`: agent application code.
- `tests`: minimal test coverage.
- `k8s`: Kubernetes manifests for local deployment.
- `scripts`: MicroK8s management scripts for the demo.

## Local Python development

Create an environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

Create your env file:

```bash
cp .env.example .env
```

Then start the agent locally against the cluster-hosted LiveKit server:

```bash
python -m voice_agent.agent dev
```

For local development, the default LLM endpoint is your Ollama server at `http://127.0.0.1:12434/v1` using model `gemma4:e4b`.
Speech recognition uses LiveKit Inference through your LiveKit credentials, and speech synthesis is delegated to a separate host-side Kokoro service, so no OpenAI key is required.

## Kokoro Service

The Kubernetes agent no longer runs Kokoro locally. Instead, it calls a host-side HTTP service at `KOKORO_SERVICE_URL`, which defaults to `http://127.0.0.1:18080`.

This is the intended path when your ROCm setup is already working on the host and you do not want to reproduce it inside MicroK8s.

### Start the host service

Create a Python environment on the Linux host where ROCm and PyTorch already work, then install the extra dependency set for the host service:

```bash
python -m venv .venv-kokoro
source .venv-kokoro/bin/activate
pip install -e '.[kokoro-service]'
```

If the host has a working ROCm or CUDA-backed PyTorch setup and you want Kokoro to prefer that GPU, set:

```bash
export KOKORO_SERVICE_DEVICE=cuda
```

On CPU-only hosts, leave `KOKORO_SERVICE_DEVICE` unset or set it to `cpu`.

Then start the service:

```bash
./scripts/run-kokoro-service.sh
```

By default it binds to `127.0.0.1:18080`, which works with the current `hostNetwork: true` configuration on the agent pod.

## Demo app

The demo web app is served by the same Python image and provides:

- a browser UI for joining a room
- participant token generation
- explicit agent dispatch into the room
- local Ollama-backed LLM inference for responses
- host-side Kokoro speech synthesis

The main entry points are:

- `python -m voice_agent.agent start`
- `python -m uvicorn voice_agent.demo:app --host 0.0.0.0 --port 8000`

## MicroK8s deployment

This repository is set up for a local demo on MicroK8s.

### Prerequisites

- MicroK8s is installed and running.
- Docker is installed locally.
- Ollama is running on the host at `http://127.0.0.1:12434` with model `gemma4:e4b` available.
- ROCm-enabled PyTorch is available on the host for the separate Kokoro service.
- Browser access to `ws://127.0.0.1:7880` works from the same machine.

### One-time setup

Make the helper scripts executable:

```bash
chmod +x scripts/*.sh
```

### Deploy the demo

Edit `k8s/agent-secret.yaml` with your LiveKit and Ollama settings before deploy.

If you want to override the browser-facing LiveKit address, set it before deploy:

```bash
export LIVEKIT_PUBLIC_URL=ws://127.0.0.1:7880
```

If your Ollama endpoint or model name changes, override those too:

```bash
export OLLAMA_BASE_URL=http://127.0.0.1:12434/v1
export OLLAMA_MODEL=gemma4:e4b
```

Kokoro defaults for the demo are configured in `k8s/agent-secret.yaml`:

```text
KOKORO_SERVICE_URL=http://127.0.0.1:18080
KOKORO_VOICE=af_heart
KOKORO_LANG_CODE=a
```

Start the host-side Kokoro service before deploying or using the agent.

Build, import, apply `k8s/agent-secret.yaml`, and deploy everything:

```bash
./scripts/microk8s-deploy.sh
```

Check the cluster state:

```bash
./scripts/microk8s-status.sh
```

That script prints the direct demo and LiveKit URLs too.

The demo app is exposed through a MicroK8s NodePort on `30080`.

Open it directly at:

```text
http://<microk8s-node-ip>:30080
```

If you still want a local-only fallback tunnel, use:

```bash
./scripts/microk8s-port-forward.sh
```

### Script usage

Build the application image:

```bash
./scripts/microk8s-build-image.sh
```

Import the image into the MicroK8s image store:

```bash
./scripts/microk8s-import-image.sh
```

Apply or refresh the runtime secret from `k8s/agent-secret.yaml`:

```bash
./scripts/microk8s-apply-secret.sh
```

Tail logs for a component:

```bash
./scripts/microk8s-logs.sh agent
./scripts/microk8s-logs.sh demo
./scripts/microk8s-logs.sh livekit
```

Delete the whole demo namespace:

```bash
./scripts/microk8s-delete.sh
```

### Demo flow

1. Open the browser at `http://<microk8s-node-ip>:30080`.
2. If direct NodePort access is blocked on your machine, start `./scripts/microk8s-port-forward.sh` and use `http://127.0.0.1:8000` instead.
3. Enter a room name and participant name, or leave them blank.
4. Click `Join Demo` and allow microphone access.
5. The backend creates the room, dispatches the agent, and the page joins with your token.
6. Speak to the agent after the room connects. Speech transcription uses LiveKit Inference, speech synthesis goes through the host-side Kokoro service, and response generation uses local Ollama Gemma.

## Generic local Kubernetes deployment

Build the image:

```bash
docker build -t livekit-integration:dev .
```

If you are using `kind`, load it into the cluster:

```bash
kind load docker-image livekit-integration:dev
```

Create the runtime secret from the example file:

```bash
cp k8s/agent-secret.example.yaml k8s/agent-secret.yaml
```

Edit `k8s/agent-secret.yaml` with your LiveKit and Ollama settings.

Deploy everything:

```bash
make deploy
```

Check resources:

```bash
kubectl get pods -n voice-agent-system
```

## Notes for local clusters

LiveKit is WebRTC infrastructure, so local Kubernetes networking matters.

- `hostNetwork: true` is enabled for the LiveKit pod because RTC traffic needs direct port access.
- `hostNetwork: true` is also enabled for the `voice-agent` pod so it can reach your host-local Ollama server at `127.0.0.1:12434` and your host-local Kokoro service at `127.0.0.1:18080` from inside MicroK8s.
- The `voice-agent` pod must keep `dnsPolicy: ClusterFirstWithHostNet` so it can still resolve the in-cluster `livekit` service while using host networking.
- A single LiveKit pod per node is the safe baseline.
- For MicroK8s on a single local machine, `ws://127.0.0.1:7880` is the expected browser URL unless you override it.
- For `kind`, `k3d`, or `minikube`, you may need extra port mappings or a dedicated node setup for browser-based testing.
- The provided manifests are for local development, not production hardening.

## Next steps

- Replace the single-agent prompt with task-specific workflows and tools.
- Move secrets to a proper secret manager for anything beyond local use.
