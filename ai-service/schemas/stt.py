from enum import Enum
from typing import Optional, Literal
from pydantic import BaseModel, Field


class STTFormat(str, Enum):
    text = "text"
    srt = "srt"
    vtt = "vtt"
    json = "json"


class STTRequest(BaseModel):
    purpose: Literal["roleplay", "fiveq", "diary"] = Field(
        ...,
        description='Indicates the feature context ("roleplay" | "fiveq" | "diary")',
        examples=["diary"],
    )
    store_audio: bool = Field(
        False,
        description="Whether to store the audio after processing",
        examples=[False],
    )
    session_id: Optional[str] = Field(
        None, 
        description="Only exists for diary"
    )


class STTResponse(BaseModel):
    text: str = Field(
        ..., 
        description="Transcribed text"
    )
    audio_url: Optional[str] = Field(
        None, 
        description="Stored audio URL (optional)"
    )
