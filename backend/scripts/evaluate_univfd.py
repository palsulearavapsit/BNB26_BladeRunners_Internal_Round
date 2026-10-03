"""Evaluate UnivFD scores on a documented, folder-labeled image dataset."""

from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
import time
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Callable, Iterable

import torch
from PIL import Image, UnidentifiedImageError

from scripts.univfd_inference import (
    DEFAULT_CHECKPOINT,
    DEVICE,
    MODEL_NAME,
    load_model,
)


CATEGORIES = ("authentic", "manipulated", "synthetic")
IMAGE_SUFFIXES = frozenset({".bmp", ".gif", ".jpeg", ".jpg", ".png", ".tif", ".tiff", ".webp"})


@dataclass(frozen=True)
class DatasetSample:
    path: Path
    category: str


def discover_samples(dataset_root: Path) -> list[DatasetSample]:
    """Discover images using category directory names as evaluation labels."""
    if not dataset_root.is_dir():
        raise FileNotFoundError(f"Dataset directory does not exist: {dataset_root}")

    missing = [category for category in CATEGORIES if not (dataset_root / category).is_dir()]
    if missing:
        raise FileNotFoundError(
            f"Dataset is missing category directories: {', '.join(missing)}"
        )

    samples: list[DatasetSample] = []
    for category in CATEGORIES:
        category_root = dataset_root / category
        for path in sorted(category_root.rglob("*")):
            if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES:
                samples.append(DatasetSample(path=path, category=category))
    return samples


def score_distribution(scores: Iterable[float]) -> dict[str, float | int | None]:
    values = list(scores)
    if not values:
        return {
            "count": 0,
            "mean": None,
            "median": None,
            "minimum": None,
            "maximum": None,
            "standard_deviation": None,
        }
    return {
        "count": len(values),
        "mean": statistics.fmean(values),
        "median": statistics.median(values),
        "minimum": min(values),
        "maximum": max(values),
        "standard_deviation": statistics.pstdev(values),
    }


def confusion_matrix(
    scores: Iterable[float],
    labels: Iterable[bool],
    threshold: float,
) -> dict[str, int]:
    matrix = {"true_positive": 0, "true_negative": 0, "false_positive": 0, "false_negative": 0}
    for score, label in zip(scores, labels):
        predicted = score >= threshold
        if predicted and label:
            matrix["true_positive"] += 1
        elif not predicted and not label:
            matrix["true_negative"] += 1
        elif predicted:
            matrix["false_positive"] += 1
        else:
            matrix["false_negative"] += 1
    return matrix


def threshold_metrics(
    scores: Iterable[float],
    labels: Iterable[bool],
    threshold: float,
) -> dict[str, Any]:
    score_values = list(scores)
    label_values = list(labels)
    if len(score_values) != len(label_values) or not label_values:
        raise ValueError("Scores and labels must have the same non-zero length")

    matrix = confusion_matrix(score_values, label_values, threshold)
    tp = matrix["true_positive"]
    tn = matrix["true_negative"]
    fp = matrix["false_positive"]
    fn = matrix["false_negative"]
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "threshold": threshold,
        "accuracy": (tp + tn) / len(label_values),
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "false_positives": fp,
        "false_negatives": fn,
        "confusion_matrix": matrix,
    }


def threshold_sweep(
    scores: Iterable[float],
    labels: Iterable[bool],
    thresholds: Iterable[float],
) -> list[dict[str, Any]]:
    return [threshold_metrics(scores, labels, threshold) for threshold in thresholds]


def validate_binary_mapping(positive_category: str | None) -> str:
    if positive_category is None:
        raise ValueError("Binary class direction unverified")
    if positive_category not in CATEGORIES:
        raise ValueError(f"Unknown positive category: {positive_category}")
    return positive_category


def evaluate_dataset(
    dataset_root: Path,
    checkpoint_path: Path = DEFAULT_CHECKPOINT,
    positive_category: str | None = None,
    threshold: float | None = None,
    model_loader: Callable[[Path], torch.nn.Module] = load_model,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Evaluate all discovered files and retain failures in the prediction report."""
    if positive_category is not None:
        validate_binary_mapping(positive_category)
    samples = discover_samples(dataset_root)
    model = model_loader(checkpoint_path) if samples else None
    predictions: list[dict[str, Any]] = []
    evaluation_started = time.perf_counter()

    for sample in samples:
        relative_path = sample.path.relative_to(dataset_root).as_posix()
        result: dict[str, Any] = {
            "relative_image_path": relative_path,
            "ground_truth_category": sample.category,
            "raw_logit": None,
            "sigmoid_score": None,
            "predicted_class": None,
            "correct": None,
            "inference_duration_seconds": None,
            "device": None,
            "error": None,
        }
        try:
            with Image.open(sample.path) as image:
                image_rgb = image.convert("RGB")
            tensor = model.preprocess(image_rgb).unsqueeze(0).to(DEVICE)
            torch.cuda.synchronize(DEVICE)
            started = time.perf_counter()
            with torch.inference_mode():
                output = model(tensor)
            torch.cuda.synchronize(DEVICE)
            if output.shape != (1, 1) or not torch.isfinite(output).all():
                raise RuntimeError("UnivFD inference returned an invalid logit")
            score = float(torch.sigmoid(output[0, 0]).item())
            result.update(
                raw_logit=float(output[0, 0].item()),
                sigmoid_score=score,
                inference_duration_seconds=time.perf_counter() - started,
                device=torch.cuda.get_device_name(DEVICE),
            )
            if positive_category is not None and threshold is not None:
                predicted_positive = score >= threshold
                result["predicted_class"] = (
                    "positive" if predicted_positive else "negative"
                )
                result["correct"] = predicted_positive == (sample.category == positive_category)
        except (OSError, UnidentifiedImageError, RuntimeError, ValueError) as exc:
            result["error"] = str(exc)
        predictions.append(result)

    valid = [item for item in predictions if item["error"] is None]
    valid_scores = [item["sigmoid_score"] for item in valid]
    valid_labels = [
        item["ground_truth_category"] == positive_category for item in valid
    ]
    threshold_results = None
    if positive_category is not None and threshold is not None and valid:
        threshold_results = threshold_metrics(valid_scores, valid_labels, threshold)
    summary: dict[str, Any] = {
        "total_attempted": len(predictions),
        "successful_inferences": len(valid),
        "failed_samples": len(predictions) - len(valid),
        "invalid_files": sum(1 for item in predictions if item["error"] is not None),
        "total_evaluation_duration_seconds": time.perf_counter() - evaluation_started,
        "gpu_used": next((item["device"] for item in valid if item["device"]), None),
        "threshold": threshold,
        "threshold_metrics": threshold_results,
        "binary_class_direction": (
            positive_category if positive_category is not None else "Binary class direction unverified"
        ),
        "score_distributions": {
            category: score_distribution(
                item["sigmoid_score"]
                for item in valid
                if item["ground_truth_category"] == category
            )
            for category in CATEGORIES
        },
    }
    return predictions, summary


def write_artifacts(
    output_dir: Path,
    predictions: list[dict[str, Any]],
    summary: dict[str, Any],
    checkpoint_path: Path,
) -> None:
    if not predictions or summary["successful_inferences"] == 0:
        raise ValueError("No valid evaluation data; refusing to create evaluation artifacts")
    output_dir.mkdir(parents=True, exist_ok=True)
    with (output_dir / "predictions.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=predictions[0].keys())
        writer.writeheader()
        writer.writerows(predictions)
    report_summary = {
        **summary,
        "evaluation_date": date.today().isoformat(),
        "model_name": MODEL_NAME,
        "checkpoint": checkpoint_path.name,
        "limitations": [
            "UnivFD is a binary detector; the three folder labels are evaluation categories only.",
            "Binary class direction must be verified before classification metrics are calculated.",
        ],
    }
    (output_dir / "metrics.json").write_text(
        json.dumps(report_summary, indent=2), encoding="utf-8"
    )
    (output_dir / "evaluation_report.md").write_text(
        "# UnivFD evaluation\n\n"
        "Binary class direction: "
        f"{summary['binary_class_direction']}\n\n"
        "UnivFD output is not a calibrated probability and does not establish "
        "SATYA's three categories.\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", type=Path)
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--positive-category", choices=CATEGORIES)
    parser.add_argument("--threshold", type=float)
    parser.add_argument("--output", type=Path, default=Path("backend/evaluation/univfd"))
    args = parser.parse_args()
    try:
        predictions, summary = evaluate_dataset(
            args.dataset, args.checkpoint, args.positive_category, args.threshold
        )
        if predictions:
            write_artifacts(args.output, predictions, summary, args.checkpoint)
        print(json.dumps(summary, indent=2))
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
