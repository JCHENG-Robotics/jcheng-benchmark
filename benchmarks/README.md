# Benchmark suites

> Status: **v0.1.0** as of 2026-11-26. Three template declarations ship; none
> has a threshold, and none has been run against a recorded or hardware
> dataset.

## Shipped declarations

| File | Kind | Level | Data source | Thresholds |
|---|---|---|---|---|
| `suites/template-position-accuracy.yaml` | `position_error` | L4 | `recorded` | none |
| `suites/template-scalar-latency.yaml` | `scalar` | L4 | `recorded` | none |
| `suites/template-success-rate.yaml` | `success_rate` | L3 | `mock` | none |

A template with zero thresholds produces an `inconclusive`, informational
report. That is intentional: a threshold must be registered before the data is
collected and must cite its source.

The loader rejects `L4` with synthetic/mock data and `L5` with anything other
than `data_source: hardware`.

## Dataset shape

Each line is one sample:

```json
{"sample_id":"pose-001-r01","trial":"pose-001","measured_m":[0.3347,-0.0147,-0.0835],"reference_m":[0.3354,-0.0127,-0.0857],"latency_ms":54.1,"success":true}
```

- `sample_id` is required and unique.
- `trial` is optional and is counted in the report.
- `measured_m` and `reference_m` are metres, used only by `position_error`.
- A `scalar` metric names one finite numeric field.
- A `success_rate` metric names one boolean field, default `success`.

The full field and failure rules are in
[`docs/BENCHMARK_PROTOCOL.md`](../docs/BENCHMARK_PROTOCOL.md).

## Adding a suite

1. Copy a template and give it a new `suite` id.
2. Write the question, level, data source, `min_samples` and thresholds before
   collecting data.
3. Cite the threshold source in `limitations`.
4. Commit the suite.
5. Export the dataset outside the repository.
6. Run with `--operator`, `--host` and a note; store the report under
   `evidence/benchmark_<YYYYMMDD>_<slug>/`.

There is no benchmark result in this repository yet. Do not add a suite whose
threshold is a guess.

## Related

- [`docs/BENCHMARK_PROTOCOL.md`](../docs/BENCHMARK_PROTOCOL.md) — protocol.
- [`docs/EVIDENCE.md`](../docs/EVIDENCE.md) — report storage.
- [`README.md`](../README.md) — repository scope.
