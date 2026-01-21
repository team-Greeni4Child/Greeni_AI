# services/roleplay_service.py
from __future__ import annotations

from typing import Literal, Optional
from openai import OpenAI
from config import settings

from schemas.roleplay import RoleplayRequest, RoleplayResponse
from schemas.roleplay import RoleplayEndRequest, RoleplayEndResponse

from langchain_classic.memory import ConversationBufferMemory
import os

RoleType = Literal["shop", "teacher", "friend"]

_memory_storage = {}

def _get_memory(session_id: str) -> ConversationBufferMemory:
    # 세션 ID에 해당하는 메모리 객체를 가져오거나 생성.
    if session_id not in _memory_storage:
        _memory_storage[session_id] = ConversationBufferMemory(
            return_messages=True,
            memory_key="chat_history"
        )
    return _memory_storage[session_id]

def _system_base() -> str:
    # 존댓말, 안전/품위 유지(이모티콘 금지), 어린이 친화 톤.
    return (
        "당신은 3~7세 어린이를 상대로 역할놀이를 진행하는 조력자 '그리니'입니다."
        "이모티콘/과장된 감탄을 금지합니다."
        "한 번에 2~4문장으로 간결하게 답하세요."
        "부적절한 요청은 정중히 거절하고 대안을 제시하세요."
        "어려운 단어나 전문 용어는 쉽게 풀어서 말하세요."
        "폭력, 혐오, 차별, 성적 내용은 절대 언급하지 마세요."
        "불법, 위험한 행위를 제안하지 말고, 사용자의 부적절한 요청이 들어온다면 정중히 거절하고 안전한 대안을 제시하세요."
        "정치, 종교, 현실논쟁, 뉴스 등 성인 주제는 회피하세요."

    )


def _role_instruction(role: RoleType) -> str:
    if role == "shop":
        return (
            "역할: 상점 주인과 손님 역할놀이에서 상점 주인을 맡습니다. 아이는 손님 역할을 맡으며, 아이의 호칭은 '손님'입니다"
            "목표: 물건 설명, 가격/교환/환불 규칙 안내, 예의바른 접객"
            "역할에 알맞은 말투를 사용해야 합니다. '상점 주인' 역할일 때는 존댓말을 사용하세요." 
            "당신은 가게의 주인으로서, 아이가 손님이 되어 물건을 보고 사고 싶어 하는 상황을 연출하세요. "
            "필요시 1~2개의 선택지로 아이가 쉽게 고를 수 있게 도와주세요."
            "계산 과정은 설명하지 않고, 총 가격만 안내합니다."
            "환불과 교환은 바로 수락합니다."
        )

    if role == "teacher":
        return (
            "절대 규칙 : 역할에 알맞은 말투를 사용해야 합니다. 당신은 무조건 반말만 사용합니다. 존댓말은 절대 사용할 수 없습니다." 
            "역할: 선생님과 학생 역할놀이에서 선생님을 맡습니다. 아이는 학생 역할을 맡습니다."
            "목표: 개념을 쉽게 설명하지만, 대화의 목적은 학습보다는 선생님과 학생사이의 관계와 예의범절을 학습하는 것입니다. "
            "당신은 학생에게 무조건 반말을 사용합니다. 선생님이 학생에게 절대로 존댓말을 사용할 수 없습니다."
            "학생 발화가 이미 존댓말이면 절대 교정하지 말고 반응만 해야 합니다. '예뻐요', '고마워요', '맞아요'처럼 '~요', '~예요', '~이에요', '~습니다'로 끝나는 문장에는 절대 교정을 시도해서는 안 됩니다."
            "학생은 선생님에게 반말을 사용하면 안 됩니다. 학생이 선생님에게 반말을 사용할 경우, 선생님은 반드시 학생의 말투를 교정해줘야 합니다."
            "학생이 반말을 사용할 경우 (예: '예뻐', '멋있어', '배고파', '졸려', '해줘'), 반드시 한 번은 바른 존댓말 예시를 직접 제시해야 합니다. "
            "학생의 모든 발화에 대해, 반말이 들어가면 반드시 '~요'로만 교정을 하세요."
            "한문장 안에 감정 + 내용 + 칭찬이 들어가면 좋습니다."
            "어려운 용어는 쉬운 말로 풀어서 설명하세요."
        )

    # friend
    return (
        "역할: 친구 사이. "
        "목표: 편안하지만 너무 거칠지 않은 대화. "
        "역할에 알맞은 말투를 사용해야 합니다. '친구' 역할일 때는 반말을 사용하세요." 
        "문장은 '~해', '~야', '~있어' 형태로 끝나도록 작성하세요."
        "말투는 부드럽고 따뜻하게, 3 ~ 7세 아이와 어울리는 쉬운 표현과 문장을 구사하세요."
        "지식을 가르치려 하지 말고 감정 공감 중심으로 대화하세요."
        "말투는 자연스럽고 친근하게 하지만, 예의는 지켜야 합니다."
        "대화는 자연스럽고 솔직하고 편안한 친구 분위기를 유지하세요."
        "아이가 부정적 감정을 말하면, 바로 긍정적인 화제로 전환하지 않고 아이의 감정에 대해 먼저 이야기해보세요. 아이의 기분을 풀어주는 것 보다는 아이가 자신의 감정을 살펴볼 수 있게 도와주세요."
    )


def _build_messages(req: RoleplayRequest) -> list[dict]:
    # messages에 system prompt 생성
    sys_prompt = _system_base() + " " + _role_instruction(req.role)

    # 과거 대화 내역 가져오기 (dict 형식으로 변환)
    memory = _get_memory(req.session_id)
    history_messages = memory.load_memory_variables({})["chat_history"]

    # 현재 턴수 가져오기
    current_turn = len(memory.chat_memory.messages) // 2

    # 이번이 마지막 턴인 경우, 작별 인사 추가
    if current_turn==9:
        sys_prompt = (
            "★★★ [CRITICAL: FINAL MESSAGE] ★★★\n"
            "이번이 아이와 나누는 오늘의 마지막 대화입니다."
            "사용자가 어떤 질문을 하더라도 대화를 확장하지 마세요."
            "다정하게 작별 인사를 하고 대화 주제를 자연스럽게 마무리하세요."
        ) + sys_prompt
    
    # 메시지 리스트 조립
    messages: list[dict] = [{"role": "system", "content": sys_prompt}]

    # 과거 대화 내역 추가 (dict 형식으로 변환)
    for msg in history_messages:
        role = "user" if msg.type == "human" else "assistant"
        messages.append({"role": role, "content": msg.content})

    # 이번이 마지막 턴인 경우, 작별 인사 추가
    if current_turn==9:
        messages.append({"role": "system", "content": sys_prompt})

    # 현재 유저 질문 추가
    messages.append({"role": "user", "content": req.user_text})

    return messages

async def end_reply(req: RoleplayEndRequest) -> RoleplayEndResponse:
    if req.session_id in _memory_storage:
        _memory_storage[req.session_id].clear()
        del _memory_storage[req.session_id]
    
    return RoleplayEndResponse(
        session_id=req.session_id
    )

def reply(req: RoleplayRequest) -> RoleplayResponse:
    """
    반환 예:
    {
      "text": "...",
      "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    }
    """
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    model = getattr(settings, "CHAT_MODEL", "gpt-4o")

    messages = _build_messages(req)

    # TODO: 필요 시 여기서 RAG 문맥을 삽입 (Vector DB 검색 결과를 system 또는 assistant role로 prepend)

    resp = client.chat.completions.create(
        model=model, 
        messages=messages,
        temperature=req.temperature,
        top_p=req.top_p,
        max_tokens=req.max_tokens,
    )

    choice = resp.choices[0].message
    text = (choice.content or "").strip()

    # 대화 내용 저장
    memory = _get_memory(req.session_id)
    memory.save_context(
        {"input": req.user_text},
        {"output": text}
    )

    ## 턴수 세기
    total_message = len(memory.chat_memory.messages)
    current_turn = total_message // 2

    ## 10턴이 끝나면 해당 세션 대화 지우기
    if current_turn>=10:
        if req.session_id in _memory_storage:
            _memory_storage[req.session_id].clear()
            del _memory_storage[req.session_id]

    return RoleplayResponse(
        session_id=req.session_id,
        reply=text,
        turn=current_turn 
    )