from fastapi import APIRouter
from schemas import RoleplayRequest, RoleplayResponse
from services import roleplay_service

router = APIRouter()

@router.post("/roleplay", response_model=RoleplayResponse)
async def roleplay(body: RoleplayRequest):
    return roleplay_service.reply(
        sid=body.sid,
        user_text=body.text,
        with_memory=body.withMemory,
        top_k=body.topK,
        recent_days=body.recentDays,
        style=body.style,
    )
