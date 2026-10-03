from uuid import UUID

from fastapi import APIRouter, Header, HTTPException

from app.config.settings import get_settings
from app.models import AnalysisResult
from app.services.storage import get_repository

router = APIRouter(tags=["analysis"])


@router.get("/analysis/{analysis_id}", response_model=AnalysisResult)
def get_analysis(analysis_id: UUID, authorization: str | None = Header(default=None)) -> AnalysisResult:
    token = authorization.removeprefix("Bearer ").strip() if authorization else None
    result = get_repository(get_settings(), token).get(analysis_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return result
