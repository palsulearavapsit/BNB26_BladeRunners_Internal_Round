"""Central registry for model adapters."""
from app.adapters.development import DevelopmentInferenceAdapter
from app.adapters.schemas import NormalizedPrediction

_ADAPTER = DevelopmentInferenceAdapter()


def get_inference_adapter() -> DevelopmentInferenceAdapter:
    return _ADAPTER


def predict(modality: str, payload: bytes, metadata: dict) -> NormalizedPrediction:
    return _ADAPTER.predict(modality, payload, metadata)
