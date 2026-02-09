# routers/diary.py
from fastapi import APIRouter

from schemas.diary import (
    DiaryChatRequest,
    DiaryChatResponse,
    DiarySessionEndRequest,
    DiarySessionEndResponse,
    DiarySummarizeRequest,
    DiarySummarizeResponse,
)
from services import diary_service

router = APIRouter()


@router.post("/chat", response_model=DiaryChatResponse)
async def diary_chat(req: DiaryChatRequest):
    return await diary_service.chat(req)


@router.post("/end", response_model=DiarySessionEndResponse)
async def diary_end(req: DiarySessionEndRequest):
    return await diary_service.end_session(req)


@router.post("/summarize", response_model=DiarySummarizeResponse)
async def diary_summarize(req: DiarySummarizeRequest):
    return await diary_service.summarize(req)
