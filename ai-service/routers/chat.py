from fastapi import APIRouter
<<<<<<< HEAD
from schemas.roleplay import RoleplayRequest
from schemas.diary import DiaryChatRequest
from services.roleplay_service import reply
=======
from schemas.roleplay import RoleplayRequest, RoleplayEndRequest
from services.roleplay_service import reply, end_reply
>>>>>>> origin/main

router = APIRouter()

@router.post("/roleplay")
<<<<<<< HEAD
def roleplay(req: RoleplayRequest):
    return reply(req)
=======
async def roleplay(req: RoleplayRequest):
    return await reply(req)

@router.post("/roleplay/close")
async def end_roleplay(req: RoleplayEndRequest):
    return await end_reply(req)
>>>>>>> origin/main
