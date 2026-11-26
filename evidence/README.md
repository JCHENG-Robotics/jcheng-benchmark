# Evidence

> Status: **empty** as of 2026-11-26. No benchmark report has been recorded.

`v0.1.0` ships no recorded dataset and no benchmark result. This directory will
hold one subdirectory per run:

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

## Related

- [`docs/EVIDENCE.md`](../docs/EVIDENCE.md) — naming and companion files.
- [`docs/BENCHMARK_PROTOCOL.md`](../docs/BENCHMARK_PROTOCOL.md) — result semantics.
- [`ACCEPTANCE.md`](../ACCEPTANCE.md) — current claim status.
