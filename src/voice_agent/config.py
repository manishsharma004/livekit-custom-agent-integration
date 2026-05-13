from __future__ import annotations

import os
from dataclasses import dataclass
from urllib.parse import urlparse, urlunparse


@dataclass(frozen=True)
class Settings:
    livekit_url: str
    livekit_api_url: str
    livekit_public_url: str
    livekit_api_key: str
    livekit_api_secret: str
    ollama_base_url: str
    ollama_model: str
    ollama_api_key: str
    kokoro_service_url: str
    agent_name: str = "local-voice-agent"
    inference_stt_model: str = "deepgram/nova-3"
    kokoro_voice: str = "af_heart"
    kokoro_lang_code: str = "a"
    kokoro_speed: float = 1.0
    demo_port: int = 8000

    @classmethod
    def from_env(cls) -> "Settings":
        livekit_url = _require("LIVEKIT_URL")
        return cls(
            livekit_url=livekit_url,
            livekit_api_url=os.getenv("LIVEKIT_API_URL", _to_http_url(livekit_url)),
            livekit_public_url=os.getenv("LIVEKIT_PUBLIC_URL", livekit_url),
            livekit_api_key=_require("LIVEKIT_API_KEY"),
            livekit_api_secret=_require("LIVEKIT_API_SECRET"),
            ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:12434/v1"),
            ollama_model=os.getenv("OLLAMA_MODEL", "gemma4:e4b"),
            ollama_api_key=os.getenv("OLLAMA_API_KEY", "ollama"),
            kokoro_service_url=os.getenv("KOKORO_SERVICE_URL", "http://127.0.0.1:18080"),
            agent_name=os.getenv("AGENT_NAME", "local-voice-agent"),
            inference_stt_model=os.getenv("INFERENCE_STT_MODEL", "deepgram/nova-3"),
            kokoro_voice=os.getenv("KOKORO_VOICE", "af_heart"),
            kokoro_lang_code=os.getenv("KOKORO_LANG_CODE", "a"),
            kokoro_speed=float(os.getenv("KOKORO_SPEED", "1.0")),
            demo_port=int(os.getenv("DEMO_PORT", "8000")),
        )


def _require(name: str) -> str:
    value = os.getenv(name)
    if value:
        return value
    raise RuntimeError(f"Missing required environment variable: {name}")


def _to_http_url(url: str) -> str:
    parsed = urlparse(url)
    scheme_map = {"ws": "http", "wss": "https"}
    scheme = scheme_map.get(parsed.scheme, parsed.scheme)
    return urlunparse(parsed._replace(scheme=scheme))
