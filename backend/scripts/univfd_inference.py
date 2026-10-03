"""Run the UnivFD binary image detector on CUDA."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

import torch
from PIL import Image, UnidentifiedImageError

from univfd.clip_models import CLIPModel


MODEL_NAME = "ViT-L/14"
DEVICE = torch.device("cuda:0")
DEFAULT_CHECKPOINT = (
    Path(__file__).resolve().parents[1] / "models" / "image" / "fc_weights.pth"
)


def load_model(checkpoint_path: Path) -> CLIPModel:
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is required for UnivFD inference, but it is unavailable")

    model = CLIPModel(MODEL_NAME)
    checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=True)
    model.fc.load_state_dict(checkpoint, strict=True)
    model = model.to(DEVICE)
    model.eval()

    if any(parameter.device != DEVICE for parameter in model.parameters()):
        raise RuntimeError("UnivFD model parameters were not placed on cuda:0")

    return model


def infer_image(
    image_path: Path,
    checkpoint_path: Path = DEFAULT_CHECKPOINT,
) -> dict[str, Any]:
    if not image_path.is_file():
        raise FileNotFoundError(f"Image file does not exist: {image_path}")

    model = load_model(checkpoint_path)

    try:
        with Image.open(image_path) as image:
            image_rgb = image.convert("RGB")
    except (UnidentifiedImageError, OSError) as exc:
        raise ValueError(f"Unsupported or invalid image: {image_path}") from exc

    image_tensor = model.preprocess(image_rgb).unsqueeze(0).to(DEVICE)

    try:
        torch.cuda.synchronize(DEVICE)
        started = time.perf_counter()
        with torch.inference_mode():
            logit = model(image_tensor)
        torch.cuda.synchronize(DEVICE)
    except torch.cuda.OutOfMemoryError as exc:
        raise RuntimeError(
            "CUDA out of memory during UnivFD inference; no CPU fallback was attempted"
        ) from exc

    if logit.shape != (1, 1) or not torch.isfinite(logit).all():
        raise RuntimeError("UnivFD inference returned an invalid logit")

    raw_logit = float(logit[0, 0].item())
    sigmoid_score = float(torch.sigmoid(logit[0, 0]).item())
    return {
        "raw_logit": raw_logit,
        "sigmoid_score": sigmoid_score,
        "device": torch.cuda.get_device_name(DEVICE),
        "inference_duration_seconds": time.perf_counter() - started,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path, help="Path to an image file")
    parser.add_argument(
        "--checkpoint",
        type=Path,
        default=DEFAULT_CHECKPOINT,
        help=f"Classifier checkpoint (default: {DEFAULT_CHECKPOINT})",
    )
    args = parser.parse_args()

    try:
        result = infer_image(args.image, args.checkpoint)
    except (FileNotFoundError, RuntimeError, ValueError) as exc:
        parser.error(str(exc))

    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
