"""Central registry for model adapters."""
from app.adapters.development import DevelopmentInferenceAdapter
from app.adapters.schemas import NormalizedPrediction
from app.adapters.univfd import ExperimentalTextAdapter, UnivFDImageAdapter

_ADAPTER = DevelopmentInferenceAdapter()
_IMAGE_ADAPTER = UnivFDImageAdapter()
_TEXT_ADAPTER = ExperimentalTextAdapter()


def get_inference_adapter() -> DevelopmentInferenceAdapter:
    return _ADAPTER


def predict(modality: str, payload: bytes, metadata: dict) -> NormalizedPrediction:
    if modality == "image":
        return _IMAGE_ADAPTER.predict(modality, payload, metadata)
    if modality == "text":
        return _TEXT_ADAPTER.predict(modality, payload, metadata)
    return _ADAPTER.predict(modality, payload, metadata)
