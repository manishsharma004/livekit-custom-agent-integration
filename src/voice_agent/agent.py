from __future__ import annotations

from dotenv import load_dotenv
from livekit import agents
from livekit.agents import Agent, AgentServer, AgentSession, inference, room_io
from livekit.plugins import openai

from voice_agent.config import Settings
from voice_agent.kokoro_tts import KokoroTTS

load_dotenv()

settings = Settings.from_env()
server = AgentServer()


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions=(
                "You are a concise voice AI assistant for internal platform and product use. "
                "Answer clearly, speak naturally, ask brief follow-up questions when needed, "
                "and keep responses short unless the user asks for more detail."
            )
        )


@server.rtc_session(agent_name=settings.agent_name)
async def entrypoint(ctx: agents.JobContext) -> None:
    session = AgentSession(
        stt=inference.STT(
            model=settings.inference_stt_model,
            base_url=settings.livekit_api_url,
            api_key=settings.livekit_api_key,
            api_secret=settings.livekit_api_secret,
        ),
        llm=openai.LLM(
            model=settings.ollama_model,
            base_url=settings.ollama_base_url,
            api_key=settings.ollama_api_key,
        ),
        tts=KokoroTTS(
            service_url=settings.kokoro_service_url,
            voice=settings.kokoro_voice,
            lang_code=settings.kokoro_lang_code,
            speed=settings.kokoro_speed,
        ),
    )

    await session.start(
        room=ctx.room,
        agent=Assistant(),
        room_options=room_io.RoomOptions(),
    )

    await session.generate_reply(
        instructions=(
            "Greet the user, mention that your reasoning model is running locally through Ollama, "
            "and ask how you can help."
        )
    )


if __name__ == "__main__":
    agents.cli.run_app(server)
