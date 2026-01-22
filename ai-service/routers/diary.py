from fastapi import APIRouter, Path, Query
from typing import Optional
from schemas.diary import DiarySessionEndRequest, DiarySessionEndResponse, DiarySummarizeRequest, DiarySummarizeResponse
from services import diary_service

router = APIRouter()