"""Small deterministic statistics used by the benchmark runner.

Percentiles use the nearest-rank definition, stated explicitly so reports are
comparable across runs and languages.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Sequence


def mean(values: Sequence[float]) -> float:
    if not values:
        raise ValueError("mean of an empty sequence")
    return math.fsum(values) / len(values)


def percentile(values: Sequence[float], p: float) -> float:
    """Nearest-rank percentile: the floor(ceil(p/100 * n))-th smallest value."""

    if not values:
        raise ValueError("percentile of an empty sequence")
    if not 0 < p <= 100:
        raise ValueError("percentile must be in (0, 100]")
    ordered = sorted(values)
    rank = math.ceil((p / 100.0) * len(ordered))
    index = min(max(rank - 1, 0), len(ordered) - 1)
    return ordered[index]


def summarize(values: Iterable[float]) -> dict[str, float | int]:
    data = [float(value) for value in values]
    if not data:
        raise ValueError("summarize of an empty sequence")
    return {
        "count": len(data),
        "mean": mean(data),
        "p50": percentile(data, 50),
        "p95": percentile(data, 95),
        "max": max(data),
        "min": min(data),
    }


def success_summary(flags: Iterable[bool]) -> dict[str, float | int]:
    data = [bool(flag) for flag in flags]
    if not data:
        raise ValueError("success_summary of an empty sequence")
    return {
        "count": len(data),
        "rate": sum(1 for flag in data if flag) / len(data),
    }
