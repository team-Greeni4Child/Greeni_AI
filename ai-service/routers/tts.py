from fastapi import APIRouter
from schemas import TTSRequest, TTSResponse
from services import tts_service

router = APIRouter()

@router.post("/speak", response_model=TTSResponse)
async def speak(body: TTSRequest):
    return await tts_service.synthesize(
        text=body.text,
        voice=body.voice,
        speed=body.speed,
    )
