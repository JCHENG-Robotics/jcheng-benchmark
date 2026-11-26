# Evidence storage

> Status: **v0.1.0** as of 2026-11-26. No benchmark report has been recorded;
> the directory contains only this README.

## 1. Directory naming

One run, one directory:

```text
evidence/benchmark_<YYYYMMDD>_<suite-slug>/
├── report.json          # machine-readable benchmark report
├── report.md            # Markdown rendering of the same report
├── command.txt          # the exact command and git commit
├── environment.txt      # OS, Python, PyYAML, host and relevant notes
└── dataset.txt          # dataset path, SHA-256, size, capture session
```

The date is the run date in ISO 8601 basic form (`20261126`). The slug matches
the suite id. If the same suite is run twice on the same day, add a suffix:
`benchmark_20261126_position-accuracy_r2/`.

## 2. Required companion files

`report.json` and `report.md` are produced by the harness. The other three
files are written by the operator and must not contradict the report:

- **`command.txt`** — the exact `jcheng-benchmark run` command, the repository
  commit and the suite path.
- **`environment.txt`** — host, OS, Python version, PyYAML version and any
  load or container note that could affect latency.
- **`dataset.txt`** — dataset path, SHA-256, sample count and, for recorded or
  hardware data, the capture date and the source repository.

For `data_source: hardware`, also record the operator's authorization for that
session. A hardware report without an authorization record is not acceptable
evidence.

## 3. Dataset handling

Datasets stay outside the repository. The report records the path and SHA-256;
the path may be machine-specific and is not a distribution mechanism. Do not
commit a dataset unless its license and the operator's permission have been
reviewed.

If a dataset must be retained long-term, put it in the workspace dataset area
or an external archive and record the archive location in `dataset.txt`. Do not
put it under `tests/fixtures/`; that directory is only for deterministic
synthetic self-tests.

## 4. Immutability

Reports are append-only:

- Do not edit `report.json` or `report.md` after they are committed.
- A rerun creates a new directory; it does not overwrite the old one.
- If a report is wrong, add a short `NOTE.md` beside it explaining what is
  wrong and which later report supersedes it. Keep the original.
- The suite SHA-256 and dataset SHA-256 in the report identify exactly what was
  run. If either input changes, it is a new run.

## 5. What is not evidence

- A synthetic or mock report for a hardware claim.
- A report without a dataset hash or without the operator.
- A Markdown file with the numbers edited by hand.
- A threshold that was changed after the data was collected.
- A successful run that omits earlier failed runs.

## 6. Current contents

None. `v0.1.0` has no recorded dataset and no benchmark result. The synthetic
fixture under `tests/fixtures/synthetic/` is a harness self-test and is not
stored here as evidence.

## Related

- [BENCHMARK_PROTOCOL.md](BENCHMARK_PROTOCOL.md) — result semantics and report fields.
- [ARCHITECTURE.md](ARCHITECTURE.md) — trust boundary.
- [`evidence/README.md`](../evidence/README.md) — directory status.
