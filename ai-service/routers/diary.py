from fastapi import APIRouter, Path, Query
from typing import Optional
from schemas import DiaryTurnRequest, DiaryTurnResponse, DiaryComposeResponse
from services import diary_service

router = APIRouter()

@router.post("/{sid}/turn", response_model=DiaryTurnResponse)
async def add_turn(sid: str, body: DiaryTurnRequest):
    return diary_service.add_turn(
        sid=sid,
        text=body.text,
        child=body.child,
        audio_url=body.audio_url,
    )

@router.get("/{sid}/compose", response_model=DiaryComposeResponse)
async def compose(
    sid: str,
    withMemory: bool = Query(True),
    topK: int = Query(5, ge=1, le=20),
    recentDays: Optional[int] = Query(90, ge=1, le=365),
):
    return diary_service.compose(
        sid=sid,
        with_memory=withMemory,
        top_k=topK,
        recent_days=recentDays,
    )
