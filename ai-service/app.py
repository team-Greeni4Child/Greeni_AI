# app.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi import Request, HTTPException

from config import settings
from routers import stt, tts, game, diary, chat

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
)

# CORS 설정
if settings.ENV == "dev":
    allow_origins = ["*"]
else:
    # 
    allow_origins = [
        settings.BASE_URL,
        "https://greeni-app.com",  # 수정예정
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# TTS 출력 경로
app.mount(
    "/storage/tts",
    StaticFiles(directory=str(settings.TTS_DIR)),
    name="tts-files",
)

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

# exception 처리
@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail},
    )

@app.exception_handler(Exception)
async def unhandled_exception_handler(_: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"error": "internal server error"},
    )
