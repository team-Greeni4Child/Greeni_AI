from fastapi import APIRouter, HTTPException, Response, BackgroundTasks
from schemas.tts import TTSRequest
from services import tts_service
from config import settings
import asyncio
import requests
import uuid
import datetime

router = APIRouter()

# 추가한 부분 7: tts 파일 이름 생성 함수
def _make_tts_filename(purpose: str) -> str:
    # 기존 files.py 규칙 유지 + purpose 추가
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    file_id = uuid.uuid4().hex[:8]
    filename = f"tts_{purpose}_{timestamp}_{file_id}.mp3"
    return filename

# 추가한 부분: purpose를 path로 바꾸는 함수
def _resolve_path(purpose: str) -> str:
    if purpose == "diary":
        return "diary"
    return "tmp"

# 추가한 부분 8: presign 요청
# 추가한 부분 8-1: filename과 path 같이 보내기
def _request_presign(filename: str, path: str) -> dict:
    """
    백엔드 presign 요청:
    GET {BACKEND_BASE_URL}{BACKEND_PRESIGN_PATH}?file=<filename>
    """
    presign_url = settings.BACKEND_BASE_URL.rstrip("/") + settings.BACKEND_PRESIGN_PATH

    headers = {}
    if getattr(settings, "BACKEND_MASTER_TOKEN", ""):
        headers["Authorization"] = f"Bearer {settings.BACKEND_MASTER_TOKEN}"

    print("[presign] token exists =", bool(settings.BACKEND_MASTER_TOKEN))
    print("[presign] auth header =", f"Bearer {settings.BACKEND_MASTER_TOKEN[:10]}..." if settings.BACKEND_MASTER_TOKEN else None)
    print("[presign] url =", presign_url)
    print("[presign] params =", {"fileName": filename, "path": path})

    r = requests.get(
        presign_url,
        params={
            "fileName": filename,
            "path": path,
        },
        headers=headers,
        timeout=60,
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
        timeout=30,
    )
    if r.status_code < 200 or r.status_code >= 300:
        raise HTTPException(
            status_code=502,
            detail=f"upload failed: {r.status_code} {r.text[:200]}",
        )

# diary 업로드 백그라운드 작업
def _upload_diary_tts(audio_bytes: bytes, filename: str, path: str):
    try:
        presign = _request_presign(filename, path)

        presigned_url = presign["url"]
        key = presign["key"]

        _put_upload(presigned_url, audio_bytes)

        audio_url = settings.S3_PUBLIC_BASE_URL.rstrip("/") + "/" + key.lstrip("/")

        print("[TTS] S3 upload success")
        print("[TTS] audio_url =", audio_url)

        # TODO
        # 나중에 백엔드 API 생기면 여기서 전달
        # requests.post(BACKEND_API, json={"audioUrl": audio_url})

    except Exception as e:
        print("[TTS] S3 upload failed:", str(e))

# 추가한 부분: response_model 제거(mp3 byte 응답이라서)
@router.post("/speak")
async def speak(body: TTSRequest, background_tasks: BackgroundTasks):
    if not body.text or not body.text.strip():
        raise HTTPException(status_code=400, detail="text is empty")

    audio_bytes = await tts_service.synthesize(
        text=body.text,
        voice=body.voice,
        speed=body.speed,
    )

    path = _resolve_path(body.purpose)

    if body.purpose == "diary":
        filename = _make_tts_filename(body.purpose)
        path = _resolve_path(body.purpose)

        background_tasks.add_task(
            _upload_diary_tts,
            audio_bytes,
            filename,
            path,
        )

    return Response(
        content=audio_bytes,
    )