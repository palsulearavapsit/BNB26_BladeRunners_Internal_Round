from datetime import datetime, timezone
from uuid import UUID

from app.models import AnalysisResult
from app.pipelines import audio, document, image, text, video
from app.services.extraction import extract_text


def analyze_file(analysis_id: UUID, filename: str, modality: str, payload: bytes) -> AnalysisResult:
    metadata: dict = {"byte_size": len(payload)}
    if modality == "image":
        output = image.analyze(payload, metadata)
    elif modality == "video":
        output = video.analyze(payload, metadata)
    elif modality in {"audio", "voice"}:
        output = audio.analyze(payload, metadata)
    elif modality == "text":
        extracted, notes = extract_text(filename, payload)
        metadata["extracted_characters"] = len(extracted or "")
        output = text.analyze(payload, metadata, notes)
    else:
        extracted, notes = extract_text(filename, payload)
        metadata["extracted_characters"] = len(extracted or "")
        output = document.analyze(payload, metadata, notes)
    return AnalysisResult(
        analysis_id=analysis_id, filename=filename, modality=modality,
        created_at=datetime.now(timezone.utc), **output,
    )
