# stt_service.py

import os
import uuid
import shutil
import subprocess
from typing import Optional

from openai import OpenAI
from fastapi import UploadFile

client = OpenAI()

# Whisper가 무리 없이 처리하는 대표 확장자 목록
SUPPORTED_EXTS = {
    ".mp3", ".mp4", ".mpeg", ".mpga", ".m4a",
    ".wav", ".webm", ".ogg", ".oga", ".flac"
}

def _ext(path: str) -> str:
    return os.path.splitext(path)[1].lower()

def _have_ffmpeg() -> bool:
    return shutil.which("ffmpeg") is not None

async def transcribe(file: UploadFile):
    """
    Transcribes an audio file using OpenAI's Whisper model,
    without relying on pyaudioop/pydub.
    """
    # 1) 업로드 파일을 임시 경로에 저장
    unique = uuid.uuid4().hex
    original_suffix = _ext(file.filename) or ".bin"
    temp_dir = os.path.abspath("./.tmp_stt")
    os.makedirs(temp_dir, exist_ok=True)

    temp_input_path = os.path.join(temp_dir, f"in_{unique}{original_suffix}")
    temp_output_path: Optional[str] = None

    contents = await file.read()
    with open(temp_input_path, "wb") as f:
        f.write(contents)

    # 2) 필요 시 FFmpeg 변환 시도 (mp3 16kHz mono)
    use_path = temp_input_path
    try:
        if _ext(temp_input_path) not in SUPPORTED_EXTS and _have_ffmpeg():
            temp_output_path = os.path.join(temp_dir, f"conv_{unique}.mp3")
            # -y: overwrite, -vn: no video, -ar 16000: 16kHz, -ac 1: mono, -b:a 64k: 적당한 비트레이트
            cmd = [
                "ffmpeg", "-y",
                "-i", temp_input_path,
                "-vn", "-ar", "16000", "-ac", "1", "-b:a", "64k",
                temp_output_path,
            ]
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            use_path = temp_output_path
    except Exception as e:
        # 변환 실패 시 원본으로 폴백
        print(f"[STT] FFmpeg 변환 실패, 원본으로 진행합니다: {e}")
        use_path = temp_input_path

    # 3) Whisper 호출
    try:
        with open(use_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="ko",
                response_format="text",
            )

        # SDK 버전에 따라 문자열 또는 객체일 수 있음 → 안전 처리
        if isinstance(transcript, str):
            text_out = transcript
        else:
            # 객체 형태라면 .text 속성 사용
            text_out = getattr(transcript, "text", str(transcript))

        return {"text": text_out, "audio_url": None}

    finally:
        # 4) 임시 파일 정리
        try:
            if os.path.exists(temp_input_path):
                os.remove(temp_input_path)
        except Exception:
            pass
        if temp_output_path:
            try:
                if os.path.exists(temp_output_path):
                    os.remove(temp_output_path)
            except Exception:
                pass
