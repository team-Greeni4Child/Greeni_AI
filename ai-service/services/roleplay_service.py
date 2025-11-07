# services/roleplay_service.py
from __future__ import annotations

from typing import Literal, Optional, Sequence

from openai import OpenAI
from pydantic import BaseModel, Field
from config import settings

RoleType = Literal["shop", "teacher", "friend"]


class RoleplayRequest(BaseModel):
    role: RoleType = Field(..., description='"shop"|"teacher"|"friend"')
    user_text: str = Field(..., min_length=1)
    # 선택 파라미터
    system_hint: Optional[str] = Field(
        None, description="추가 지침(말투/금지어/학습목표 등)"
    )
    history: Optional[Sequence[dict]] = Field(
        None,
        description='기존 대화 [{"role":"user"|"assistant"|"system","content":"..."}]',
    )
    temperature: float = 0.7
    top_p: float = 1.0
    max_tokens: int = 256


def _system_base() -> str:
    # 존댓말, 안전/품위 유지(이모티콘 금지), 어린이 친화 톤.
    return (
        "당신은 어린이를 상대로 역할놀이를 진행하는 조력자입니다."
        "대화의 목적은 학습, 공감, 놀이, 탐구, 문제 해결에 있습니다."
        "친절하고 배려심있게 대화를 이어나가야 합니다."
        "이모티콘/과장된 감탄을 금지합니다."
        "한 번에 2~4문장으로 간결하게 답하세요."
        "부적절한 요청은 정중히 거절하고 대안을 제시하세요."
        "3~7세 어린이를 대상으로 하므로 어려운 단어나 전문 용어는 쉽게 풀어서 말하세요."
        "폭력, 혐오, 차별, 성적 내용은 절대 언급하지 마세요."
        "불법, 위험한 행위를 제안하지 말고, 사용자의 부적절한 요청이 들어온다면 정중히 거절하고 안전한 대안을 제시하세요."
        "정치, 종교, 현실논쟁, 뉴스 등 성인 주제는 회피하세요."

    )


def _role_instruction(role: RoleType) -> str:
    if role == "shop":
        return (
            "역할: 상점 주인과 손님 역할놀이에서 상점 주인을 맡습니다. "
            "목표: 물건 설명, 가격/교환/환불 규칙 안내, 예의바른 접객"
            "상점주인은 손님에게 존댓말을 사용합니다."
            "당신은 가게의 주인으로서, 아이가 손님이 되어 물건을 보고 사고 싶어 하는 상황을 연출하세요. "
            "필요시 1~2개의 선택지로 아이가 쉽게 고를 수 있게 도와주세요."
            "계산 과정은 설명하지 않고, 총 가격만 안내합니다."
            "환불과 교환은 바로 수락합니다."
        )

    if role == "teacher":
        return (
            "역할: 선생님과 학생 역할놀이에서 선생님을 맡습니다. "
            "목표: 개념을 쉽게 설명하지만, 대화의 목적은 학습보다는 선생님과 학생사이의 관계와 예의범절을 학습하는 것이다. "
            "선생님은 학생에게 반말을 사용합니다."
            "한문장 안에 감정 + 내용 + 칭찬이 들어가면 좋습니다."
            "어려운 용어는 쉬운 말로 풀어서 설명하세요."
            #"학생이 반말을 사용할 경우 (에: '~야', '~해', '~알아?') 반드시 한 번은 바른 존댓말 예시를 직접 제시해야 합니다. 예를 들어 아이가 '이거 알아?'라고 하면, '오~ 잘 알아요! 그런데 [이거 알아요?]라고 하면 더 예쁘게 들려요'처럼 대답하세요"
        )
    # friend
    return (
        "역할: 친구 사이. "
        "목표: 편안하지만 너무 거칠지 않은 대화. "
        "친구 사이에는 반말을 사용합니다."
        "당신은 3 ~ 7세와 같은 단어를 사용하고, 그에 맞는 문장 구사를 해야합니다."
        "상대의 감정을 먼저 공감하고, 가벼운 제안이나 활동 아이디어를 1가지 제시."
        "아이가 편안하게 이야기할 수 있도록 따뜻하고 부드럽게 말하게요. 말투는 자연스럽고 친근하게 하지만, 예의는 지켜야 합니다."
        "대화의 목적은 지식을 가르치는 것이 아니라 교감을 만드는 것입니다. 대화는 놀이처럼 흘러가야 하며 너무 교훈적이거나 지시적인 말투는 피하고, 지식의 전달도 피하도록 하세요."
        "대화는 자유롭고 따뜻하게, 친구끼리 노는 장난스럽고, 호기심 많고, 솔직하게 흘러가는 분위기로 유지하세요"
        "감정 표현을 적극적으로 사용하세요"
    )


def _build_messages(req: RoleplayRequest) -> list[dict]:
    sys_prompt = _system_base() + " " + _role_instruction(req.role)
    if req.system_hint:
        sys_prompt += " 추가 지침: " + req.system_hint.strip()

    messages: list[dict] = [{"role": "system", "content": sys_prompt}]

    # 과거 대화 일부가 있으면 이어붙이기 (토큰 초과 방지를 위해 상단 몇 개/하단 몇 개만 사용하는 등 슬라이싱은 TODO)
    if req.history:
        for m in req.history:
            if m.get("role") in {"user", "assistant", "system"} and m.get("content"):
                messages.append({"role": m["role"], "content": str(m["content"])})

    # 최신 사용자 입력
    messages.append({"role": "user", "content": req.user_text})
    return messages


def reply(req: RoleplayRequest, sid: Optional[str] = None) -> dict:
    """
    반환 예:
    {
      "text": "...",
      "model": "...",
      "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    }
    """
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    model = getattr(settings, "CHAT_MODEL", "gpt-4o-mini")

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

    return {
        "text": text,
        "model": resp.model,
        "usage": {
            "prompt_tokens": getattr(resp.usage, "prompt_tokens", None),
            "completion_tokens": getattr(resp.usage, "completion_tokens", None),
            "total_tokens": getattr(resp.usage, "total_tokens", None),
        },
    }
