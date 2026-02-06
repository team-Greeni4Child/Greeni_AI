# app.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi import Request, HTTPException

from config import settings
from routers import stt, tts, game, diary, chat

from common.logging import setup_logging, get_logger
from common.errors import register_exception_handlers

# 로깅 설정
setup_logging()
log = get_logger("greeni")

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
)

# 전역 핸들러 등록
register_exception_handlers(app, logger=log)

# CORS 설정
#if settings.ENV == "dev":
#    allow_origins = ["*"]
#else:
    # 
#    allow_origins = [
#        settings.BASE_URL,
#        "https://greeni-app.com",  # 수정예정
#    ]

#app.add_middleware(
#    CORSMiddleware,
#    allow_origins=allow_origins,
#    allow_credentials=True,
#    allow_methods=["*"],
#    allow_headers=["*"],
#)

# TTS 출력 경로 # 추가한 부분 2: app.mount 주석(삭제)
# app.mount(
#     "/storage/tts",
#     StaticFiles(directory=str(settings.TTS_DIR)),
#     name="tts-files",
# )

# 라우터 설정
app.include_router(stt.router, prefix="/stt", tags=["stt"])
app.include_router(tts.router, prefix="/tts", tags=["tts"])
app.include_router(game.router, prefix="/game", tags=["game"])
app.include_router(diary.router, prefix="/diary", tags=["diary"])
app.include_router(chat.router, prefix="/chat", tags=["chat"])

# health check
@app.get("/health")
def health():
    return {"ok": True, "env": settings.ENV}

# HTTPException은 현재처럼 dict면 그대로 내려주되, 응답 형태는 고정
@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException):
    if isinstance(exc.detail, dict):
        # detail이 {"error": "...", "code": "..."} 형태면 그대로
        return JSONResponse(status_code=exc.status_code, content=exc.detail)
    # 문자열 detail도 통일된 형태로 반환
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": str(exc.detail), "code": "http_exception"},
    )

# 예기치 못한 예외는 반드시 서버 로그에 남기고, 클라이언트 응답은 통일
@app.exception_handler(Exception)
async def unhandled_exception_handler(_: Request, exc: Exception):
    log.exception("unhandled_exception", exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={"error": "internal server error", "code": "internal_error"},
    )
