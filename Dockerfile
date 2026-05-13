FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./

RUN python - <<'PY' > /tmp/requirements.txt
import tomllib

with open("pyproject.toml", "rb") as file_handle:
    project = tomllib.load(file_handle)["project"]

for dependency in project.get("dependencies", []):
    print(dependency)
PY

RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY src ./src

RUN pip install --no-cache-dir --no-deps .

CMD ["python", "-m", "voice_agent.agent", "start"]
