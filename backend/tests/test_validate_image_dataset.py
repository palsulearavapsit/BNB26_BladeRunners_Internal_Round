import csv
from pathlib import Path

from PIL import Image

from scripts.validate_image_dataset import REQUIRED_COLUMNS, validate_manifest


def _write_manifest(root: Path, rows: list[dict[str, str]], columns=REQUIRED_COLUMNS):
    manifest = root / "manifests" / "metadata.csv"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    with manifest.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows({column: row.get(column, "") for column in columns} for row in rows)
    return manifest


def _row(relative_path="authentic/sample.png", **overrides):
    row = {column: "" for column in REQUIRED_COLUMNS}
    row.update(
        {
            "sample_id": "sample-1",
            "relative_path": relative_path,
            "modality": "image",
            "ground_truth_category": "authentic",
            "original_dataset": "fixture",
            "original_label": "real",
            "source_id": "fixture-1",
            "source_url": "https://example.invalid/fixture",
            "license": "test-only",
            "license_url": "https://example.invalid/license",
            "split": "test",
        }
    )
    row.update(overrides)
    return row


def _image(root: Path, relative_path="authentic/sample.png", color="red"):
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (8, 8), color=color).save(path)
    return path


def test_valid_manifest(tmp_path):
    _image(tmp_path)
    _write_manifest(tmp_path, [_row()])

    report = validate_manifest(tmp_path)

    assert report["status"] == "ready"
    assert report["valid_files"] == 1
    assert report["issues"] == []


def test_missing_file_is_reported(tmp_path):
    _write_manifest(tmp_path, [_row()])

    report = validate_manifest(tmp_path)

    assert report["status"] == "incomplete"
    assert any(issue["kind"] == "missing_file" for issue in report["issues"])


def test_invalid_image_is_reported(tmp_path):
    path = tmp_path / "authentic" / "bad.png"
    path.parent.mkdir(parents=True)
    path.write_bytes(b"not an image")
    _write_manifest(tmp_path, [_row("authentic/bad.png")])

    report = validate_manifest(tmp_path)

    assert any(issue["kind"] == "invalid_image" for issue in report["issues"])


def test_duplicate_hash_is_reported(tmp_path):
    _image(tmp_path, "authentic/one.png")
    _image(tmp_path, "authentic/two.png")
    first = (tmp_path / "authentic/one.png").read_bytes()
    (tmp_path / "authentic/two.png").write_bytes(first)
    _write_manifest(tmp_path, [_row("authentic/one.png"), _row("authentic/two.png", sample_id="sample-2")])

    report = validate_manifest(tmp_path)

    assert any(issue["kind"] == "duplicate_sha256" for issue in report["issues"])


def test_invalid_category_is_reported(tmp_path):
    _image(tmp_path)
    _write_manifest(tmp_path, [_row(ground_truth_category="fake")])

    report = validate_manifest(tmp_path)

    assert any(issue["kind"] == "invalid_category" for issue in report["issues"])


def test_missing_required_column_is_reported(tmp_path):
    _write_manifest(tmp_path, [_row()], columns=REQUIRED_COLUMNS[:-1])

    report = validate_manifest(tmp_path)

    assert any(issue["kind"] == "missing_required_column" for issue in report["issues"])


def test_path_traversal_is_reported(tmp_path):
    _write_manifest(tmp_path, [_row("../outside.png")])

    report = validate_manifest(tmp_path)

    assert any(issue["kind"] == "path_traversal" for issue in report["issues"])


def test_duplicate_sample_id_is_reported(tmp_path):
    _image(tmp_path, "authentic/one.png")
    _image(tmp_path, "authentic/two.png", color="blue")
    _write_manifest(tmp_path, [_row("authentic/one.png"), _row("authentic/two.png")])

    report = validate_manifest(tmp_path)

    assert any(issue["kind"] == "duplicate_sample_id" for issue in report["issues"])
