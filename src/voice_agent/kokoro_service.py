from __future__ import annotations

import io
import logging
import threading
import wave
from uuid import uuid4

import numpy as np
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field

load_dotenv()

app = FastAPI(title="Kokoro Service", version="0.1.0")
logger = logging.getLogger(__name__)

_pipeline_cache: dict[tuple[str, str | None], object] = {}
_pipeline_lock = threading.Lock()


class SynthesizeRequest(BaseModel):
    text: str = Field(min_length=1, max_length=8000)
    voice: str = Field(default="af_heart", max_length=64)
    lang_code: str = Field(default="a", max_length=8)
    speed: float = Field(default=1.0, ge=0.5, le=2.0)
    media_type: str = Field(default="audio/pcm", max_length=64)


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/synthesize")
async def synthesize(payload: SynthesizeRequest) -> Response:
    pcm = await _run_in_thread(payload)
    audio_bytes, media_type = _encode_audio(pcm, payload.media_type)

    return Response(
        content=audio_bytes,
        media_type=media_type,
        headers={
            "X-Sample-Rate": "24000",
            "X-Num-Channels": "1",
            "X-Request-Id": str(uuid4()),
        },
    )


async def _run_in_thread(payload: SynthesizeRequest) -> bytes:
    import asyncio

    return await asyncio.to_thread(_synthesize_pcm, payload)


def _synthesize_pcm(payload: SynthesizeRequest) -> bytes:
    pipeline = _get_pipeline(payload.lang_code)
    pcm_chunks: list[np.ndarray] = []

    for result in pipeline(payload.text, voice=payload.voice, speed=payload.speed):
        audio = result.audio
        if audio is None:
            continue

        if hasattr(audio, "detach"):
            audio = audio.detach().float().cpu().numpy()

        chunk = np.asarray(audio, dtype=np.float32).reshape(-1)
        if chunk.size == 0:
            continue
        pcm_chunks.append(chunk)

    if not pcm_chunks:
        raise RuntimeError("Kokoro returned no audio")

    waveform = np.concatenate(pcm_chunks)
    waveform = np.clip(waveform, -1.0, 1.0)
    return (waveform * 32767.0).astype(np.int16).tobytes()


def _encode_audio(pcm: bytes, requested_media_type: str) -> tuple[bytes, str]:
    media_type = requested_media_type.strip().lower()

    if media_type in {"audio/pcm", "audio/raw", "application/octet-stream"}:
        return pcm, "audio/pcm"

    if media_type in {"audio/wav", "audio/wave", "audio/x-wav"}:
        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(24000)
            wav_file.writeframes(pcm)
        return buffer.getvalue(), "audio/wav"

    raise HTTPException(
        status_code=400,
        detail=(
            "Unsupported media_type. Supported values are audio/pcm and audio/wav. "
            f"Received: {requested_media_type}"
        ),
    )


def _get_pipeline(lang_code: str):
    from kokoro import KPipeline

    device = _kokoro_device()
    cache_key = (lang_code, device)
    pipeline = _pipeline_cache.get(cache_key)
    if pipeline is not None:
        return pipeline

    with _pipeline_lock:
        pipeline = _pipeline_cache.get(cache_key)
        if pipeline is not None:
            return pipeline
        _pipeline_cache[cache_key] = _create_pipeline(KPipeline, lang_code=lang_code, device=device)
        return _pipeline_cache[cache_key]


def _kokoro_device() -> str | None:
    import os

    value = os.getenv("KOKORO_SERVICE_DEVICE", "").strip()
    return value or None


def _create_pipeline(pipeline_cls, *, lang_code: str, device: str | None):
    try:
        return pipeline_cls(lang_code=lang_code, device=device)
    except RuntimeError as exc:
        if not _should_fallback_to_cpu(device, exc):
            raise

        logger.warning(
            "Kokoro device %r is unavailable, retrying on CPU: %s",
            device,
            exc,
        )
        return pipeline_cls(lang_code=lang_code, device="cpu")


def _should_fallback_to_cpu(device: str | None, exc: RuntimeError) -> bool:
    if device is None:
        return False

    normalized_device = device.strip().lower()
    if normalized_device not in {"cuda", "gpu"}:
        return False

    message = str(exc).lower()
    return "cuda requested but not available" in message
