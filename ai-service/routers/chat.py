from fastapi import APIRouter
from schemas.roleplay import RoleplayRequest, RoleplayEndRequest
from services.roleplay_service import reply, end_reply

router = APIRouter()

@router.post("/roleplay")
def roleplay(req: RoleplayRequest):
    return reply(req)

@router.post("/roleplay/close")
async def end_roleplay(req: RoleplayEndRequest):
    return await end_reply(req)