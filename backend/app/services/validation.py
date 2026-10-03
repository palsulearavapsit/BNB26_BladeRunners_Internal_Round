from pathlib import Path

from fastapi import HTTPException, UploadFile

EXTENSION_MODALITIES = {
    "image": {".jpg", ".jpeg", ".png", ".webp", ".gif"},
    "video": {".mp4", ".mov", ".avi", ".mkv", ".webm"},
    "audio": {".mp3", ".wav", ".m4a", ".ogg", ".flac"},
    "voice": {".amr", ".3gp", ".3gpp"},
    "text": {".txt", ".md", ".csv", ".json", ".log", ".xml", ".html"},
    "document": {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx"},
}


def infer_modality(filename: str, content_type: str | None) -> str:
    suffix = Path(filename).suffix.lower()
    normalized_type = (content_type or "").split(";", 1)[0].lower()
    if normalized_type.startswith("image/"):
        return "image"
    if normalized_type.startswith("video/"):
        return "video"
    if normalized_type.startswith("audio/"):
        if "voice" in Path(filename).stem.lower() or "recording" in Path(filename).stem.lower():
            return "voice"
        return "audio"
    if normalized_type.startswith("text/"):
        return "text"
    for modality, extensions in EXTENSION_MODALITIES.items():
        if suffix in extensions:
            return modality
    return "unknown"


async def read_upload(upload: UploadFile, max_bytes: int) -> bytes:
    data = await upload.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise HTTPException(status_code=413, detail="Upload exceeds configured size limit")
    if not data:
        raise HTTPException(status_code=400, detail="Upload is empty")
    return data
