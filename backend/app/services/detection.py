from app.adapters.schemas import NormalizedPrediction
from app.model_registry import predict


def detect(modality: str, payload: bytes, metadata: dict) -> NormalizedPrediction:
    return predict(modality, payload, metadata)
