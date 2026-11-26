"""Render benchmark reports as JSON and Markdown."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _format(value: Any) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        return f"{value:.6g}"
    return str(value)


def render_markdown(report: dict[str, Any]) -> str:
    suite = report["suite"]
    dataset = report["dataset"]
    lines = [
        f"# Benchmark report — {suite['title']}",
        "",
        f"> Result: **{report['result']}** — {report['result_reason']}.",
        f"> Suite: `{suite['id']}` at level {suite['level']}, "
        f"data source `{suite['data_source']}`.",
        f"> Operator: {report['operator']} · Host: {report['host']} · "
        f"Generated: {report['generated_at']}.",
        f"> Dataset: `{dataset['path']}` — {dataset['samples']} samples, "
        f"{dataset['trials'] if dataset['trials'] is not None else 0} trials, "
        f"sha256 `{dataset['sha256']}`.",
        f"> Suite spec: `{suite['path']}`, sha256 `{suite['sha256']}`.",
        "",
        "## Metrics",
        "",
        "| Metric | Aggregate | Value | Unit |",
        "|---|---|---:|---|",
    ]
    for metric_id, metric in report["metrics"].items():
        aggregates = ["rate"] if metric["kind"] == "success_rate" else [
            "count",
            "mean",
            "p50",
            "p95",
            "max",
            "min",
        ]
        for aggregate in aggregates:
            if aggregate in metric:
                lines.append(
                    f"| `{metric_id}` | {aggregate} | "
                    f"{_format(metric[aggregate])} | {metric['unit']} |"
                )
    if not report["metrics"]:
        lines.append("| — | — | — | — |")

    lines.extend(
        [
            "",
            "## Thresholds",
            "",
            "| Metric | Aggregate | Rule | Actual | Result |",
            "|---|---|---|---:|---|",
        ]
    )
    for threshold in report["thresholds"]:
        lines.append(
            f"| `{threshold['metric']}` | {threshold['aggregate']} | "
            f"{threshold['op']} {_format(threshold['value'])} | "
            f"{_format(threshold['actual'])} | "
            f"{'pass' if threshold['pass'] else 'fail'} |"
        )
    if not report["thresholds"]:
        lines.append("| — | — | — | — | — |")

    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- {item}" for item in report["limitations"])

    if report.get("notes"):
        lines.extend(["", "## Notes", ""])
        lines.extend(f"- {item}" for item in report["notes"])

    lines.extend(
        [
            "",
            "---",
            "",
            "This is a benchmark report, not an acceptance report. It does not "
            "replace the source repository's `ACCEPTANCE.md`.",
            "",
        ]
    )
    return "\n".join(lines)


def write_json(path: str | Path, report: dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def write_markdown(path: str | Path, report: dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(render_markdown(report), encoding="utf-8")
