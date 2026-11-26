"""Suite contract for the benchmark harness.

A suite is a small, pre-registered YAML declaration: dataset level, metrics and
thresholds. Nothing in this module touches ROS, a device or the network.
"""

from __future__ import annotations

import hashlib
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

LEVELS = ("L0", "L1", "L2", "L3", "L4", "L5")
DATA_SOURCES = ("hardware", "recorded", "synthetic", "mock")
METRIC_KINDS = ("position_error", "scalar", "success_rate")
AGGREGATES = ("mean", "p50", "p95", "max", "min")
COMPARATORS = ("<=", "<", ">=", ">")

_SLUG = re.compile(r"^[a-z][a-z0-9_-]*$")


class BenchmarkError(ValueError):
    """A suite or dataset violates the benchmark contract."""


@dataclass(frozen=True)
class MetricSpec:
    id: str
    kind: str
    unit: str
    source: str | None = None
    aggregate: str | None = None

    @property
    def produced_aggregates(self) -> tuple[str, ...]:
        return ("rate",) if self.kind == "success_rate" else AGGREGATES


@dataclass(frozen=True)
class ThresholdSpec:
    metric: str
    aggregate: str
    op: str
    value: float


@dataclass(frozen=True)
class SuiteSpec:
    schema_version: int
    suite: str
    title: str
    level: str
    data_source: str
    description: str
    min_samples: int
    metrics: tuple[MetricSpec, ...]
    thresholds: tuple[ThresholdSpec, ...]
    limitations: tuple[str, ...]
    path: Path
    sha256: str


def _mapping(value: Any, where: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise BenchmarkError(f"{where} must be a mapping")
    return value


def _text(
    mapping: dict[str, Any],
    key: str,
    where: str,
    *,
    required: bool = True,
    default: str | None = None,
) -> str | None:
    value = mapping.get(key, default)
    if not required and (value is None or (isinstance(value, str) and not value.strip())):
        return None
    if not isinstance(value, str) or not value.strip():
        raise BenchmarkError(f"{where}.{key} must be a non-empty string")
    return value.strip()


def _list(mapping: dict[str, Any], key: str, where: str) -> list[Any]:
    value = mapping.get(key)
    if not isinstance(value, list):
        raise BenchmarkError(f"{where}.{key} must be a list")
    return value


def _integer(mapping: dict[str, Any], key: str, where: str, minimum: int) -> int:
    value = mapping.get(key)
    if type(value) is not int or value < minimum:
        raise BenchmarkError(f"{where}.{key} must be an integer >= {minimum}")
    return value


def _number(value: Any, where: str) -> float:
    if type(value) not in (int, float) or not math.isfinite(value):
        raise BenchmarkError(f"{where} must be a finite number")
    return float(value)


def _metric(raw: Any, index: int, where: str) -> MetricSpec:
    item = _mapping(raw, f"{where}.metrics[{index}]")
    metric_id = _text(item, "id", f"{where}.metrics[{index}]")
    assert metric_id is not None
    if not _SLUG.match(metric_id):
        raise BenchmarkError(
            f"{where}.metrics[{index}].id must match {_SLUG.pattern}"
        )
    kind = _text(item, "kind", f"{where}.metrics[{index}]")
    assert kind is not None
    if kind not in METRIC_KINDS:
        raise BenchmarkError(
            f"{where}.metrics[{index}].kind must be one of {METRIC_KINDS}"
        )
    unit = _text(
        item, "unit", f"{where}.metrics[{index}]", required=False, default=None
    )
    source = _text(
        item, "source", f"{where}.metrics[{index}]", required=False, default=None
    )
    aggregate = _text(
        item, "aggregate", f"{where}.metrics[{index}]", required=False, default=None
    )

    if kind == "position_error":
        if unit is not None and unit != "mm":
            raise BenchmarkError(
                f"{where}.metrics[{index}] is position_error; unit is fixed to mm"
            )
        if source is not None or aggregate is not None:
            raise BenchmarkError(
                f"{where}.metrics[{index}] is position_error; it derives "
                "measured_m/reference_m and takes no source or aggregate"
            )
        return MetricSpec(id=metric_id, kind=kind, unit="mm")

    if kind == "scalar":
        if unit is None:
            raise BenchmarkError(f"{where}.metrics[{index}].unit is required")
        if source is None:
            raise BenchmarkError(f"{where}.metrics[{index}].source is required")
        if aggregate is None:
            raise BenchmarkError(f"{where}.metrics[{index}].aggregate is required")
        if aggregate not in AGGREGATES:
            raise BenchmarkError(
                f"{where}.metrics[{index}].aggregate must be one of {AGGREGATES}"
            )
        return MetricSpec(
            id=metric_id,
            kind=kind,
            unit=unit,
            source=source,
            aggregate=aggregate,
        )

    # success_rate
    if unit is not None and unit != "ratio":
        raise BenchmarkError(
            f"{where}.metrics[{index}] is success_rate; unit is fixed to ratio"
        )
    if aggregate is not None and aggregate != "rate":
        raise BenchmarkError(
            f"{where}.metrics[{index}] is success_rate; aggregate is fixed to rate"
        )
    return MetricSpec(
        id=metric_id,
        kind=kind,
        unit="ratio",
        source=source or "success",
        aggregate="rate",
    )


def _threshold(
    raw: Any, index: int, where: str, metrics: dict[str, MetricSpec]
) -> ThresholdSpec:
    item = _mapping(raw, f"{where}.thresholds[{index}]")
    metric_id = _text(item, "metric", f"{where}.thresholds[{index}]")
    aggregate = _text(item, "aggregate", f"{where}.thresholds[{index}]")
    op = _text(item, "op", f"{where}.thresholds[{index}]")
    assert metric_id is not None and aggregate is not None and op is not None
    if metric_id not in metrics:
        raise BenchmarkError(
            f"{where}.thresholds[{index}].metric {metric_id!r} is not declared"
        )
    if aggregate not in metrics[metric_id].produced_aggregates:
        raise BenchmarkError(
            f"{where}.thresholds[{index}].aggregate {aggregate!r} is not "
            f"produced by {metric_id!r}"
        )
    if op not in COMPARATORS:
        raise BenchmarkError(
            f"{where}.thresholds[{index}].op must be one of {COMPARATORS}"
        )
    if "value" not in item:
        raise BenchmarkError(f"{where}.thresholds[{index}].value is required")
    return ThresholdSpec(
        metric=metric_id,
        aggregate=aggregate,
        op=op,
        value=_number(item["value"], f"{where}.thresholds[{index}].value"),
    )


def load_suite(path: str | Path) -> SuiteSpec:
    """Load and validate one suite file."""

    suite_path = Path(path)
    try:
        raw = suite_path.read_bytes()
    except OSError as exc:
        raise BenchmarkError(f"cannot read suite {suite_path}: {exc}") from exc
    try:
        document = yaml.safe_load(raw.decode("utf-8"))
    except (UnicodeDecodeError, yaml.YAMLError) as exc:
        raise BenchmarkError(f"cannot parse suite {suite_path}: {exc}") from exc
    where = str(suite_path)
    root = _mapping(document, where)

    schema_version = _integer(root, "schema_version", where, 1)
    if schema_version != 1:
        raise BenchmarkError(f"{where}.schema_version must be 1")

    suite_id = _text(root, "suite", where)
    assert suite_id is not None
    if not _SLUG.match(suite_id):
        raise BenchmarkError(f"{where}.suite must match {_SLUG.pattern}")

    title = _text(root, "title", where)
    level = _text(root, "level", where)
    data_source = _text(root, "data_source", where)
    assert title is not None and level is not None and data_source is not None
    if level not in LEVELS:
        raise BenchmarkError(f"{where}.level must be one of {LEVELS}")
    if data_source not in DATA_SOURCES:
        raise BenchmarkError(
            f"{where}.data_source must be one of {DATA_SOURCES}"
        )
    if level == "L4" and data_source not in ("recorded", "hardware"):
        raise BenchmarkError(
            f"{where}: L4 is replay and requires a recorded dataset "
            "(data_source: recorded); synthetic and mock runs are L2/L3"
        )
    if level == "L5" and data_source != "hardware":
        raise BenchmarkError(
            f"{where}: L5 is hardware and requires data_source: hardware"
        )
    if data_source == "hardware" and level != "L5":
        raise BenchmarkError(
            f"{where}: data_source hardware requires level L5"
        )

    description = _text(
        root, "description", where, required=False, default=""
    ) or ""

    min_samples = _integer(root, "min_samples", where, 1)

    raw_metrics = _list(root, "metrics", where)
    if not raw_metrics:
        raise BenchmarkError(f"{where}.metrics must not be empty")
    metrics: list[MetricSpec] = []
    seen: set[str] = set()
    for index, raw_metric in enumerate(raw_metrics):
        metric = _metric(raw_metric, index, where)
        if metric.id in seen:
            raise BenchmarkError(f"{where}.metrics has duplicate id {metric.id!r}")
        seen.add(metric.id)
        metrics.append(metric)
    metric_index = {metric.id: metric for metric in metrics}

    raw_thresholds = root.get("thresholds")
    if raw_thresholds is None:
        raw_thresholds = []
    if not isinstance(raw_thresholds, list):
        raise BenchmarkError(f"{where}.thresholds must be a list")
    thresholds = tuple(
        _threshold(raw_threshold, index, where, metric_index)
        for index, raw_threshold in enumerate(raw_thresholds)
    )

    raw_limitations = root.get("limitations")
    if raw_limitations is None:
        raw_limitations = []
    if not isinstance(raw_limitations, list) or not all(
        isinstance(item, str) and item.strip() for item in raw_limitations
    ):
        raise BenchmarkError(f"{where}.limitations must be a list of strings")

    return SuiteSpec(
        schema_version=schema_version,
        suite=suite_id,
        title=title,
        level=level,
        data_source=data_source,
        description=description,
        min_samples=min_samples,
        metrics=tuple(metrics),
        thresholds=thresholds,
        limitations=tuple(item.strip() for item in raw_limitations),
        path=suite_path,
        sha256=hashlib.sha256(raw).hexdigest(),
    )
