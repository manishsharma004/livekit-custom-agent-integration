from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import FileResponse
from livekit import api
from pydantic import BaseModel, Field

from voice_agent.config import Settings

load_dotenv()

settings = Settings.from_env()
app = FastAPI(title="LiveKit Demo UI", version="0.1.0")


class SessionRequest(BaseModel):
    room_name: str | None = Field(default=None, max_length=64)
    participant_name: str | None = Field(default=None, max_length=64)


class SessionResponse(BaseModel):
    room_name: str
    participant_name: str
    participant_token: str
    livekit_url: str
    agent_name: str


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(Path(__file__).with_name("static") / "index.html")


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/session", response_model=SessionResponse)
async def create_session(payload: SessionRequest) -> SessionResponse:
    room_name = _normalize_room_name(payload.room_name)
    participant_name = payload.participant_name or f"demo-user-{uuid4().hex[:6]}"

    async with api.LiveKitAPI(
        url=settings.livekit_api_url,
        api_key=settings.livekit_api_key,
        api_secret=settings.livekit_api_secret,
    ) as livekit_api:
        rooms = await livekit_api.room.list_rooms(api.ListRoomsRequest(names=[room_name]))
        if not rooms.rooms:
            await livekit_api.room.create_room(
                api.CreateRoomRequest(name=room_name, empty_timeout=300, max_participants=8)
            )

        dispatches = await livekit_api.agent_dispatch.list_dispatch(room_name)
        if not any(dispatch.agent_name == settings.agent_name for dispatch in dispatches):
            await livekit_api.agent_dispatch.create_dispatch(
                api.CreateAgentDispatchRequest(agent_name=settings.agent_name, room=room_name)
            )

    token = (
        api.AccessToken(settings.livekit_api_key, settings.livekit_api_secret)
        .with_identity(participant_name)
        .with_name(participant_name)
        .with_grants(api.VideoGrants(room_join=True, room=room_name))
        .to_jwt()
    )

    return SessionResponse(
        room_name=room_name,
        participant_name=participant_name,
        participant_token=token,
        livekit_url=settings.livekit_public_url,
        agent_name=settings.agent_name,
    )


def _normalize_room_name(room_name: str | None) -> str:
    if not room_name:
        return f"demo-room-{uuid4().hex[:8]}"

    sanitized = "".join(char.lower() if char.isalnum() else "-" for char in room_name)
    compact = "-".join(part for part in sanitized.split("-") if part)
    return compact[:64] or f"demo-room-{uuid4().hex[:8]}"
