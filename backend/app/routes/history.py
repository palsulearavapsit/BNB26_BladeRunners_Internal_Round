from fastapi import APIRouter, Header

from app.config.settings import get_settings
from app.models import HistoryItem
from app.services.storage import get_repository

router = APIRouter(tags=["history"])

@router.get("/history", response_model=list[HistoryItem])
def history(authorization: str | None = Header(default=None)) -> list[HistoryItem]:
    token = authorization.removeprefix("Bearer ").strip() if authorization else None
    return get_repository(get_settings(), token).history()
