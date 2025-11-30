from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, HttpUrl


class STTFormat(str, Enum):
    text = "text"
    srt = "srt"
    vtt = "vtt"
    json = "json"


class STTResponse(BaseModel):
    text: str = Field(..., description="Transcribed text")
    audio_url: Optional[HttpUrl] = Field(
        None, description="Stored audio URL (optional)"
    )
