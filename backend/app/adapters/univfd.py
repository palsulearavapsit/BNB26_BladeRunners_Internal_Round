from functools import lru_cache
from io import BytesIO
import os
from pathlib import Path
from time import perf_counter

import torch
from PIL import Image, UnidentifiedImageError

from app.adapters.schemas import NormalizedPrediction
from scripts.univfd_inference import DEFAULT_CHECKPOINT, DEVICE, MODEL_NAME, load_model


class UnivFDImageAdapter:
    name = "UnivFD-CLIP-ViT-L/14"

    @staticmethod
    @lru_cache(maxsize=1)
    def _load(checkpoint_path: str):
        return load_model(Path(checkpoint_path))

    def predict(self, modality: str, payload: bytes, metadata: dict) -> NormalizedPrediction:
        if modality != "image":
            raise ValueError("UnivFDImageAdapter only supports image inputs")
        try:
            with Image.open(BytesIO(payload)) as image:
                image_rgb = image.convert("RGB")
        except (OSError, UnidentifiedImageError) as exc:
            raise ValueError("Uploaded image is invalid or unsupported") from exc

        checkpoint = Path(os.getenv("SATYA_UNIVFD_CHECKPOINT", str(DEFAULT_CHECKPOINT)))
        model = self._load(str(checkpoint))
        tensor = model.preprocess(image_rgb).unsqueeze(0).to(DEVICE)
        try:
            torch.cuda.synchronize(DEVICE)
            started = perf_counter()
            with torch.inference_mode():
                logit = model(tensor)
            torch.cuda.synchronize(DEVICE)
        except torch.cuda.OutOfMemoryError as exc:
            raise RuntimeError(
                "UnivFD ran out of CUDA memory; reduce other GPU workloads and retry"
            ) from exc

        if logit.shape != (1, 1) or not torch.isfinite(logit).all():
            raise RuntimeError("UnivFD returned an invalid inference output")
        raw_logit = float(logit[0, 0].item())
        score = float(torch.sigmoid(logit[0, 0]).item())
        return NormalizedPrediction(
            label="insufficient_evidence",
            score=score,
            signals=[
                "UnivFD binary fake/generated detector score computed on CUDA",
                "Three-class authenticity classification is not established",
            ],
            model_name=self.name,
            is_development_inference=False,
            metadata={
                "raw_logit": raw_logit,
                "sigmoid_score": score,
                "score_interpretation": "UnivFD fake/generated detector score; not calibrated",
                "device": torch.cuda.get_device_name(DEVICE),
                "inference_duration_seconds": perf_counter() - started,
                "model_name": MODEL_NAME,
            },
        )


class ExperimentalTextAdapter:
    name = "experimental-text-baseline"

    def predict(self, modality: str, payload: bytes, metadata: dict) -> NormalizedPrediction:
        if modality != "text":
            raise ValueError("ExperimentalTextAdapter only supports text inputs")
        text = payload.decode("utf-8", errors="replace").strip()
        if not text:
            raise ValueError("Text input is empty")
        return NormalizedPrediction(
            label="insufficient_evidence",
            score=0.0,
            signals=[f"Experimental baseline received {len(text)} characters"],
            model_name=self.name,
            metadata={
                "experimental": True,
                "score_interpretation": "No text-detector score is available",
            },
        )
