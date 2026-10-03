"""Validate SATYA's image manifest and locally acquired files."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from PIL import Image, UnidentifiedImageError


REQUIRED_COLUMNS = (
    "sample_id",
    "relative_path",
    "modality",
    "ground_truth_category",
    "original_dataset",
    "original_label",
    "source_id",
    "source_url",
    "manipulation_method",
    "generator_name",
    "parent_image_id",
    "split",
    "license",
    "license_url",
    "collection_date",
    "notes",
)
CATEGORIES = frozenset({"authentic", "manipulated", "synthetic"})
SUPPORTED_FORMATS = {
    "BMP": {".bmp"},
    "GIF": {".gif"},
    "JPEG": {".jpg", ".jpeg"},
    "PNG": {".png"},
    "TIFF": {".tif", ".tiff"},
    "WEBP": {".webp"},
}


def _issue(
    issues: list[dict[str, Any]],
    kind: str,
    message: str,
    row_number: int | None = None,
) -> None:
    issue: dict[str, Any] = {"kind": kind, "message": message}
    if row_number is not None:
        issue["row_number"] = row_number
    issues.append(issue)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_manifest(
    dataset_root: Path,
    manifest_path: Path | None = None,
) -> dict[str, Any]:
    """Return a non-destructive validation report for a dataset manifest."""
    dataset_root = dataset_root.resolve()
    manifest_path = (manifest_path or dataset_root / "manifests" / "metadata.csv").resolve()
    issues: list[dict[str, Any]] = []
    rows: list[dict[str, str]] = []
    hash_rows: defaultdict[str, list[int]] = defaultdict(list)
    sample_id_rows: defaultdict[str, list[int]] = defaultdict(list)
    parent_splits: defaultdict[str, set[str]] = defaultdict(set)
    category_counts: Counter[str] = Counter()
    source_counts: Counter[str] = Counter()
    valid_files = 0
    invalid_files = 0
    missing_provenance = 0
    missing_license = 0

    if not manifest_path.is_file():
        _issue(issues, "missing_manifest", f"Manifest does not exist: {manifest_path.name}")
    else:
        try:
            with manifest_path.open(newline="", encoding="utf-8") as handle:
                reader = csv.DictReader(handle)
                fieldnames = reader.fieldnames or []
                missing_columns = [column for column in REQUIRED_COLUMNS if column not in fieldnames]
                for column in missing_columns:
                    _issue(issues, "missing_required_column", f"Missing required column: {column}")
                if not missing_columns:
                    for row_number, row in enumerate(reader, start=2):
                        normalized = {key: (value or "").strip() for key, value in row.items()}
                        rows.append(normalized)
                        sample_id = normalized["sample_id"]
                        relative_path = normalized["relative_path"]
                        category = normalized["ground_truth_category"]
                        split = normalized["split"]
                        sample_id_rows[sample_id].append(row_number)
                        category_counts[category] += 1
                        source_counts[normalized["original_dataset"]] += 1

                        if not sample_id:
                            _issue(issues, "missing_sample_id", "sample_id is empty", row_number)
                        if category not in CATEGORIES:
                            _issue(
                                issues,
                                "invalid_category",
                                f"Unsupported ground_truth_category: {category}",
                                row_number,
                            )
                        if not normalized["original_dataset"] or not normalized["original_label"]:
                            missing_provenance += 1
                            _issue(
                                issues,
                                "missing_provenance",
                                "original_dataset and original_label are required",
                                row_number,
                            )
                        if not normalized["license"] or not normalized["license_url"]:
                            missing_license += 1
                            _issue(
                                issues,
                                "missing_license",
                                "license and license_url require verification",
                                row_number,
                            )
                        if normalized["parent_image_id"]:
                            parent_splits[normalized["parent_image_id"]].add(split)

                        candidate = (dataset_root / relative_path).resolve()
                        if not relative_path:
                            _issue(issues, "missing_path", "relative_path is empty", row_number)
                            invalid_files += 1
                            continue
                        if not candidate.is_relative_to(dataset_root):
                            _issue(issues, "path_traversal", "Path escapes dataset root", row_number)
                            invalid_files += 1
                            continue
                        if not candidate.is_file():
                            _issue(issues, "missing_file", f"Referenced file is missing: {relative_path}", row_number)
                            invalid_files += 1
                            continue

                        try:
                            with Image.open(candidate) as image:
                                image.verify()
                            with Image.open(candidate) as image:
                                detected_format = (image.format or "").upper()
                                width, height = image.size
                            if width <= 0 or height <= 0:
                                raise ValueError("Image dimensions must be positive")
                        except (OSError, UnidentifiedImageError, ValueError) as exc:
                            _issue(issues, "invalid_image", str(exc), row_number)
                            invalid_files += 1
                            continue

                        valid_extensions = SUPPORTED_FORMATS.get(detected_format, set())
                        if not valid_extensions:
                            _issue(
                                issues,
                                "unsupported_format",
                                f"Unsupported decoded format: {detected_format}",
                                row_number,
                            )
                        elif candidate.suffix.lower() not in valid_extensions:
                            _issue(
                                issues,
                                "extension_mismatch",
                                f"Extension does not match decoded format: {detected_format}",
                                row_number,
                            )
                        file_hash = _sha256(candidate)
                        hash_rows[file_hash].append(row_number)
                        valid_files += 1
        except (OSError, UnicodeError, csv.Error) as exc:
            _issue(issues, "manifest_read_error", str(exc))

    for sample_id, row_numbers in sample_id_rows.items():
        if sample_id and len(row_numbers) > 1:
            _issue(issues, "duplicate_sample_id", f"{sample_id}: rows {row_numbers}")
    for file_hash, row_numbers in hash_rows.items():
        if len(row_numbers) > 1:
            _issue(issues, "duplicate_sha256", f"{file_hash}: rows {row_numbers}")
            splits = {rows[row_number - 2]["split"] for row_number in row_numbers}
            if len(splits) > 1:
                _issue(issues, "duplicate_across_splits", f"{file_hash}: splits {sorted(splits)}")
    for parent_id, splits in parent_splits.items():
        if len(splits) > 1:
            _issue(issues, "parent_split_leakage", f"{parent_id}: splits {sorted(splits)}")

    status = "ready" if not issues and rows else "incomplete"
    return {
        "status": status,
        "dataset_root": dataset_root.name,
        "manifest": manifest_path.name,
        "total_manifest_rows": len(rows),
        "valid_files": valid_files,
        "invalid_files": invalid_files,
        "duplicate_hash_groups": sum(1 for values in hash_rows.values() if len(values) > 1),
        "missing_provenance_rows": missing_provenance,
        "missing_license_rows": missing_license,
        "counts_by_category": dict(sorted(category_counts.items())),
        "counts_by_source": dict(sorted(source_counts.items())),
        "issues": issues,
        "limitations": [
            "No near-duplicate detector is run; perceptual-hash review remains required.",
            "A ready status only validates local manifest/file integrity, not dataset license validity.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "dataset_root",
        type=Path,
        nargs="?",
        default=Path("backend/data/image"),
    )
    parser.add_argument("--manifest", type=Path)
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("backend/data/image/reports/dataset_validation_report.json"),
    )
    args = parser.parse_args()
    report = validate_manifest(args.dataset_root, args.manifest)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
