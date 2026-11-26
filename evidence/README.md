# Evidence

> Status: **one migrated live-probe snapshot bundle** as of 2026-11-26. No
> `benchmark-report` v1 result has been recorded.

`v0.1.0` ships no recorded dataset and no harness benchmark result. Harness runs
go in one subdirectory per run:

```text
evidence/benchmark_<YYYYMMDD>_<suite-slug>/
├── report.json
├── report.md
├── command.txt
├── environment.txt
└── dataset.txt
```

Reports are append-only; a rerun creates a new directory. The full rules,
including the hardware-authorization record, are in
[`docs/EVIDENCE.md`](../docs/EVIDENCE.md).

The synthetic fixture under `tests/fixtures/synthetic/` is a harness self-test,
not evidence, and is not stored here.

## Migrated live-probe evidence

`host_benchmark_20261117_session4/` is the 2026-11-17 host/DDS snapshot bundle,
copied byte-for-byte from the frozen `jcheng-manipulation` v1.0.0 baseline on
2026-11-26. It has a different shape from a harness report (per-host JSON and
text files, no suite, no threshold, no dataset hash) and must never be counted
as a `benchmark-report` v1 result. See its
[`README.md`](host_benchmark_20261117_session4/README.md) and
[`docs/HOST_BENCHMARK.md`](../docs/HOST_BENCHMARK.md).

## Related

- [`docs/EVIDENCE.md`](../docs/EVIDENCE.md) — naming and companion files.
- [`docs/BENCHMARK_PROTOCOL.md`](../docs/BENCHMARK_PROTOCOL.md) — result semantics.
- [`ACCEPTANCE.md`](../ACCEPTANCE.md) — current claim status.
