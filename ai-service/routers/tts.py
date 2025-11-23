from fastapi import Query
from fastapi import APIRouter, HTTPException
from schemas import TTSRequest, TTSResponse
from services import tts_service
from storage.files import save_tts_file, delete_after_delay
from config import settings
import asyncio

router = APIRouter()

BASE_URL = settings.BASE_URL  # 예: http://localhost:8000

@router.post("/speak", response_model=TTSResponse)
async def speak(body: TTSRequest):
    if not body.text or not body.text.strip():
        raise HTTPException(status_code=400, detail="text is empty")

    audio_bytes = await tts_service.synthesize(
        text=body.text,
        voice=body.voice,
        speed=body.speed,
    )
    filepath = save_tts_file(audio_bytes)
    asyncio.create_task(delete_after_delay(filepath, delay=30))
    audio_url = f"{BASE_URL}/storage/tts/{filepath.name}"

    return TTSResponse(audio_url=audio_url)

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

