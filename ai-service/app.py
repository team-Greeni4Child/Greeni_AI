# app.py
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from routers import stt, tts, game, diary, chat

# 앱 인스턴스 생성
from config import settings
app = FastAPI(title=settings.APP_NAME)

# CORS 설정: api 호출 모두 허용
# 나중에 내부에서만 접근 가능하도록 수정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 연결
app.include_router(stt.router, prefix="/stt", tags=["stt"])
app.include_router(tts.router, prefix="/tts", tags=["tts"])
app.include_router(game.router, prefix="/game", tags=["game"])
app.include_router(diary.router, prefix="/diary", tags=["diary"])
app.include_router(chat.router, prefix="/chat", tags=["chat"])

# 서버 활성 체크 (브라우저에서 열리면 시스템이 돌아가고 있는것)
@app.get("/health")
async def health():
    return {"ok": True}

# 에러 처리
@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "code": "HTTP_EXCEPTION"},
    )

@app.exception_handler(Exception)
async def unhandled_exception_handler(_: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"error": "internal server error", "code": "UNHANDLED_EXCEPTION"},
    )
