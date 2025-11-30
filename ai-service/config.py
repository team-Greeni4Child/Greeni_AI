# config.py
import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

@dataclass
class Settings:
    APP_NAME: str = os.getenv("APP_NAME", "Greeni-AI-Service")
    ENV: str = os.getenv("ENV", "dev")  # dev / prod

    BASE_URL: str = os.getenv("BASE_URL", "http://localhost:8000")

    STORAGE_DIR: Path = BASE_DIR / "storage"
    TTS_DIR: Path = STORAGE_DIR / "tts"

    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    HF_API_KEY: str = os.getenv("HF_API_KEY","")
    TTS_PROVIDER: str = os.getenv("TTS_PROVIDER", "clova")
    CLOVA_API_KEY_ID: str = os.getenv("CLOVA_API_KEY_ID", "")
    CLOVA_API_KEY: str = os.getenv("CLOVA_API_KEY", "")

settings = Settings()

# 디렉토리 설정 (없으면 만들어줌)
settings.TTS_DIR.mkdir(parents=True, exist_ok=True)
