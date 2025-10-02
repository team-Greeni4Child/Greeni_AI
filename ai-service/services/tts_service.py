import asyncio
import requests
from requests.adapters import HTTPAdapter, Retry
from typing import Optional
from fastapi import HTTPException
from config import settings

CLOVA_TTS_URL = "https://naveropenapi.apigw.ntruss.com/tts-premium/v1/tts"

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

# 클로바 api key 불러오기
def _require_keys():
    if not settings.CLOVA_API_KEY_ID or not settings.CLOVA_API_KEY:
        raise HTTPException(status_code=500, detail="CLOVA API key not configured")

# speed 
def _map_speed(speed: float) -> int:
    # 0.5~2.0  →  -5~+5 근사
    return max(-5, min(5, round((speed - 1.0) * 5)))

# api 호출 및 음성 생성
def _call_clova_tts(text: str, speaker: str, speed_opt: int, pitch: int) -> bytes:
    form = {
        "speaker": speaker,      # 기본: "ngaram"
        "text": text,
        "format": "mp3",
        "pitch": str(pitch),     # 요청: 1
        "volume": "0",
        "speed": str(speed_opt), # 항상 명시
    }
    headers = {
        "X-NCP-APIGW-API-KEY-ID": settings.CLOVA_API_KEY_ID,
        "X-NCP-APIGW-API-KEY": settings.CLOVA_API_KEY,
        "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
    }
    r = _session.post(CLOVA_TTS_URL, headers=headers, data=form, timeout=20)
    if r.status_code != 200:
        # 사용자 에러메시지는 짧게, 상세는 로그에서 처리 권장
        try:
            msg = r.json()
        except Exception:
            msg = {"message": r.text[:200]}
        raise HTTPException(status_code=502, detail=f"CLOVA TTS error {r.status_code}")
    return r.content

# 요청
async def synthesize(text: str, voice: Optional[str], speed: float) -> bytes:
    _require_keys()
    speaker = voice or "ngaram"
    pitch = 1
    speed_opt = _map_speed(speed)
    return await asyncio.to_thread(_call_clova_tts, text, speaker, speed_opt, pitch)
