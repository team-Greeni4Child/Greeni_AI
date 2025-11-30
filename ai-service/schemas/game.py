from pydantic import BaseModel, Field


# ===== Five Questions =====

class FiveQCheckRequest(BaseModel):
    utterance: str = Field(..., description="Child utterance (from STT)")
    answer: str = Field(..., description="Target word")


class FiveQCheckResponse(BaseModel):
    correct: bool
