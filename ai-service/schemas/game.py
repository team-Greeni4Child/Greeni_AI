from typing import List
from pydantic import BaseModel, Field


class FiveQHintRequest(BaseModel): 
    answer: str = Field(..., description="Target word")


class FiveQHintResponse(BaseModel):
    hints: List[str] = Field(..., description="5 hints")


class FiveQCheckRequest(BaseModel):
    utterance: str = Field(..., description="Child utterance (from STT)")
    answer: str = Field(..., description="Target word")


class FiveQCheckResponse(BaseModel):
    correct: bool