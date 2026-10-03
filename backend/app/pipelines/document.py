from app.pipelines.base import run_pipeline

def analyze(payload: bytes, metadata: dict, extraction_notes: list[str]) -> dict:
    return run_pipeline("document", payload, metadata, extraction_notes)
