from __future__ import annotations

from pydantic import BaseModel, Field, conint, confloat
from typing_extensions import Literal


# ========= Enums =========

DiaryStatus = Literal["active", "ended", "completed"]

EmotionLabel = Literal[
    "angry",
    "happy",
    "sad",
    "surprised",
    "anxiety",
]


# ========= Chat (ping-pong) =========

class DiaryChatRequest(BaseModel):
    session_id: str = Field(..., description="Diary session id (from frontend)")
    user_text: str = Field(..., min_length=1, description="Child utterance text")

class DiaryChatResponse(BaseModel):
    session_id: str
    reply: str = Field(..., description="Model answer")
    turn_count: conint(ge=0) = Field(..., description="Total user turns so far")
    status: DiaryStatus = Field("active", description="active or ended")


# ========= Session End (explicit) =========

class DiarySessionEndRequest(BaseModel):
    session_id: str
    status : DiaryStatus

class DiarySessionEndResponse(BaseModel):
    session_id: str
    turn_count: conint(ge=0)
    status: DiaryStatus = Field("ended")


# ========= Summary + Emotion (after end) =========

class DiaryEmotion(BaseModel):
    primary: EmotionLabel
    confidence: confloat(ge=0.0, le=1.0)

class DiarySummarizeRequest(BaseModel):
    session_id: str

class DiarySummarizeResponse(BaseModel):
    session_id: str
    turn_count: conint(ge=0)
    summary: str
    emotion: DiaryEmotion
