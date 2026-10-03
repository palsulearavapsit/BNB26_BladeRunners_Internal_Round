from uuid import uuid4

from fastapi import APIRouter, File, Header, HTTPException, UploadFile

from app.config.settings import get_settings
from app.models import UploadResponse
from app.services.analysis import analyze_file
from app.services.storage import get_repository
from app.services.validation import infer_modality, read_upload

router = APIRouter(tags=["analysis"])

@router.post("/upload", response_model=UploadResponse)
async def upload(file: UploadFile = File(...), authorization: str | None = Header(default=None)) -> UploadResponse:
    settings = get_settings()
    modality = infer_modality(file.filename or "upload", file.content_type)
    payload = await read_upload(file, settings.max_upload_bytes)
    analysis_id = uuid4()
    try:
        result = analyze_file(analysis_id, file.filename or "upload", modality, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    get_repository(settings, authorization.removeprefix("Bearer ").strip() if authorization else None).save(result)
    return UploadResponse(analysis_id=analysis_id, filename=result.filename, modality=modality, status="completed")
