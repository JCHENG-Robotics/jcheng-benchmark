"""Read a dataset, compute declared metrics and evaluate thresholds.

The runner is deliberately strict: one malformed row aborts the run instead of
being dropped. Silent row loss changes the denominator and is not acceptable in
an evidence-producing tool.
"""

from __future__ import annotations

import hashlib
import json
import math
import operator
import socket
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import __version__
from .model import BenchmarkError, SuiteSpec, ThresholdSpec
from .stats import success_summary, summarize

_OPS = {
    "<=": operator.le,
    "<": operator.lt,
    ">=": operator.ge,
    ">": operator.gt,
}


@dataclass(frozen=True)
class Dataset:
    path: Path
    sha256: str
    samples: tuple[dict[str, Any], ...]


def read_dataset(path: str | Path) -> Dataset:
    """Read a JSONL dataset. Blank lines are ignored; malformed rows abort."""

    data_path = Path(path)
    try:
        raw = data_path.read_bytes()
    except OSError as exc:
        raise BenchmarkError(f"cannot read dataset {data_path}: {exc}") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise BenchmarkError(f"dataset {data_path} is not UTF-8: {exc}") from exc

    samples: list[dict[str, Any]] = []
    seen: set[str] = set()
    for line_number, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        try:
            record = json.loads(stripped)
        except json.JSONDecodeError as exc:
            raise BenchmarkError(
                f"{data_path}:{line_number}: invalid JSON: {exc.msg}"
            ) from exc
        if not isinstance(record, dict):
            raise BenchmarkError(
                f"{data_path}:{line_number}: each line must be a JSON object"
            )
        sample_id = record.get("sample_id")
        if not isinstance(sample_id, str) or not sample_id.strip():
            raise BenchmarkError(
                f"{data_path}:{line_number}: sample_id must be a non-empty string"
            )
        sample_id = sample_id.strip()
        if sample_id in seen:
            raise BenchmarkError(
                f"{data_path}:{line_number}: duplicate sample_id {sample_id!r}"
            )
        seen.add(sample_id)
        trial = record.get("trial")
        if trial is not None and (
            not isinstance(trial, str) or not trial.strip()
        ):
            raise BenchmarkError(
                f"{data_path}:{line_number}: trial must be a non-empty string"
            )
        record["sample_id"] = sample_id
        samples.append(record)

    return Dataset(
        path=data_path,
        sha256=hashlib.sha256(raw).hexdigest(),
        samples=tuple(samples),
    )


def _vector(
    sample: dict[str, Any], key: str, index: int, sample_id: str
) -> tuple[float, float, float]:
    value = sample.get(key)
    if not isinstance(value, (list, tuple)) or len(value) != 3:
        raise BenchmarkError(
            f"sample {index} ({sample_id}): {key} must be [x, y, z]"
        )
    components: list[float] = []
    for component in value:
        if type(component) not in (int, float) or not math.isfinite(component):
            raise BenchmarkError(
                f"sample {index} ({sample_id}): {key} components must be "
                "finite numbers"
            )
        components.append(float(component))
    return components[0], components[1], components[2]


def _number(
    sample: dict[str, Any], key: str | None, index: int, sample_id: str
) -> float:
    if key is None:
        raise BenchmarkError(
            f"sample {index} ({sample_id}): metric has no source field"
        )
    value = sample.get(key)
    if type(value) not in (int, float) or not math.isfinite(value):
        raise BenchmarkError(
            f"sample {index} ({sample_id}): {key} must be a finite number"
        )
    return float(value)


def _flag(
    sample: dict[str, Any], key: str | None, index: int, sample_id: str
) -> bool:
    if key is None:
        raise BenchmarkError(
            f"sample {index} ({sample_id}): metric has no source field"
        )
    value = sample.get(key)
    if type(value) is not bool:
        raise BenchmarkError(
            f"sample {index} ({sample_id}): {key} must be true or false"
        )
    return value


def _metric_values(
    spec: SuiteSpec, dataset: Dataset
) -> dict[str, dict[str, float | int]]:
    metrics: dict[str, dict[str, float | int]] = {}
    for metric in spec.metrics:
        values: list[float] | list[bool] = []
        for index, sample in enumerate(dataset.samples):
            sample_id = sample["sample_id"]
            if metric.kind == "position_error":
                measured = _vector(sample, "measured_m", index, sample_id)
                reference = _vector(sample, "reference_m", index, sample_id)
                values.append(math.dist(measured, reference) * 1000.0)
            elif metric.kind == "scalar":
                values.append(_number(sample, metric.source, index, sample_id))
            else:
                values.append(_flag(sample, metric.source, index, sample_id))
        if metric.kind == "success_rate":
            stats = success_summary(values)
        else:
            stats = summarize(values)
        entry: dict[str, float | int | str] = {
            "kind": metric.kind,
            "unit": metric.unit,
        }
        if metric.source is not None:
            entry["source"] = metric.source
        if metric.aggregate is not None:
            entry["declared_aggregate"] = metric.aggregate
        entry.update(stats)
        metrics[metric.id] = entry
    return metrics


def _evaluate_threshold(
    threshold: ThresholdSpec, metrics: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    actual = metrics[threshold.metric][threshold.aggregate]
    return {
        "metric": threshold.metric,
        "aggregate": threshold.aggregate,
        "op": threshold.op,
        "value": threshold.value,
        "actual": actual,
        "pass": bool(_OPS[threshold.op](actual, threshold.value)),
    }


def _limitations(spec: SuiteSpec, operator_name: str) -> list[str]:
    items = list(spec.limitations)
    if spec.data_source in ("synthetic", "mock"):
        items.append(
            f"Data source is {spec.data_source}; this result is not a hardware "
            "or recorded-data result and must not be reported as one."
        )
    elif spec.data_source == "recorded":
        items.append(
            "The dataset is an external recording identified by SHA-256; the "
            "report does not verify how it was captured."
        )
    else:
        items.append(
            "Hardware data requires the session authorization and environment "
            "record; this report alone is not a safety certification."
        )
    items.append(
        "A benchmark threshold is a project gate, not a safety certification."
    )
    if spec.thresholds:
        items.append(
            "Thresholds apply to the declared aggregates only and do not "
            "replace the source repository's acceptance criteria."
        )
    if operator_name == "unknown":
        items.append(
            "Operator is 'unknown'; this report is not suitable as evidence."
        )
    deduplicated: list[str] = []
    for item in items:
        if item not in deduplicated:
            deduplicated.append(item)
    return deduplicated


def run_suite(
    spec: SuiteSpec,
    data_path: str | Path,
    *,
    operator_name: str = "unknown",
    host: str | None = None,
    generated_at: str | None = None,
    notes: tuple[str, ...] | list[str] = (),
) -> dict[str, Any]:
    """Run one suite against one JSONL dataset and return a report mapping."""

    if not isinstance(operator_name, str) or not operator_name.strip():
        raise BenchmarkError("operator must be a non-empty string")
    operator_name = operator_name.strip()
    dataset = read_dataset(data_path)

    metrics: dict[str, dict[str, Any]] = {}
    if dataset.samples:
        metrics = _metric_values(spec, dataset)

    threshold_results: list[dict[str, Any]] = []
    for threshold in spec.thresholds:
        if not dataset.samples:
            threshold_results.append(
                {
                    "metric": threshold.metric,
                    "aggregate": threshold.aggregate,
                    "op": threshold.op,
                    "value": threshold.value,
                    "actual": None,
                    "pass": False,
                }
            )
        else:
            threshold_results.append(_evaluate_threshold(threshold, metrics))

    reasons: list[str] = []
    if not dataset.samples:
        reasons.append("dataset is empty")
    elif len(dataset.samples) < spec.min_samples:
        reasons.append(
            f"{len(dataset.samples)} samples is below min_samples "
            f"{spec.min_samples}"
        )
    if not spec.thresholds:
        reasons.append(
            "suite declares no thresholds; the result is informational"
        )
    failed = [item for item in threshold_results if not item["pass"]]
    if failed:
        reasons.append(f"{len(failed)} threshold(s) failed")

    if not dataset.samples or len(dataset.samples) < spec.min_samples:
        result = "inconclusive"
    elif not spec.thresholds:
        result = "inconclusive"
    elif failed:
        result = "fail"
    else:
        result = "pass"

    if result == "pass":
        reason = (
            f"all {len(spec.thresholds)} threshold(s) passed with "
            f"{len(dataset.samples)} samples"
        )
    else:
        reason = "; ".join(reasons) if reasons else "no result was produced"

    trials = [
        sample["trial"].strip()
        for sample in dataset.samples
        if isinstance(sample.get("trial"), str)
    ]

    report: dict[str, Any] = {
        "schema_version": 1,
        "report_kind": "benchmark-report",
        "tool": {"name": "jcheng-benchmark", "version": __version__},
        "generated_at": generated_at
        or datetime.now(timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z"),
        "operator": operator_name,
        "host": host or socket.gethostname(),
        "suite": {
            "id": spec.suite,
            "title": spec.title,
            "level": spec.level,
            "data_source": spec.data_source,
            "description": spec.description,
            "min_samples": spec.min_samples,
            "path": str(spec.path),
            "sha256": spec.sha256,
        },
        "dataset": {
            "path": str(dataset.path),
            "sha256": dataset.sha256,
            "samples": len(dataset.samples),
            "trials": len(set(trials)) if trials else None,
        },
        "metrics": metrics,
        "thresholds": threshold_results,
        "result": result,
        "result_reason": reason,
        "limitations": _limitations(spec, operator_name),
        "notes": list(notes),
    }
    return report
