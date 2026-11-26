from __future__ import annotations

import pytest

from jcheng_benchmark.stats import mean, percentile, success_summary, summarize


def test_mean_uses_all_values() -> None:
    assert mean([1.0, 2.0, 3.0]) == pytest.approx(2.0)


def test_percentile_is_nearest_rank() -> None:
    values = list(range(1, 11))
    assert percentile(values, 50) == 5
    assert percentile(values, 95) == 10
    assert percentile(values, 100) == 10
    assert percentile(values, 10) == 1


def test_percentile_rejects_out_of_range() -> None:
    with pytest.raises(ValueError):
        percentile([1.0], 0)
    with pytest.raises(ValueError):
        percentile([1.0], 101)
    with pytest.raises(ValueError):
        percentile([], 50)


def test_summarize_reports_the_declared_aggregates() -> None:
    stats = summarize([0.0, 1.0, 2.0])
    assert stats == {
        "count": 3,
        "mean": pytest.approx(1.0),
        "p50": 1.0,
        "p95": 2.0,
        "max": 2.0,
        "min": 0.0,
    }


def test_success_summary_counts_true_values() -> None:
    stats = success_summary([True, False, True, True])
    assert stats == {"count": 4, "rate": 0.75}
