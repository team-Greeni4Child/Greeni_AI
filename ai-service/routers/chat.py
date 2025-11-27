from fastapi import APIRouter
from services.roleplay_service import RoleplayRequest, reply

router = APIRouter()

@router.post("/roleplay")
def roleplay(req: RoleplayRequest):
    return reply(req)
