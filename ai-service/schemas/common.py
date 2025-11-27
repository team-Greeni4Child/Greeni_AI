from pydantic import BaseModel, Field
from typing import Optional


class ErrorResponse(BaseModel):
    error: str = Field(..., description="Error message")
    code: Optional[str] = Field(None, description="Stable error code")
