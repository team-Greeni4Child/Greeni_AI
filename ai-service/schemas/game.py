from typing import Optional
from pydantic import BaseModel, Field


# ===== Animal Check =====

class AnimalCheckRequest(BaseModel):
    utterance: str = Field(..., description="Child utterance (from STT)")
    answer: str = Field(..., description="Canonical animal name")


class AnimalCheckResponse(BaseModel):
    correct: bool
    matched: Optional[str] = None
    note: Optional[str] = Field(None, description="e.g., 'negation_detected'")


# ===== Twenty Questions (five-questions) =====

class TwentyQCheckRequest(BaseModel):
    utterance: str = Field(..., description="Child utterance (from STT)")
    answer: str = Field(..., description="Target word")


class TwentyQCheckResponse(BaseModel):
    correct: bool
