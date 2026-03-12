# game_service.py

import json
from openai import OpenAI
from config import settings
from typing import Dict, List

client = OpenAI(api_key=settings.OPENAI_API_KEY)

def generate_fiveq(answer: str):
    system_prompt = f"""
당신은 어린이를 위한 다섯고개 퀴즈 문제를 만듭니다. 
규칙: 
- 정답에 대한 초성힌트가 어린이에게 제공되고 있습니다. 그에 맞는 난이도의 힌트를 생성해주세요.
- 출력은 반드시 JSON 배열(문자열 5개)만 반환합니다. 번호/설명/여는말 금지. 
- 힌트는 반드시 한글로만 표현해야 합니다.
- 힌트 난이도 규칙:
1번: 정답에 가까운 유추 표현
2번: 약간 구체적인 특징
3번: 조금 더 구체적인 특징
4번: 형태 또는 행동 특징
5번: 구체적인 형태 또는 행동 특징
- 정답 단어, 동의어, 이모지, 초성을 포함하지 않습니다. 
- 힌트는 한국어로 작성하며 30자 이하의 짧은 문장이어야 합니다. 
- 8세 이하 아동도 듣고 쉽게 이해할 단어만 사용합니다.
- 존재하지 않는 특징을 거짓으로 만들지 않습니다.
- 정답을 직접 떠올리게 하는 소리, 의성어, 의태어를 사용해도 좋습니다.
말투
- 반말을 사용합니다. (예: '긴 꼬리를 가지고 있어.', '나무로 만들어진 물건이야.')
- 단, 다음과 같은 말투는 사용하지 않습니다. (예: '속에서 아기를 키운단다.', '대나무를 먹는단다.', '간편하게 점심으로 많이 먹는단다.', '눈으로 만든 친구란다.', '입이 있다네.', '소리를 내며 열고 닫는구나.')
    """

    user_prompt = f"""
아래의 "정답"을 기준으로 다섯고개 힌트를 생성하세요. 

정답: {answer}
금지어: {answer}

출력은 JSON 배열만 반환하세요. 
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=1,
        messages=[
            {"role":"system", "content":system_prompt},
            {"role":"user", "content":user_prompt},
        ]
    )

    raw = response.choices[0].message.content
    hints: List[str] = json.loads(raw)

    return {"hints": hints}

def check_fiveq(utterance: str, answer: str) -> Dict:

    prompt = f"""
아래는 어린이용 다섯고개 퀴즈입니다.

정답 단어: "{answer}"
아이의 발화: "{utterance}"

판단 기준:
1) 아이가 정답을 명확히 언급하거나, 강하게 추측하는 표현이면 정답으로 처리합니다.
   - 예: "{answer}인 것 같아", "{answer} 아닐까?", "{answer}이라고 생각해", 
         "{answer} 같아 보여", "{answer}이지?", "{answer}일 것 같아"

2) 아이가 확신이 없거나 모른다는 표현은 오답으로 처리합니다.
   - 예: "{answer}인지 잘 모르겠어", "모르겠어", "비슷한데 모르겠어", 
         "{answer}는 아닌 것 같아"

3) 아이가 정답을 직접 말하지 않는 경우는 무조건 오답입니다.

4) 출력은 반드시 "True" 또는 "False"만 반환하세요.
    - 설명은 절대 포함하지 마세요.

아이의 발화는 정답을 맞춘 것으로 볼 수 있나요?
    """

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a strict evaluator."},
            {"role": "user", "content": prompt}
        ]
    )

    result = completion.choices[0].message.content.strip()

    correct = result.lower() == "true"

    return {"correct": correct}
