from fastapi import Query
from fastapi import APIRouter, HTTPException
from schemas.tts import TTSRequest, TTSResponse
from services import tts_service
# 추가한 부분 4: 불필요한 import 주석(삭제)
# from storage.files import save_tts_file, delete_after_delay
from config import settings
import asyncio
# 추가한 부분 5: import 추가 - requests , uuid, datetime
import requests
import uuid
import datetime

router = APIRouter()

# 추가한 부분 6: 불필요한 BASE_URL 주석(삭제)
# BASE_URL = settings.BASE_URL  # 예: http://localhost:8000

# 추가한 부분 7: tts 파일 이름 생성 함수
def _make_tts_filename(purpose: str) -> str:
    # 기존 files.py 규칙 유지 + purpose 추가
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    file_id = uuid.uuid4().hex[:8]
    filename = f"tts_{purpose}_{timestamp}_{file_id}.mp3"
    return filename

# 추가한 부분 8: presign 요청
def _request_presign(filename: str) -> dict:
    """
    백엔드 presign 요청:
    GET {BACKEND_BASE_URL}{BACKEND_PRESIGN_PATH}?file=<filename>
    """
    presign_url = settings.BACKEND_BASE_URL.rstrip("/") + settings.BACKEND_PRESIGN_PATH

    headers = {}
    if getattr(settings, "BACKEND_ACCESS_TOKEN", ""):
        headers["Authorization"] = f"Bearer {settings.BACKEND_ACCESS_TOKEN}"

    # Token 제대로 반영하고 있는지 확인하려고 넣어본 디버깅 코드
    # print("DBG token len:", len(getattr(settings, "BACKEND_ACCESS_TOKEN", "") or ""))
    # print("DBG auth header:", headers.get("Authorization"))

    r = requests.get(
        presign_url,
        params={"file": filename},
        headers=headers,
        timeout=10,
    )

    if r.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail=f"presign request failed: {r.status_code} {r.text[:200]}",
        )

    data = r.json()

    # 경우1 { "url": "...", "key": "..." }
    if isinstance(data, dict) and data.get("url") and data.get("key"):
        return {"url": data["url"], "key": data["key"]}

    # 경우2 { "isSuccess": true, "result": {"url": "...", "key": "..."} }
    if data.get("isSuccess") is True:
        result = data.get("result") or {}
        if result.get("url") and result.get("key"):
            return {"url": result["url"], "key": result["key"]}

    raise HTTPException(status_code=502, detail=f"presign invalid response: {data}")

# 추가한 부분 9: presign url로 PUT 업로드
def _put_upload(presigned_url: str, audio_bytes: bytes) -> None:
    r = requests.put(
        presigned_url,
        data=audio_bytes,
        headers={"Content-Type": "audio/mpeg"},
        timeout=30,
    )
    if r.status_code < 200 or r.status_code >= 300:
        raise HTTPException(
            status_code=502,
            detail=f"upload failed: {r.status_code} {r.text[:200]}",
        )

@router.post("/speak", response_model=TTSResponse)
async def speak(body: TTSRequest):
    if not body.text or not body.text.strip():
        raise HTTPException(status_code=400, detail="text is empty")

    audio_bytes = await tts_service.synthesize(
        text=body.text,
        voice=body.voice,
        speed=body.speed,
    )

    # 추가한 부분 10: 업로드 파일명 생성 - purpose 포함
    filename = _make_tts_filename(body.purpose)

    # 추가한 부분 11: presign 요청
    presign = await asyncio.to_thread(_request_presign, filename)
    presigned_url = presign["url"]
    key = presign["key"]

    # 추가한 부분 12: put 업로드
    await asyncio.to_thread(_put_upload, presigned_url, audio_bytes)

    # 추가한 부분 13: key -> 최종 재생 url
    audio_url = settings.S3_PUBLIC_BASE_URL.rstrip("/") + "/" + key.lstrip("/")

    # 추가한 부분 14: 불필요한 부분 주석(삭제)
    # filepath = save_tts_file(audio_bytes)
    # asyncio.create_task(delete_after_delay(filepath, delay=300))
    # audio_url = f"{BASE_URL}/storage/tts/{filepath.name}"

    return TTSResponse(audio_url=audio_url)
