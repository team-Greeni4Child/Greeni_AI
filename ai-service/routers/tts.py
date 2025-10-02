from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from schemas import TTSRequest
from services import tts_service

from fastapi import Query

router = APIRouter()

@router.post("/speak")
async def speak(body: TTSRequest):
    if not body.text or not body.text.strip():
        raise HTTPException(status_code=400, detail="text is empty")

    audio = await tts_service.synthesize(
        text=body.text, voice=body.voice, speed=body.speed
    )
    return Response(
        content=audio,
        media_type="audio/mpeg",
        headers={
            "Content-Disposition": 'inline; filename="tts.mp3"',
            "Cache-Control": "no-store",
        },
    )

# get test code (삭제 예정)
@router.get("/stream")
async def stream(text: str = Query(...), voice: str | None = None, speed: float = 1.0):
    if not text.strip():
        raise HTTPException(status_code=400, detail="text is empty")
    audio = await tts_service.synthesize(text=text, voice=voice, speed=speed)
    return Response(
        content=audio,
        media_type="audio/mpeg",
        headers={
            "Content-Disposition": 'inline; filename="tts.mp3"',
            "Cache-Control": "no-store",
        },
    )
