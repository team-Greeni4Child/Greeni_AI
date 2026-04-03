import asyncio
import requests
from requests.adapters import HTTPAdapter, Retry
from typing import Optional
from fastapi import HTTPException
from config import settings
from common.logging import get_logger
from common.errors import AppError

CLOVA_TTS_URL = "https://naveropenapi.apigw.ntruss.com/tts-premium/v1/tts"
log = get_logger("greeni.tts_service")

# 재시도 가능한 세션
_session = requests.Session()
_session.mount(
    "https://",
    HTTPAdapter(
        max_retries=Retry(
            total=3, backoff_factor=0.5, status_forcelist=[429, 500, 502, 503, 504]
        )
    ),
)

# 클로바 api key
def _require_keys():
    if not settings.CLOVA_API_KEY_ID or not settings.CLOVA_API_KEY:
        log.error("clova_key_missing")
        raise AppError(
            message="CLOVA API key not configured",
            code="clova_key_missing",
            status_code=500,
        )

# speed 매핑
def _map_speed(speed: float) -> int:
    return max(-5, min(5, round((speed - 1.0) * 5)))

# api 호출 및 음성 생성
def _call_clova_tts(text: str, speaker: str, speed_opt: int, pitch: int) -> bytes:
    form = {
        "speaker": speaker,      # 기본: "ngaram"
        "text": text,
        "format": "mp3",
        "pitch": 1,              # 고정
        "volume": "0",
        "speed": str(speed_opt), # 항상 명시
    }
    headers = {
        "X-NCP-APIGW-API-KEY-ID": settings.CLOVA_API_KEY_ID,
        "X-NCP-APIGW-API-KEY": settings.CLOVA_API_KEY,
        "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
    }

    log.info(
        "clova_tts_request_start",
        extra={
            "speaker": speaker,
            "speed_opt": speed_opt,
            "text_len": len(text),
        }
    )
    try: 
        r = _session.post(CLOVA_TTS_URL, headers=headers, data=form, timeout=20)
    except requests.RequestException as e:
        log.exception(
            "clova_tts_network_error",
            extra={
                "speaker": speaker,
                "speed_opt": speed_opt,
                "text_len": len(text),
            }
        )
        raise AppError(
            message="CLOVA TTS 요청에 실패했습니다.",
            code="clova_tts_network_error",
            status_code=502,
        ) from e
    
    if r.status_code != 200:
        log.warning(
            "clova_tts_bad_status",
            extra={
                "status_code": r.status_code,
                "speaker": speaker,
                "speed_opt": speed_opt,
                "text_len": len(text),
            },
        )
        raise AppError(
            message="CLOVA TTS 생성에 실패했습니다.",
            code="clova_tts_failed",
            status_code=502,
        )
    
    log.info(
        "clova_tts_success",
        extra={
            "speaker": speaker,
            "speed_opt": speed_opt,
            "text_len": len(text),
        },
    )

    return r.content

# 요청
async def synthesize(text: str, voice: Optional[str], speed: float) -> bytes:
    _require_keys()
    speaker = voice or "ngaram"
    pitch = 1
    speed_opt = _map_speed(speed)
    return await asyncio.to_thread(_call_clova_tts, text, speaker, speed_opt, pitch)
