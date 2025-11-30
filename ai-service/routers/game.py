from fastapi import APIRouter
from schemas.game import (
    AnimalCheckRequest, AnimalCheckResponse,
    TwentyQCheckRequest, TwentyQCheckResponse,
)
from services import nlu_service

router = APIRouter()

@router.post("/animal/check", response_model=AnimalCheckResponse)
async def animal_check(body: AnimalCheckRequest):
    return nlu_service.check_animal(
        utterance=body.utterance,
        answer=body.answer,
    )

@router.post("/twentyq/check", response_model=TwentyQCheckResponse)
async def twentyq_check(body: TwentyQCheckRequest):
    return nlu_service.check_twentyq(
        utterance=body.utterance,
        answer=body.answer,
    )
