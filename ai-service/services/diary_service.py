# services/diary_service.py
from __future__ import annotations

from typing import Dict

from schemas.diary import (
    DiaryChatRequest,
    DiaryChatResponse,
    DiarySessionEndRequest,
    DiarySessionEndResponse,
    DiarySummarizeRequest,
    DiarySummarizeResponse,
    DiaryEmotion,
)

from common.llm import chat_text
from common.errors import AppError

# -------------------------
# in-memory session storage
# -------------------------
# {
#   session_id: {
#       "turns": int,
#       "texts": [str, ...]
#   }
# }
_sessions: Dict[str, Dict] = {}


def _get_session(session_id: str) -> Dict:
    if session_id not in _sessions:
        _sessions[session_id] = {
            "turns": 0,
            "texts": [],
        }
    return _sessions[session_id]


# -------------------------
# system prompts
# -------------------------
DIARY_SYSTEM_PROMPT = (
    "당신은 5~8세 어린이를 위한 일기 대화 도우미입니다. "
    "아이의 말을 존중하고, 판단하거나 훈계하지 않습니다. "
    "항상 존댓말을 사용합니다. "
    "한 번에 2~3문장으로 짧게 대답합니다. "
    "질문은 최대 1개만 합니다. "
    "아이의 감정을 대신 단정하지 말고, 스스로 표현하도록 돕습니다."
)

SUMMARY_SYSTEM_PROMPT = (
    "다음은 아이와의 일기 대화 기록입니다. "
    "이를 바탕으로 하루를 한 문단으로 요약하고, "
    "아이의 주요 감정을 하나로 추정하세요."
)

EMOTION_LABELS = ["angry", "happy", "sad", "surprised", "anxiety"]


# -------------------------
# chat (ping-pong)
# -------------------------
async def chat(req: DiaryChatRequest) -> DiaryChatResponse:
    session = _get_session(req.session_id)

    session["turns"] += 1
    session["texts"].append(req.user_text)

    messages = [
        {"role": "system", "content": DIARY_SYSTEM_PROMPT},
    ]

    # 이전 대화 문맥 추가
    for t in session["texts"][:-1]:
        messages.append({"role": "user", "content": t})
        messages.append(
            {
                "role": "assistant",
                "content": "알겠습니다. 조금 더 이야기해 주실 수 있을까요?",
            }
        )

    # 이번 발화
    messages.append({"role": "user", "content": req.user_text})

    reply = chat_text(
        messages=messages,
        feature="diary_chat",
        session_id=req.session_id,
    )

    return DiaryChatResponse(
        session_id=req.session_id,
        reply=reply,
        turn_count=session["turns"],
        status="active",
    )


# -------------------------
# explicit end
# -------------------------
async def end_session(req: DiarySessionEndRequest) -> DiarySessionEndResponse:
    session = _get_session(req.session_id)

    return DiarySessionEndResponse(
        session_id=req.session_id,
        turn_count=session["turns"],
        status="ended",
    )


# -------------------------
# summarize + emotion
# -------------------------
async def summarize(req: DiarySummarizeRequest) -> DiarySummarizeResponse:
    session = _sessions.get(req.session_id)
    if not session:
        raise AppError(
            message="해당 일기 세션을 찾을 수 없습니다.",
            code="diary_session_not_found",
            status_code=404,
        )

    diary_text = " ".join(session["texts"])

    messages = [
        {"role": "system", "content": SUMMARY_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"대화 기록:\n{diary_text}\n\n"
                "출력 형식:\n"
                "요약: <한 문단 요약>\n"
                "감정: <angry|happy|sad|surprised|anxiety>"
            ),
        },
    ]

    result = chat_text(
        messages=messages,
        feature="diary_summary",
        session_id=req.session_id,
    )

    # 매우 단순한 파싱 (후에 구조화 가능)
    summary = result
    emotion_label = "happy"

    for e in EMOTION_LABELS:
        if e in result.lower():
            emotion_label = e
            break

    # 세션 정리
    del _sessions[req.session_id]

    return DiarySummarizeResponse(
        session_id=req.session_id,
        turn_count=session["turns"],
        summary=summary,
        emotion=DiaryEmotion(
            primary=emotion_label,
            confidence=0.6,
        ),
    )
