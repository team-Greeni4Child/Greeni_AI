# routers/tts.py

from fastapi import APIRouter, HTTPException, Response, BackgroundTasks
from schemas.tts import TTSRequest, TTSResponse
from services import tts_service
from config import settings
import requests
import uuid
import datetime
import base64
from common.logging import get_logger
from common.errors import AppError

log = get_logger("greeni.tts")
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
        log.info(
            "presign_request_start",
            extra={
                "tts_filename":filename,
                "path":path,
                "url": presign_url,
                "has_auth": bool(settings.BACKEND_MASTER_TOKEN),
            },
        )

    try:
        r = requests.get(
            presign_url,
            params={
                "fileName": filename,
                "path": path,
            },
            headers=headers,
            timeout=60,
        )
    except requests.RequestException as e:
        log.exception(
            "presign_request_failed",
            extra={"tts_filename": filename, "path": path},
        )
        raise AppError(
            message="presign 요청에 실패했습니다.",
            code="presign_network_error",
            status_code=502,
        ) from e

    if r.status_code != 200:
        log.warning(
            "presign_bad_status",
            extra={
                "tts_filename": filename,
                "path": path,
                "status_code": r.status_code,
            },
        )
        raise AppError(
            message="presign 요청에 실패했습니다.",
            code="presign_bad_status",
            status_code=502,
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
    
    log.warning(
        "presign_invalid_response",
        extra={
            "tts_filename": filename,
            "path": path,
        },
    )
    raise AppError(
        message="presign 응답 형식이 올바르지 않습니다.",
        code="presign_invalid_response",
        status_code=502,
    )


# 추가한 부분 9: presign url로 PUT 업로드
def _put_upload(presigned_url: str, audio_bytes: bytes) -> None:
    try:
        r = requests.put(
            presigned_url,
            data=audio_bytes,
            timeout=30,
        )
    except requests.RequestException as e: 
        log.exception("tts_upload_network_error")
        raise AppError(
            message="TTS 업로드에 실패했습니다.",
            code="tts_upload_network_error",
            status_code=502,
        ) from e
    
    if r.status_code < 200 or r.status_code >= 300:
        log.warning(
            "tts_upload_bad_status",
            extra={"status_code": r.status_code},
        )
        raise AppError(
            message="TTS 업로드에 실패했습니다.",
            code="tts_upload_bad_status",
            status_code=502,
        )

# diary 업로드 백그라운드 작업
def _upload_diary_tts(audio_bytes: bytes, filename: str, path: str):
    audio_url = None

    try:
        presign = _request_presign(filename, path)

        presigned_url = presign["url"]
        key = presign["key"]

        _put_upload(presigned_url, audio_bytes)

        audio_url = settings.S3_PUBLIC_BASE_URL.rstrip("/") + "/" + key.lstrip("/")

        log.info(
            "tts_upload_success",
            extra={
                "tts_filename": filename,
                "path": path,
                "audio_url": audio_url,
            },
        )

    except AppError:
        log.exception(
            "tts_upload_failed",
            extra={"tts_filename": filename, "path": path},
        )

    except Exception:
        log.exception(
            "tts_upload_unexpected",
            extra={"tts_filename": filename, "path": path},
        )

    return audio_url


@router.post("/speak", response_model=TTSResponse)
async def speak(body: TTSRequest, background_tasks: BackgroundTasks):
    if not body.text or not body.text.strip():
        raise HTTPException(status_code=400, detail="text is empty")
    
    log.info(
        "tts_request_start",
        extra={
            "purpose": body.purpose,
            "has_voice": bool(body.voice),
            "speed": body.speed,
            "text_len": len(body.text or ""),
        },
    )

    audio_bytes = await tts_service.synthesize(
        text=body.text,
        voice=body.voice,
        speed=body.speed,
    )

    audio_b64 = base64.b64encode(audio_bytes).decode("ascii")
    audio_url = None

    if body.purpose == "diary":
        filename = _make_tts_filename(body.purpose)
        path = _resolve_path(body.purpose)
        audio_url = _upload_diary_tts(audio_bytes, filename, path)

    log.info(
        "tts_request_success",
        extra={
            "purpose": body.purpose,
            "has_audio_url": bool(audio_url),
        },
    )

    return TTSResponse(
        audio_content=audio_b64,
        audio_url=audio_url
    )