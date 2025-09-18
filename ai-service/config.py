# config.py
# 환경변수 설정 + 어플리케이션 이름 설정
# 사용 시 import config 
import os
from dataclasses import dataclass

@dataclass
class Settings:
    APP_NAME: str = os.getenv("APP_NAME", "Greeni")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    TTS_PROVIDER: str = os.getenv("TTS_PROVIDER", "clova")
    CLOVA_API_KEY_ID: str = os.getenv("CLOVA_API_KEY_ID", "")
    CLOVA_API_KEY: str = os.getenv("CLOVA_API_KEY", "")

settings = Settings()

# 추후 CORS, 앱, 로그 추가
# 타임아웃/리트라이 추가
# 파일경로 및 접근 제한 추가
# 모델 및 명세서 추가