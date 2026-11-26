from __future__ import annotations

import json
from pathlib import Path

import yaml

from jcheng_benchmark.cli import main

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_SUITE = ROOT / "tests" / "fixtures" / "synthetic" / "suite.yaml"
FIXTURE_DATA = ROOT / "tests" / "fixtures" / "synthetic" / "samples.jsonl"


def test_validate_accepts_the_fixture() -> None:
    assert main(["validate", "--spec", str(FIXTURE_SUITE)]) == 0


def test_validate_rejects_a_bad_suite(tmp_path: Path) -> None:
    bad = tmp_path / "bad.yaml"
    bad.write_text("schema_version: 1\nsuite: Bad Name\n", encoding="utf-8")
    assert main(["validate", "--spec", str(bad)]) == 2


def test_list_accepts_the_shipped_suites() -> None:
    assert main(["list", "--dir", str(ROOT / "benchmarks" / "suites")]) == 0


def test_run_writes_json_and_markdown(tmp_path: Path) -> None:
    json_path = tmp_path / "report.json"
    markdown_path = tmp_path / "report.md"
    code = main(
        [
            "run",
            "--spec",
            str(FIXTURE_SUITE),
            "--data",
            str(FIXTURE_DATA),
            "--operator",
            "unit-test",
            "--host",
            "ci",
            "--json",
            str(json_path),
            "--markdown",
            str(markdown_path),
        ]
    )
    assert code == 0
    report = json.loads(json_path.read_text(encoding="utf-8"))
    assert report["result"] == "pass"
    assert report["operator"] == "unit-test"
    assert report["host"] == "ci"
    assert report["suite"]["data_source"] == "synthetic"
    assert "synthetic" in markdown_path.read_text(encoding="utf-8")


def test_run_returns_one_on_a_failed_threshold(tmp_path: Path) -> None:
    suite = {
        "schema_version": 1,
        "suite": "cli-fail",
        "title": "CLI fail",
        "level": "L2",
        "data_source": "synthetic",
        "min_samples": 2,
        "metrics": [
            {"id": "position_error", "kind": "position_error", "unit": "mm"}
        ],
        "thresholds": [
            {
                "metric": "position_error",
                "aggregate": "p95",
                "op": "<",
                "value": 0.1,
            }
        ],
    }
    spec_path = tmp_path / "suite.yaml"
    spec_path.write_text(yaml.safe_dump(suite), encoding="utf-8")
    assert (
        main(
            [
                "run",
                "--spec",
                str(spec_path),
                "--data",
                str(FIXTURE_DATA),
                "--operator",
                "unit-test",
            ]
        )
        == 1
    )


def test_run_returns_two_on_missing_data(tmp_path: Path) -> None:
    assert (
        main(
            [
                "run",
                "--spec",
                str(FIXTURE_SUITE),
                "--data",
                str(tmp_path / "missing.jsonl"),
            ]
        )
        == 2
    )
