from app.services.detection import detect
from app.services.explanation import explain
from app.services.confidence import calibrate


def run_pipeline(modality: str, payload: bytes, metadata: dict, extraction_notes: list[str] | None = None) -> dict:
    prediction = detect(modality, payload, metadata)
    summary, evidence, limitations = explain(prediction, extraction_notes or [])
    return {
        "label": prediction.label,
        "confidence": 0.0 if prediction.model_name == "UnivFD-CLIP-ViT-L/14" else calibrate(prediction.score, len(evidence)),
        "summary": summary,
        "evidence": evidence,
        "limitations": limitations,
        "metadata": {
            "model_name": prediction.model_name,
            "development_inference": prediction.is_development_inference,
            **prediction.metadata,
        },
        "is_development_inference": prediction.is_development_inference,
    }
