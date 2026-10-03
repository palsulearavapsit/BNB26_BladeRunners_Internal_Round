from app.pipelines.base import run_pipeline

def analyze(payload: bytes, metadata: dict) -> dict:
    return run_pipeline("image", payload, metadata)
