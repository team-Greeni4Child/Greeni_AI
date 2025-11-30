from typing import Optional, List
from pydantic import BaseModel, Field, HttpUrl, conint, confloat


# ===== Turns =====

class DiaryTurnRequest(BaseModel):
    child: bool = Field(..., description="True if speaker is the child")
    text: str = Field(..., description="STT text")
    audio_url: Optional[HttpUrl] = Field(
        None,
        description="Original audio URL (optional)"
    )


class DiaryTurnResponse(BaseModel):
    turns: conint(ge=0)


# ===== Memory Hits =====

class MemoryHit(BaseModel):
    id: str = Field(..., description="e.g., 'sid:20250102:1'")
    score: confloat(ge=0.0, le=1.0)
    date: str = Field(..., description="YYYY-MM-DD")
    tags: Optional[List[str]] = None


# ===== Compose =====

class DiaryComposeQuery(BaseModel):
    withMemory: bool = Field(True)
    topK: conint(ge=1, le=20) = Field(5)
    recentDays: Optional[conint(ge=1, le=365)] = Field(90)


class DiaryComposeResponse(BaseModel):
    diary: str
    child_turns: conint(ge=0)
    memory_hits: Optional[List[MemoryHit]] = None
    mood: Optional[str] = None
