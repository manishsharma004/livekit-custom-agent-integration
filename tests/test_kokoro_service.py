from __future__ import annotations

from voice_agent import kokoro_service


def test_kokoro_device_reads_env(monkeypatch):
    monkeypatch.setenv("KOKORO_SERVICE_DEVICE", " cpu ")

    assert kokoro_service._kokoro_device() == "cpu"


def test_should_fallback_to_cpu_for_unavailable_cuda():
    exc = RuntimeError("CUDA requested but not available")

    assert kokoro_service._should_fallback_to_cpu("cuda", exc) is True


def test_should_not_fallback_for_other_devices():
    exc = RuntimeError("CUDA requested but not available")

    assert kokoro_service._should_fallback_to_cpu("cpu", exc) is False
    assert kokoro_service._should_fallback_to_cpu(None, exc) is False


def test_create_pipeline_retries_with_cpu_when_cuda_unavailable():
    calls: list[tuple[str, str | None]] = []

    class FakePipeline:
        def __init__(self, *, lang_code: str, device: str | None) -> None:
            calls.append((lang_code, device))
            if device == "cuda":
                raise RuntimeError("CUDA requested but not available")

    pipeline = kokoro_service._create_pipeline(FakePipeline, lang_code="a", device="cuda")

    assert isinstance(pipeline, FakePipeline)
    assert calls == [("a", "cuda"), ("a", "cpu")]
