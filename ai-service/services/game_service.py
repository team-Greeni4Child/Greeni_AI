# game_service.py

from openai import OpenAI
from config import settings
from typing import Dict

client = OpenAI(api_key=settings.OPENAI_API_KEY)

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

    # GPT 출력이 "True"/"False"라고 가정
    correct = result.lower() == "true"

    return {"correct": correct}
