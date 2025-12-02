from fastapi import APIRouter
from schemas.game import (
    FiveQHintRequest, FiveQHintResponse,
    FiveQCheckResponse, FiveQCheckRequest
)
from services import game_service

router = APIRouter()

@router.post("/fiveq/hint", response_model=FiveQHintResponse)
async def fiveq_hint(body: FiveQHintRequest):
    return game_service.generate_fiveq(
        answer=body.answer
    )

@router.post("/fiveq/check", response_model=FiveQCheckResponse)
async def fiveq_check(body: FiveQCheckRequest):
    return game_service.check_fiveq(
        utterance=body.utterance,
        answer=body.answer,
    )
