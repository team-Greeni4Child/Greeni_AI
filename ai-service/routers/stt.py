from fastapi import APIRouter, File, UploadFile
from schemas.stt import STTResponse
from services import stt_service

router = APIRouter()

@router.post("/transcribe", response_model=STTResponse)
async def transcribe(file: UploadFile = File(...)):
    return await stt_service.transcribe(file)
