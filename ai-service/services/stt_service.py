import os, uuid, shutil, subprocess
from typing import Optional
from schemas.stt import STTResponse
from openai import OpenAI

client = OpenAI()

# Whisper가 무리 없이 처리하는 대표 확장자 목록
SUPPORTED_EXTS = {
    ".mp3", ".mp4", ".mpeg", ".mpga", ".m4a",
    ".wav", ".webm", ".ogg", ".oga", ".flac"
}

def ext(path: str) -> str:
    return os.path.splitext(path)[1].lower()

def have_ffmpeg() -> bool:
    return shutil.which("ffmpeg") is not None

async def transcribe_file(
    audio_bytes: bytes,
    filename: str,
    purpose: str,
    store_audio: bool = False,
    session_id: str = None
) -> STTResponse:
    
    unique = uuid.uuid4().hex
    ext = os.path.splitext(filename)[1].lower() if filename else ".bin"
    temp_dir = os.path.abspath("./tmp_stt")
    os.makedirs(temp_dir, exist_ok=True)

    temp_input_path = os.path.join(temp_dir, f"in_{unique}{ext}")
    temp_output_path: Optional[str] = None

    # 1) 바이너리 데이터를 임시 파일로 저장
    with open(temp_input_path, "wb") as f:
        f.write(audio_bytes)

    use_path = temp_input_path

    try:
        # 2) FFmpeg 변환 로직
        if ext not in SUPPORTED_EXTS and shutil.which("ffmpeg"):
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
 
        # 3) Whisper 호출
        with open(use_path, "rb") as audio_file:
            fname = os.path.basename(use_path) 
            
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=(fname, audio_file),  
                language="ko",
                response_format="text",
            )

        text_out = transcript if isinstance(transcript, str) else getattr(transcript, "text", str(transcript))
        return STTResponse(text=text_out, audio_url=None)

    finally:
        # 4) 임시 파일 정리
        for path in [temp_input_path, temp_output_path]:
            if path and os.path.exists(path):
                os.remove(path)
