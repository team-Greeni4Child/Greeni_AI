# schemas.py

from __future__ import annotations
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, HttpUrl, conint, confloat


# ===== Common =====

class ErrorResponse(BaseModel):
    error: str = Field(..., description="Error message")
    code: Optional[str] = Field(None, description="Stable error code")


# ===== STT =====

class STTFormat(str, Enum):
    text = "text"
    srt = "srt"
    vtt = "vtt"
    json = "json"

class STTResponse(BaseModel):
    text: str = Field(..., description="Transcribed text")
    audio_url: Optional[HttpUrl] = Field(None, description="Stored audio URL (optional)")


# ===== TTS =====

class TTSRequest(BaseModel):
    text: str = Field(..., description="Text to synthesize")
    voice: Optional[str] = Field(None, description="Voice id/name")
    speed: confloat(ge=0.5, le=2.0) = Field(1.0, description="Playback speed multiplier")

class TTSResponse(BaseModel):
    audio_url: HttpUrl
    durationSec: Optional[confloat(gt=0.0)] = None


# ===== Game (animal / twentyq) =====

class AnimalCheckRequest(BaseModel):
    utterance: str = Field(..., description="Child utterance (from STT)")
    answer: str = Field(..., description="Canonical animal name")

class AnimalCheckResponse(BaseModel):
    correct: bool
    matched: Optional[str] = None
    note: Optional[str] = Field(None, description="e.g., 'negation_detected'")

class TwentyQCheckRequest(BaseModel):
    utterance: str = Field(..., description="Child utterance (from STT)")
    answer: str = Field(..., description="Target word")

class TwentyQCheckResponse(BaseModel):
    correct: bool


# ===== Diary (turns -> compose with memory) =====

class DiaryTurnRequest(BaseModel):
    child: bool = Field(..., description="True if speaker is the child")
    text: str = Field(..., description="STT text")
    audio_url: Optional[HttpUrl] = Field(None, description="Original audio URL (optional)")

class DiaryTurnResponse(BaseModel):
    turns: conint(ge=0)

class MemoryHit(BaseModel):
    id: str = Field(..., description="e.g., 'sid:20250911:1'")
    score: confloat(ge=0.0, le=1.0)
    date: str = Field(..., description="YYYY-MM-DD")
    tags: Optional[List[str]] = None

class DiaryComposeQuery(BaseModel):
    withMemory: bool = Field(True)
    topK: conint(ge=1, le=20) = Field(5)
    recentDays: Optional[conint(ge=1, le=365)] = Field(90)

class DiaryComposeResponse(BaseModel):
    diary: str
    child_turns: conint(ge=0)
    memory_hits: Optional[List[MemoryHit]] = None
    mood: Optional[str] = None


# ===== Chat (roleplay) =====

class RoleplayRequest(BaseModel):
    sid: str = Field(..., description="Session/child id")
    text: str = Field(..., description="Child utterance")
    withMemory: bool = Field(True)
    topK: conint(ge=1, le=20) = Field(5)
    recentDays: Optional[conint(ge=1, le=365)] = Field(90)
    style: Optional[str] = Field(None, description="Optional system style")

class RoleplayResponse(BaseModel):
    reply: str
