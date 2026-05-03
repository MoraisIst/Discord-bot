from typing import List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import api_dto
from discord_bot import MusicCog

app = FastAPI()


def get_cog() -> MusicCog:
    try:
        music_cog = MusicCog()
        if music_cog is None:
            raise HTTPException(status_code=503, detail="MusicCog not found")
        if music_cog.is_inVoice():
            return HTTPException(
                status_code=503, detail="Bot is currently in a voice channel"
            )
        return music_cog
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
    await music_cog.play(url)
    return {"status": "success", "message": f"Playing song from URL: {url}"}


@app.post("/skip")
async def skip_song():
    music_cog = get_cog()
    await music_cog.skip()
    return {"status": "success", "message": "Skipped current song"}


@app.post("/stop")
async def stop_music():
    music_cog = get_cog()
    await music_cog.stop()
    return {"status": "success", "message": "Stopped music and cleared queue"}


@app.post("/volume")
async def set_volume(command: Command):
    music_cog = get_cog()
    volume = command.payload.get("volume")
    if volume is None or not (0 <= volume <= 100):
        raise HTTPException(status_code=400, detail="Volume must be between 0 and 100")
    await music_cog.set_volume(volume)
    return {"status": "success", "message": f"Volume set to {volume}"}


@app.post("/pause")
async def pause_music():
    music_cog = get_cog()
    await music_cog.pause()
    return {"status": "success", "message": "Paused music"}


@app.post("/resume")
async def resume_music():
    music_cog = get_cog()
    await music_cog.resume()
    return {"status": "success", "message": "Resumed music"}


@app.post("/clear")
async def clear_queue():
    music_cog = get_cog()
    await music_cog.clear_queue()
    return {"status": "success", "message": "Cleared music queue"}


@app.post("/command")
async def receive_command(command: Command):
    print(f"Received command: {command.action} with payload: {command.payload}")
    return {"status": "success", "message": f"Command '{command.action}' received."}
