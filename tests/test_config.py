from __future__ import annotations

from voice_agent.config import Settings


def test_settings_from_env(monkeypatch):
    monkeypatch.setenv("LIVEKIT_URL", "ws://livekit:7880")
    monkeypatch.setenv("LIVEKIT_API_KEY", "devkey")
    monkeypatch.setenv("LIVEKIT_API_SECRET", "secret")
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://127.0.0.1:12434/v1")
    monkeypatch.setenv("OLLAMA_MODEL", "gemma4:e4b")

    settings = Settings.from_env()

    assert settings.livekit_url == "ws://livekit:7880"
    assert settings.livekit_api_url == "http://livekit:7880"
    assert settings.ollama_base_url == "http://127.0.0.1:12434/v1"
    assert settings.ollama_model == "gemma4:e4b"
    assert settings.kokoro_service_url == "http://127.0.0.1:18080"
    assert settings.inference_stt_model == "deepgram/nova-3"
    assert settings.kokoro_voice == "af_heart"
    assert settings.agent_name == "local-voice-agent"
