from fastapi import APIRouter, File, HTTPException, UploadFile
import httpx

from app.config.settings import get_settings

router = APIRouter(tags=["transcription"])


@router.post("/transcribe")
async def transcribe(file: UploadFile = File(...)) -> dict[str, str]:
    settings = get_settings()
    if not settings.whisper_api_key:
        raise HTTPException(status_code=503, detail="Whisper is not configured; set SATYA_WHISPER_API_KEY in backend/.env")
    payload = await file.read()
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                settings.whisper_api_url,
                headers={"Authorization": f"Bearer {settings.whisper_api_key}"},
                files={"file": (file.filename or "audio", payload, file.content_type or "application/octet-stream")},
                data={"model": "whisper-1", "response_format": "json"},
            )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="Whisper transcription failed") from exc
    result = response.json()
    return {"text": str(result.get("text", ""))}
