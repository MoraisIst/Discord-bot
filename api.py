from typing import List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import api_dto
from discord_bot import MusicCog

app = FastAPI()


def get_cog() -> MusicCog:
    try:
        music_cog = MusicCog.get_instance()
        if music_cog is None:
            raise HTTPException(status_code=503, detail="MusicCog not found")
        return music_cog
    except ValueError:
        raise HTTPException(status_code=503, detail="Bot not initialized yet")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class Command(BaseModel):
    action: str
    payload: dict = {}


@app.get("/state", response_model=api_dto.BotStateDTO)
async def get_bot_state():
    music_cog = get_cog()
    state = api_dto.BotStateDTO(
        is_playing=music_cog.is_playing,
        current_song=music_cog.current_song,
        queue_length=len(music_cog.queue),
        volume=music_cog.volume,
    )
    return state


@app.get("/queue", response_model=List[api_dto.TrackDTO])
async def get_queue():
    music_cog = get_cog()
    queue = [
        api_dto.TrackDTO(
            title=track.title,
            url=track.url,
            duration=track.duration,
            thumbnail=track.thumbnail,
        )
        for track in music_cog.queue
    ]
    return queue


@app.post("/play")
async def play_song(command: Command):
    music_cog = get_cog()
    url = command.payload.get("url")
    if not url:
        raise HTTPException(status_code=400, detail="URL is required to play a song")
    success, message = await music_cog._play_impl(url)
    return {"status": f"{success}", "message": f"{message}"}


@app.post("/command")
async def receive_command(command: Command):
    print(f"Received command: {command.action} with payload: {command.payload}")
    return {"status": "success", "message": f"Command '{command.action}' received."}
