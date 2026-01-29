from fastapi import APIRouter
from schemas.stt import STTRequest, STTResponse
from services import stt_service

router = APIRouter()

@router.post("/transcribe", response_model=STTResponse)
async def transcribe(req: STTRequest):
    return await stt_service.transcribe_url(
        audio_url=req.audio_url,
        store_audio=req.store_audio,
    )
