# Evidence storage

> Status: **v0.1.0 plus one migrated live snapshot** as of 2026-11-26. No
> `benchmark-report` v1 result has been recorded.

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

- `host_benchmark_20261117_session4/` — the only evidence bundle; a read-only
  host/DDS snapshot migrated on 2026-11-26 from the frozen
  `jcheng-manipulation` baseline. It is not a harness report and no suite
  threshold was evaluated.

`v0.1.0` has no recorded dataset and no harness benchmark result. The synthetic
fixture under `tests/fixtures/synthetic/` is a harness self-test and is not
stored here as evidence.

## 7. Migrated live-probe snapshots

The quarantined probe under `tools/live/` writes a different, legacy-shaped
bundle. It uses `evidence/host_benchmark_<YYYYMMDD>_<slug>/` with per-host
files:

```text
evidence/host_benchmark_<YYYYMMDD>_<slug>/
├── README.md            # scope, operator and provenance
├── laptop_host.json/.txt
├── ping_robot.txt
├── robot_host.json/.txt
├── robot_ros.json/.txt
└── laptop_ros.json/.txt
```

These are raw snapshots, not `benchmark-report` v1 documents: there is no
suite, no threshold and no dataset hash. They must not be counted as a suite
pass and must not be mixed with `evidence/benchmark_<date>_<suite>/`. The
runner refuses a non-empty directory, so a rerun creates a new bundle; record
the operator and the read-only nature of the session in the bundle `README.md`.

## Related

- [BENCHMARK_PROTOCOL.md](BENCHMARK_PROTOCOL.md) — result semantics and report fields.
- [ARCHITECTURE.md](ARCHITECTURE.md) — trust boundary.
- [`evidence/README.md`](../evidence/README.md) — directory status.
