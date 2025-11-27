# storage/files.py
import uuid
import datetime
from pathlib import Path
import asyncio

BASE_DIR = Path("storage")
TTS_DIR = BASE_DIR / "tts"

def save_tts_file(audio_bytes: bytes) -> Path:
    """TTS mp3 파일을 storage/tts 폴더에 저장"""
    TTS_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    file_id = uuid.uuid4().hex[:8]
    filename = f"tts_{timestamp}_{file_id}.mp3"

    filepath = TTS_DIR / filename

    with open(filepath, "wb") as f:
        f.write(audio_bytes)

    return filepath


async def delete_after_delay(filepath: Path, delay: int = 300):
    """파일을 일정 시간 뒤 삭제"""
    await asyncio.sleep(delay)
    if filepath.exists():
        filepath.unlink()
