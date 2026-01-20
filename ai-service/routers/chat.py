from fastapi import APIRouter
from schemas.roleplay import RoleplayRequest
from schemas.diary import DiaryChatRequest
from services.roleplay_service import reply

router = APIRouter()

@router.post("/roleplay")
def roleplay(req: RoleplayRequest):
    return reply(req)