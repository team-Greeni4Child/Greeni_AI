# common/llm.py
from __future__ import annotations

import logging
import time
from typing import Any, Optional

from fastapi import HTTPException
from openai import OpenAI
from config import settings

logger = logging.getLogger("greeni.llm")

_client: Optional[OpenAI] = None


def get_client() -> OpenAI:
    """
    OpenAI client singleton.
    - roleplay/game에서 각각 만들던 것을 common으로 통일합니다.
    """
    global _client
    if _client is None:
        _client = OpenAI(api_key=settings.OPENAI_API_KEY)
    return _client


def chat_text(
    *,
    messages: list[dict[str, str]],
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    top_p: Optional[float] = None,
    max_tokens: Optional[int] = None,
    feature: str = "unknown",
    session_id: Optional[str] = None,
    timeout_sec: float = 30.0,
) -> str:
    """
    Chat Completions 호출 후 '텍스트'만 반환.

    - 공통화 포인트:
      - client 생성/재사용
      - 모델/옵션 기본값 처리
      - 에러를 HTTPException으로 표준화(현재 app.py 핸들러와 호환) :contentReference[oaicite:1]{index=1}
      - 최소 로깅(기능명/세션/latency)

    NOTE:
    - 현재 app.py는 HTTPException.detail을 {"error": exc.detail}로 내려보냅니다. :contentReference[oaicite:2]{index=2}
      그래서 여기서는 detail을 "문자열"로 유지합니다.
    """

    use_model = model or getattr(settings, "CHAT_MODEL", "gpt-4o")  # roleplay가 쓰던 기본값 유지 :contentReference[oaicite:3]{index=3}
    client = get_client()

    t0 = time.time()
    try:
        resp = client.chat.completions.create(
            model=use_model,
            messages=messages,
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
            timeout=timeout_sec,  # openai sdk에서 지원되는 인자(미지원 버전이면 TypeError 가능)
        )

        text = (resp.choices[0].message.content or "").strip()
        if not text:
            raise HTTPException(status_code=502, detail="llm_bad_response")

        return text

    except TypeError:
        # timeout 파라미터를 SDK가 지원하지 않는 경우를 대비한 폴백
        try:
            resp = client.chat.completions.create(
                model=use_model,
                messages=messages,
                temperature=temperature,
                top_p=top_p,
                max_tokens=max_tokens,
            )
            text = (resp.choices[0].message.content or "").strip()
            if not text:
                raise HTTPException(status_code=502, detail="llm_bad_response")
            return text
        except HTTPException:
            raise
        except Exception as e:
            logger.exception("llm_call_failed_no_timeout",
                             extra={"feature": feature, "session_id": session_id})
            raise HTTPException(status_code=502, detail="llm_upstream_error") from e

    except HTTPException:
        raise

    except Exception as e:
        # 세부 예외 분류(Timeout/RateLimit 등)를 더 하고 싶으면 여기에서 openai 예외 타입별로 분기하면 됩니다.
        logger.exception("llm_call_failed",
                         extra={"feature": feature, "session_id": session_id})
        raise HTTPException(status_code=502, detail="llm_upstream_error") from e

    finally:
        dt = int((time.time() - t0) * 1000)
        logger.info("llm_call_done",
                    extra={"feature": feature, "session_id": session_id, "latency_ms": dt})
