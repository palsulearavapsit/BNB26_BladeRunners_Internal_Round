import hashlib

from app.adapters.schemas import NormalizedPrediction


class DevelopmentInferenceAdapter:
    """Deterministic plumbing adapter, not a trained ML model."""

    name = "development-heuristic-placeholder"

    def predict(self, modality: str, payload: bytes, metadata: dict) -> NormalizedPrediction:
        digest = hashlib.sha256(payload).digest()
        score = round(0.35 + (digest[0] / 255) * 0.3, 3)
        return NormalizedPrediction(
            label="insufficient_evidence",
            score=score,
            signals=[f"{modality} content was received", "No genuine ML detector is configured"],
            model_name=self.name,
        )
