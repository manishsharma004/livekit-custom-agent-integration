from __future__ import annotations

import asyncio
import json
from urllib import error, request
from uuid import uuid4

from livekit.agents import tts
from livekit.agents.log import logger
from livekit.agents.types import APIConnectOptions, DEFAULT_API_CONNECT_OPTIONS


class KokoroTTS(tts.TTS):
    def __init__(
        self,
        *,
        service_url: str,
        voice: str = "af_heart",
        lang_code: str = "a",
        speed: float = 1.0,
    ) -> None:
        super().__init__(
            capabilities=tts.TTSCapabilities(streaming=False),
            sample_rate=24000,
            num_channels=1,
        )
        self._service_url = service_url.rstrip("/")
        self._voice = voice
        self._lang_code = lang_code
        self._speed = speed

    @property
    def model(self) -> str:
        return "kokoro"

    @property
    def provider(self) -> str:
        return "kokoro"

    def prewarm(self) -> None:
        try:
            self._healthcheck()
        except Exception as exc:
            logger.warning("Kokoro service health check failed: %s", exc)

    def synthesize(
        self, text: str, *, conn_options: APIConnectOptions = DEFAULT_API_CONNECT_OPTIONS
    ) -> tts.ChunkedStream:
        return KokoroChunkedStream(tts=self, input_text=text, conn_options=conn_options)

    async def aclose(self) -> None:
        return None

    def _healthcheck(self) -> None:
        with request.urlopen(f"{self._service_url}/healthz", timeout=5) as response:
            if response.status != 200:
                raise RuntimeError(f"Kokoro service health check failed with status {response.status}")

    def _synthesize_pcm(self, text: str) -> tuple[bytes, int, int, str]:
        payload = json.dumps(
            {
                "text": text,
                "voice": self._voice,
                "lang_code": self._lang_code,
                "speed": self._speed,
            }
        ).encode("utf-8")
        req = request.Request(
            f"{self._service_url}/v1/synthesize",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with request.urlopen(req, timeout=60) as response:
                if response.status != 200:
                    raise RuntimeError(f"Kokoro service returned status {response.status}")
                audio = response.read()
                sample_rate = int(response.headers.get("X-Sample-Rate", "24000"))
                num_channels = int(response.headers.get("X-Num-Channels", "1"))
                request_id = response.headers.get("X-Request-Id", str(uuid4()))
                return audio, sample_rate, num_channels, request_id
        except error.URLError as exc:
            raise RuntimeError(f"Failed to call Kokoro service at {self._service_url}: {exc}") from exc


class KokoroChunkedStream(tts.ChunkedStream):
    def __init__(self, *, tts: KokoroTTS, input_text: str, conn_options: APIConnectOptions) -> None:
        super().__init__(tts=tts, input_text=input_text, conn_options=conn_options)
        self._tts = tts

    async def _run(self, output_emitter: tts.AudioEmitter) -> None:
        pcm, sample_rate, num_channels, request_id = await asyncio.to_thread(
            self._tts._synthesize_pcm, self.input_text
        )
        output_emitter.initialize(
            request_id=request_id,
            sample_rate=sample_rate,
            num_channels=num_channels,
            mime_type="audio/pcm",
        )
        output_emitter.push(pcm)
        output_emitter.flush()
