from enum import Enum
from typing import Optional, Literal
from pydantic import BaseModel, Field, HttpUrl


class STTFormat(str, Enum):
    text = "text"
    srt = "srt"
    vtt = "vtt"
    json = "json"


class STTRequest(BaseModel):
    audio_url: HttpUrl = Field(
        ...,
        description="Access URL to the S3 audio file provided by the backend (assumes presigned URL)",
        examples=["https://example-bucket.s3.amazonaws.com/audio.wav?X-Amz-Signature=..."],
    )
    purpose: Literal["roleplay", "game", "diary"] = Field(
        ...,
        description='Indicates the feature context ("roleplay" | "game" | "diary")',
        examples=["diary"],
    )
    store_audio: bool = Field(
        False,
        description="Whether to store the audio after processing",
        examples=[False],
    )


class STTResponse(BaseModel):
    text: str = Field(..., description="Transcribed text")
    audio_url: Optional[HttpUrl] = Field(
        None, description="Stored audio URL (optional)"
    )
