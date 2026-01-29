from typing import Optional, Literal
from pydantic import BaseModel, Field, HttpUrl, confloat


class TTSRequest(BaseModel):
    # 추가한 부분 3: TTS 요청 명시 - purpose
    purpose: Literal["fiveq", "roleplay", "diary"] = Field(
        ..., description="TTS usage context"
    )
    text: str = Field(..., description="Text to synthesize")
    voice: Optional[str] = Field(None, description="Voice id/name")
    speed: confloat(ge=0.5, le=2.0) = Field(
        1.0,
        description="Playback speed multiplier"
    )

class TTSResponse(BaseModel):
    audio_url: HttpUrl