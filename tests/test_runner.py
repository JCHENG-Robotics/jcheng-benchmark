from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest
import yaml

from jcheng_benchmark.model import BenchmarkError, load_suite
from jcheng_benchmark.runner import read_dataset, run_suite

BASE_SUITE: dict[str, Any] = {
    "schema_version": 1,
    "suite": "unit-suite",
    "title": "Unit suite",
    "level": "L2",
    "data_source": "synthetic",
    "description": "Unit test data.",
    "min_samples": 2,
    "metrics": [
        {"id": "position_error", "kind": "position_error", "unit": "mm"}
    ],
    "thresholds": [
        {
            "metric": "position_error",
            "aggregate": "p95",
            "op": "<=",
            "value": 5.0,
        }
    ],
    "limitations": ["Unit test only."],
}


def make_suite(tmp_path: Path, **overrides: Any):
    document = {**BASE_SUITE, **overrides}
    path = tmp_path / "suite.yaml"
    path.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")
    return load_suite(path)


def write_samples(tmp_path: Path, rows: list[dict[str, Any]]) -> Path:
    path = tmp_path / "samples.jsonl"
    path.write_text(
        "\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8"
    )
    return path


def position_rows() -> list[dict[str, Any]]:
    return [
        {
            "sample_id": "s1",
            "trial": "pose-1",
            "measured_m": [0.0, 0.0, 0.0],
            "reference_m": [0.0, 0.0, 0.0],
        },
        {
            "sample_id": "s2",
            "trial": "pose-1",
            "measured_m": [0.001, 0.0, 0.0],
            "reference_m": [0.0, 0.0, 0.0],
        },
        {
            "sample_id": "s3",
            "trial": "pose-2",
            "measured_m": [0.002, 0.0, 0.0],
            "reference_m": [0.0, 0.0, 0.0],
        },
    ]


def test_run_pass(tmp_path: Path) -> None:
    spec = make_suite(tmp_path)
    report = run_suite(spec, write_samples(tmp_path, position_rows()))
    assert report["result"] == "pass"
    assert report["metrics"]["position_error"]["p95"] == pytest.approx(2.0)
    assert report["metrics"]["position_error"]["count"] == 3
    assert report["dataset"]["samples"] == 3
    assert report["dataset"]["trials"] == 2
    assert report["thresholds"][0]["pass"] is True


def test_run_fail_when_threshold_is_exceeded(tmp_path: Path) -> None:
    spec = make_suite(
        tmp_path,
        thresholds=[
            {
                "metric": "position_error",
                "aggregate": "p95",
                "op": "<",
                "value": 1.5,
            }
        ],
    )
    report = run_suite(spec, write_samples(tmp_path, position_rows()))
    assert report["result"] == "fail"
    assert report["thresholds"][0]["pass"] is False
    assert "threshold" in report["result_reason"]


def test_run_is_inconclusive_below_min_samples(tmp_path: Path) -> None:
    spec = make_suite(tmp_path, min_samples=4)
    report = run_suite(spec, write_samples(tmp_path, position_rows()))
    assert report["result"] == "inconclusive"
    assert "below min_samples" in report["result_reason"]


def test_run_without_thresholds_is_informational(tmp_path: Path) -> None:
    spec = make_suite(tmp_path, thresholds=[])
    report = run_suite(spec, write_samples(tmp_path, position_rows()))
    assert report["result"] == "inconclusive"
    assert "no thresholds" in report["result_reason"]
    assert report["metrics"]["position_error"]["count"] == 3


def test_empty_dataset_is_inconclusive(tmp_path: Path) -> None:
    spec = make_suite(tmp_path)
    data = tmp_path / "empty.jsonl"
    data.write_text("", encoding="utf-8")
    report = run_suite(spec, data)
    assert report["result"] == "inconclusive"
    assert report["metrics"] == {}
    assert report["thresholds"][0]["actual"] is None


def test_malformed_json_aborts_with_line_number(tmp_path: Path) -> None:
    path = tmp_path / "bad.jsonl"
    path.write_text('{"sample_id": "ok"}\n{bad\n', encoding="utf-8")
    with pytest.raises(BenchmarkError, match=":2: invalid JSON"):
        read_dataset(path)


def test_duplicate_sample_id_aborts(tmp_path: Path) -> None:
    path = tmp_path / "dup.jsonl"
    path.write_text(
        '{"sample_id": "x"}\n{"sample_id": "x"}\n', encoding="utf-8"
    )
    with pytest.raises(BenchmarkError, match="duplicate sample_id"):
        read_dataset(path)


def test_missing_position_field_aborts(tmp_path: Path) -> None:
    spec = make_suite(tmp_path)
    rows = position_rows()
    del rows[1]["measured_m"]
    with pytest.raises(BenchmarkError, match="measured_m"):
        run_suite(spec, write_samples(tmp_path, rows))


def test_boolean_is_not_a_number(tmp_path: Path) -> None:
    spec = make_suite(
        tmp_path,
        metrics=[
            {
                "id": "latency",
                "kind": "scalar",
                "source": "latency_ms",
                "aggregate": "p95",
                "unit": "ms",
            }
        ],
        thresholds=[],
    )
    rows = [
        {"sample_id": "a", "latency_ms": True},
        {"sample_id": "b", "latency_ms": 10.0},
    ]
    with pytest.raises(BenchmarkError, match="finite number"):
        run_suite(spec, write_samples(tmp_path, rows))


def test_trial_must_be_a_non_empty_string(tmp_path: Path) -> None:
    path = tmp_path / "trial.jsonl"
    path.write_text('{"sample_id": "a", "trial": 3}\n', encoding="utf-8")
    with pytest.raises(BenchmarkError, match="trial"):
        read_dataset(path)


def test_scalar_metric_computes_percentiles(tmp_path: Path) -> None:
    spec = make_suite(
        tmp_path,
        metrics=[
            {
                "id": "latency",
                "kind": "scalar",
                "source": "latency_ms",
                "aggregate": "p95",
                "unit": "ms",
            }
        ],
        thresholds=[],
    )
    rows = [
        {"sample_id": "a", "latency_ms": 10.0},
        {"sample_id": "b", "latency_ms": 20.0},
        {"sample_id": "c", "latency_ms": 30.0},
        {"sample_id": "d", "latency_ms": 40.0},
    ]
    report = run_suite(spec, write_samples(tmp_path, rows))
    assert report["metrics"]["latency"]["p95"] == pytest.approx(40.0)
    assert report["metrics"]["latency"]["declared_aggregate"] == "p95"


def test_success_rate_metric(tmp_path: Path) -> None:
    spec = make_suite(
        tmp_path,
        metrics=[
            {
                "id": "success",
                "kind": "success_rate",
                "source": "success",
                "unit": "ratio",
            }
        ],
        thresholds=[
            {
                "metric": "success",
                "aggregate": "rate",
                "op": ">=",
                "value": 0.75,
            }
        ],
        min_samples=4,
    )
    rows = [
        {"sample_id": "a", "success": True},
        {"sample_id": "b", "success": True},
        {"sample_id": "c", "success": False},
        {"sample_id": "d", "success": True},
    ]
    report = run_suite(spec, write_samples(tmp_path, rows))
    assert report["result"] == "pass"
    assert report["metrics"]["success"]["rate"] == pytest.approx(0.75)


@pytest.mark.parametrize(
    ("level", "data_source"),
    [
        ("L4", "synthetic"),
        ("L4", "mock"),
        ("L5", "recorded"),
        ("L3", "hardware"),
    ],
)
def test_level_and_data_source_must_match(
    tmp_path: Path, level: str, data_source: str
) -> None:
    with pytest.raises(BenchmarkError):
        make_suite(tmp_path, level=level, data_source=data_source)


def test_l4_with_recorded_data_is_accepted(tmp_path: Path) -> None:
    spec = make_suite(tmp_path, level="L4", data_source="recorded")
    assert spec.level == "L4"


def test_duplicate_metric_id_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(BenchmarkError, match="duplicate id"):
        make_suite(
            tmp_path,
            metrics=[
                {"id": "x", "kind": "position_error", "unit": "mm"},
                {"id": "x", "kind": "position_error", "unit": "mm"},
            ],
        )


def test_threshold_metric_must_exist(tmp_path: Path) -> None:
    with pytest.raises(BenchmarkError, match="not declared"):
        make_suite(
            tmp_path,
            thresholds=[
                {
                    "metric": "missing",
                    "aggregate": "p95",
                    "op": "<=",
                    "value": 1.0,
                }
            ],
        )


def test_success_threshold_cannot_use_mean(tmp_path: Path) -> None:
    with pytest.raises(BenchmarkError, match="not produced"):
        make_suite(
            tmp_path,
            metrics=[
                {"id": "success", "kind": "success_rate", "unit": "ratio"}
            ],
            thresholds=[
                {
                    "metric": "success",
                    "aggregate": "mean",
                    "op": ">=",
                    "value": 0.5,
                }
            ],
        )


def test_position_unit_is_fixed_to_mm(tmp_path: Path) -> None:
    with pytest.raises(BenchmarkError, match="unit is fixed to mm"):
        make_suite(
            tmp_path,
            metrics=[
                {"id": "position_error", "kind": "position_error", "unit": "cm"}
            ],
        )


def test_dataset_hash_is_recorded(tmp_path: Path) -> None:
    path = write_samples(tmp_path, position_rows())
    dataset = read_dataset(path)
    expected = hashlib.sha256(path.read_bytes()).hexdigest()
    assert dataset.sha256 == expected
    assert len(dataset.sha256) == 64


def test_synthetic_report_says_it_is_not_a_hardware_result(
    tmp_path: Path,
) -> None:
    spec = make_suite(tmp_path)
    report = run_suite(spec, write_samples(tmp_path, position_rows()))
    assert any(
        "not a hardware" in item for item in report["limitations"]
    )


def test_unknown_operator_is_flagged(tmp_path: Path) -> None:
    spec = make_suite(tmp_path)
    report = run_suite(spec, write_samples(tmp_path, position_rows()))
    assert any("not suitable as evidence" in item for item in report["limitations"])
