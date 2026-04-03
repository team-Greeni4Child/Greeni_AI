# routers/stt.py

from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form
from schemas.stt import STTResponse
from services import stt_service

router = APIRouter()

@router.post("/transcribe", response_model=STTResponse)
async def transcribe(
    voice: UploadFile = File(...),
    purpose: str = Form(...),
    store_audio: bool = Form(False),
    session_id: Optional[str] = Form(None)
):
    audio_bytes = await voice.read()

    return await stt_service.transcribe_file(
        audio_bytes=audio_bytes,
        filename=voice.filename,
        purpose=purpose,
        store_audio=store_audio,
        session_id=session_id
    )
