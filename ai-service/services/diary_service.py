# services/diary_service.py
from __future__ import annotations

import json
from typing import Dict, Any

from langchain_classic.memory import ConversationBufferMemory

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

_memory_storage: Dict[str, ConversationBufferMemory] = {}


def _get_memory(session_id: str) -> ConversationBufferMemory:
    if session_id not in _memory_storage:
        _memory_storage[session_id] = ConversationBufferMemory(
            return_messages=True,
            memory_key="chat_history",
        )
    return _memory_storage[session_id]


def _turn_count(memory: ConversationBufferMemory) -> int:
    return len(memory.chat_memory.messages) // 2


def _serialize_history(memory: ConversationBufferMemory) -> str:
    history_messages = memory.load_memory_variables({})["chat_history"]
    lines = []
    for msg in history_messages:
        speaker = "아이" if msg.type == "human" else "그리니"
        lines.append(f"{speaker}: {msg.content}")
    return "\n".join(lines).strip()


DIARY_SYSTEM_PROMPT = (
    "당신은 5~8세 어린이를 위한 일기 대화 도우미입니다. "
    "아이의 말을 존중하고, 판단하거나 훈계하지 않습니다. "
    "항상 존댓말을 사용합니다. "
    "한 번에 2~3문장으로 짧게 대답합니다. "
    "질문은 최대 1개만 합니다. "
    "아이의 감정을 대신 단정하지 말고, 스스로 표현하도록 돕습니다."
)

SUMMARY_SYSTEM_PROMPT = (
    "당신은 일기 대화 기록을 요약하는 도우미입니다. "
    "반드시 JSON만 출력해야 합니다. "
    "JSON 외 텍스트(설명/문장/코드블록 표기 등)는 절대 출력하지 마세요."
)

EMOTION_LABELS = ["angry", "happy", "sad", "surprised", "anxiety"]


CLOSING_PROMPT = (
    "이제 오늘의 일기 대화를 마무리해야 합니다. "
    "아이의 이야기를 따뜻하게 정리해주고, "
    "오늘 이야기해줘서 고맙다고 말해주세요. "
    "질문은 하지 마세요. "
    "2~3문장으로 부드럽게 마무리하세요."
)


async def chat(req: DiaryChatRequest) -> DiaryChatResponse:
    memory = _get_memory(req.session_id)
    history_messages = memory.load_memory_variables({})["chat_history"]

    # 현재 턴 수 계산 (assistant 응답 기준)
    tc = _turn_count(memory)

    # 이번 응답이 10번째가 되도록 마무리 유도 여부 판단
    is_closing_turn = tc >= 9

    messages: list[dict[str, str]] = [
        {"role": "system", "content": DIARY_SYSTEM_PROMPT}
    ]

    # 10턴 도달 직전이면 마무리 프롬프트 추가
    if is_closing_turn:
        messages.append(
            {"role": "system", "content": CLOSING_PROMPT}
        )

    # 기존 대화 히스토리 반영
    for msg in history_messages:
        role = "user" if msg.type == "human" else "assistant"
        messages.append({"role": role, "content": msg.content})

    # 이번 사용자 입력 추가
    messages.append({"role": "user", "content": req.user_text})

    # LLM 호출
    reply = chat_text(
        messages=messages,
        feature="diary_chat",
        session_id=req.session_id,
    )

    # 메모리 저장
    memory.save_context({"input": req.user_text}, {"output": reply})

    # 저장 후 턴 수 재계산
    tc = _turn_count(memory)

    # 10턴 도달 시 대화 종료 상태 반환 (memory는 유지)
    if tc >= 10:
        return DiaryChatResponse(
            session_id=req.session_id,
            reply=reply,
            turn_count=tc,
            status="completed",
        )

    # 일반 진행 상태
    return DiaryChatResponse(
        session_id=req.session_id,
        reply=reply,
        turn_count=tc,
        status="active",
    )



async def end_session(req: DiarySessionEndRequest) -> DiarySessionEndResponse:
    # 일기쓰기 자체를 종료 -> memory 삭제
    # 대화를 종료하고 일기 summary로 넘어감 -> memory 삭제 x
    memory = _get_memory(req.session_id)
    turn_count = _turn_count(memory)

    if req.status != "completed":
        memory.clear()
        del _memory_storage[req.session_id]

        return DiarySessionEndResponse(
        session_id=req.session_id,
        turn_count=_turn_count,
        status="ended",
    )
        
    return DiarySessionEndResponse(
        session_id=req.session_id,
        turn_count=turn_count,
        status=req.status,
    )


async def summarize(req: DiarySummarizeRequest) -> DiarySummarizeResponse:
    memory = _memory_storage.get(req.session_id)
    if not memory:
        raise AppError(
            message="해당 일기 세션을 찾을 수 없습니다.",
            code="diary_session_not_found",
            status_code=404,
        )

    diary_text = _serialize_history(memory)
    tc = _turn_count(memory)

    user_prompt = {
        "dialogue": diary_text,
        "labels": EMOTION_LABELS,
        "output_schema": {
            "summary": "string (Korean, 2~4 sentences, one paragraph)",
            "emotion": {"primary": "one of labels", "confidence": "number 0.0~1.0"},
        },
        "rules": [
            "출력은 반드시 JSON 객체 1개만",
            "키는 summary, emotion만 사용",
            "emotion.primary는 labels 중 1개",
            "emotion.confidence는 0.0~1.0",
        ],
    }

    result = chat_text(
        messages=[
            {"role": "system", "content": SUMMARY_SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(user_prompt, ensure_ascii=False)},
        ],
        feature="diary_summary",
        session_id=req.session_id,
    )

    # 파싱 및 exception 처리
    parsed: Dict[str, Any]
    try:
        parsed = json.loads(result)
    except Exception:
        # 최소 폴백: 전체 문자열을 summary로 처리
        parsed = {
            "summary": result.strip(),
            "emotion": {"primary": "happy", "confidence": 0.5},
        }

    summary = str(parsed.get("summary", "")).strip() or "오늘 이야기를 정리하기가 어려웠어요."
    emo = parsed.get("emotion") or {}
    primary = str(emo.get("primary", "happy"))
    if primary not in EMOTION_LABELS:
        primary = "happy"
    try:
        confidence = float(emo.get("confidence", 0.6))
    except Exception:
        confidence = 0.6
    confidence = max(0.0, min(1.0, confidence))

    # 현재는 기존처럼 세션 종료 후 메모리 삭제(원하시면 여기 대신 Vector DB 저장으로 교체)
    memory.clear()
    del _memory_storage[req.session_id]

    return DiarySummarizeResponse(
        session_id=req.session_id,
        turn_count=tc,
        summary=summary,
        emotion=DiaryEmotion(primary=primary, confidence=confidence),
    )
