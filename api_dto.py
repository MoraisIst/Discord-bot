from typing import List, Optional
from pydantic import BaseModel


class TrackDTO(BaseModel):
    title: str
    url: str
    duration: Optional[int] = None
    thumbnail: Optional[str] = None


class BotStateDTO(BaseModel):
    is_playing: bool
    current_song: Optional[str]
    queue_length: int
    volume: int
