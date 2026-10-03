from pathlib import Path

import pytest

from scripts.evaluate_univfd import (
    confusion_matrix,
    discover_samples,
    evaluate_dataset,
    score_distribution,
    threshold_sweep,
    threshold_metrics,
    validate_binary_mapping,
)


def test_dataset_label_parsing(tmp_path):
    for category in ("authentic", "manipulated", "synthetic"):
        (tmp_path / category).mkdir()
    (tmp_path / "authentic" / "one.png").write_bytes(b"not decoded here")

    samples = discover_samples(tmp_path)

    assert samples[0].category == "authentic"
    assert samples[0].path == Path(tmp_path / "authentic" / "one.png")


def test_missing_directories_are_reported(tmp_path):
    with pytest.raises(FileNotFoundError, match="Dataset directory"):
        discover_samples(tmp_path / "missing")

    (tmp_path / "authentic").mkdir()
    with pytest.raises(FileNotFoundError, match="missing category directories"):
        discover_samples(tmp_path)


def test_invalid_image_is_recorded(tmp_path):
    for category in ("authentic", "manipulated", "synthetic"):
        (tmp_path / category).mkdir()
    image_path = tmp_path / "authentic" / "bad.png"
    image_path.write_bytes(b"invalid")

    predictions, summary = evaluate_dataset(tmp_path, model_loader=lambda _: None)

    assert predictions[0]["error"]
    assert predictions[0]["relative_image_path"] == "authentic/bad.png"
    assert summary["failed_samples"] == 1


def test_empty_dataset_has_no_successful_samples(tmp_path):
    for category in ("authentic", "manipulated", "synthetic"):
        (tmp_path / category).mkdir()

    predictions, summary = evaluate_dataset(tmp_path, model_loader=lambda _: None)

    assert predictions == []
    assert summary["successful_inferences"] == 0


def test_score_aggregation():
    result = score_distribution([0.1, 0.3, 0.5])

    assert result["count"] == 3
    assert result["mean"] == pytest.approx(0.3)
    assert result["median"] == pytest.approx(0.3)
    assert result["minimum"] == pytest.approx(0.1)
    assert result["maximum"] == pytest.approx(0.5)


def test_threshold_and_confusion_matrix():
    scores = [0.9, 0.8, 0.2, 0.1]
    labels = [True, False, True, False]

    assert confusion_matrix(scores, labels, 0.5) == {
        "true_positive": 1,
        "true_negative": 1,
        "false_positive": 1,
        "false_negative": 1,
    }
    assert threshold_metrics(scores, labels, 0.5)["accuracy"] == pytest.approx(0.5)
    assert len(threshold_sweep(scores, labels, [0.25, 0.5, 0.75])) == 3


def test_binary_mapping_requires_explicit_direction():
    with pytest.raises(ValueError, match="Binary class direction unverified"):
        validate_binary_mapping(None)
    assert validate_binary_mapping("authentic") == "authentic"


def test_no_three_class_prediction_is_created():
    assert set(("positive", "negative")).isdisjoint(
        {"authentic", "manipulated", "synthetic"}
    )
