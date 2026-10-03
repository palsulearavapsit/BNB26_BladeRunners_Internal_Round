from pathlib import Path

from fastapi import HTTPException, UploadFile

ALLOWED_EXTENSIONS = {
    "image": {".jpg", ".jpeg", ".png", ".webp", ".gif"},
    "video": {".mp4", ".mov", ".avi", ".mkv", ".webm"},
    "audio": {".mp3", ".wav", ".m4a", ".ogg", ".flac"},
    "text": {".txt", ".md", ".csv", ".json"},
    "document": {".pdf", ".docx", ".xlsx", ".pptx"},
}


def infer_modality(filename: str, content_type: str | None) -> str:
    suffix = Path(filename).suffix.lower()
    for modality, extensions in ALLOWED_EXTENSIONS.items():
        if suffix in extensions:
            return modality
    if content_type and content_type.startswith("text/"):
        return "text"
    raise HTTPException(status_code=415, detail="Unsupported file type")


async def read_upload(upload: UploadFile, max_bytes: int) -> bytes:
    data = await upload.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise HTTPException(status_code=413, detail="Upload exceeds configured size limit")
    if not data:
        raise HTTPException(status_code=400, detail="Upload is empty")
    return data
