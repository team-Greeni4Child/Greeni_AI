from fastapi import APIRouter
from schemas.game import (
    FiveQCheckResponse, FiveQCheckRequest
)
from services import game_service

router = APIRouter()

@router.post("/fiveq/check", response_model=FiveQCheckResponse)
async def fiveq_check(body: FiveQCheckRequest):
    return game_service.check_fiveq(
        utterance=body.utterance,
        answer=body.answer,
    )
