from typing import Optional
from pydantic import BaseModel, Field, conint


class RoleplayRequest(BaseModel):
    sid: str = Field(..., description="Session/child id")
    text: str = Field(..., description="Child utterance")
    withMemory: bool = Field(True)
    topK: conint(ge=1, le=20) = Field(5)
    recentDays: Optional[conint(ge=1, le=365)] = Field(90)
    style: Optional[str] = Field(None, description="Optional system style")


class RoleplayResponse(BaseModel):
    reply: str
