from fastapi import APIRouter
from services.roleplay_service import RoleplayRequest, reply

router = APIRouter(prefix="/chat", tags=["Chat"])

@router.post("/roleplay")
def roleplay(req: RoleplayRequest):
    return reply(req)
