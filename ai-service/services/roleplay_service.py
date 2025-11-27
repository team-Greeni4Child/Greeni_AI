# services/roleplay_service.py
from __future__ import annotations

from typing import Literal, Optional, Sequence

from openai import OpenAI
from pydantic import BaseModel, Field
from config import settings

# 내가 추가한 부분
import requests


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


# 내가 추가한 부분

def _polyglot_tone_hint(role: RoleType) -> str:
    if role == "shop":
        return (
            "말투는 시장 상인처럼 호탕하고 쾌활하게, 하지만 어린이가 듣기 편하도록 부드럽게 다듬어 주세요. "
            "너무 과장되면 안 되고, 말투만 살짝 시장 상인 느낌으로 자연스럽게 조정하세요. "
        )
    if role == "teacher":
        return (
            "말투는 따뜻하고 다정한 선생님처럼 차분하고 안정감 있게 다듬어 주세요. "
            "과한 감탄이나 감정표현 없이, 어른스럽고 부드러운 말투로 자연스럽게 조정하세요. "
        )
    if role == "friend":
        return (
            "말투는 발랄하고 귀여운 친구처럼 경쾌하게, 하지만 유치하지 않게 자연스럽게 다듬어 주세요. "
            "너무 과장되지 않은 자연스러운 친구 말투를 유지하세요. "
        )

def refine_with_polyglot_kor(text: str, role: RoleType) -> str:
    url = "https://router.huggingface.co/models/monologg/polyglot-ko-1.3b"
    headers = {"Authorization": f"Bearer {settings.HF_API_KEY}"}

    tone_hint = _polyglot_tone_hint(role)

    prompt = (
        "다음 문장의 말투와 단어 선택만 아주 조금 자연스럽게 다듬어 주세요. "
        "문장의 의미, 규칙, 역할에 따른 말투(반말/존댓말/교정 규칙)는 절대 바꾸지 마세요."
        "문장을 재창작하지 말고 표현만 부드럽게 바꿔주세요."
        f"{tone_hint}"
        f"\n\n문장: {text}\n\n출력: "
    )

    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 128,
            "temperature": 0.7,
            "top_p": 0.9
        }
    }
    res = requests.post(url, headers=headers, json=payload)
    if res.status_code == 200:
        output = res.json()
        return output[0]["generated_text"]
    else:
        print(res.status_code, res.text)
        return text

# 내가 추가한 부분 (reply 함수 수정, return 수정)
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

    refined_text = refine_with_polyglot_kor(text, req.role)

    return {
        "text": refined_text,
        "model": f"{resp.model} + polyglot-ko-1.3b",
        "usage": {
            "prompt_tokens": getattr(resp.usage, "prompt_tokens", None),
            "completion_tokens": getattr(resp.usage, "completion_tokens", None),
            "total_tokens": getattr(resp.usage, "total_tokens", None),
        },
        "raw_openai": text,
    }