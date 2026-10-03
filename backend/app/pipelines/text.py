from app.pipelines.base import run_pipeline


def analyze(payload: bytes, metadata: dict, extraction_notes: list[str] | None = None) -> dict:
    return run_pipeline("text", payload, metadata, extraction_notes)
