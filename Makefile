IMAGE_NAME ?= livekit-integration:dev
NAMESPACE ?= voice-agent-system

.PHONY: install test lint docker-build deploy delete

install:
	pip install -e .[dev]

test:
	pytest

lint:
	ruff check .

docker-build:
	docker build -t $(IMAGE_NAME) .

deploy:
	kubectl apply -f k8s/namespace.yaml
	kubectl apply -f k8s/redis.yaml
	kubectl apply -f k8s/livekit-configmap.yaml
	kubectl apply -f k8s/livekit.yaml
	kubectl apply -f k8s/agent-secret.yaml
	kubectl apply -f k8s/agent.yaml
	kubectl apply -f k8s/demo.yaml

delete:
	kubectl delete namespace $(NAMESPACE)
