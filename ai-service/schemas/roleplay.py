from typing import Optional
from pydantic import BaseModel, Field
from typing import Optional, Sequence, Literal


RoleType = Literal["shop", "teacher", "friend"]

class RoleplayRequest(BaseModel):
    session_id: str = Field(..., description="Session Identifier")
    role: RoleType = Field(..., description='"shop"|"teacher"|"friend"')
    user_text: str = Field(..., min_length=1)
    temperature: float = 0.7
    top_p: float = 1.0
    max_tokens: int = 256


class RoleplayResponse(BaseModel):
    session_id: str
    reply: str
    turn: int = Field(..., ge=0)

class RoleplayEndRequest(BaseModel):
    session_id: str = Field(..., description="Session Identifier")

class RoleplayEndResponse(BaseModel):
    session_id: str