# Live host/DDS probe (quarantined)

> Status: **Experimental, migrated 2026-11-26** from the frozen
> `jcheng-manipulation` v1.0.0 baseline. It is an operator tool, not part of
> the offline harness and not a runtime capability.

## Why this directory exists

The 2026-11-17 Session 4 host/DDS benchmark originally lived in
`jcheng-manipulation` (`armpi_analysis/host_benchmark.py`,
`tools/phase4/run_benchmark.sh`). Benchmark ownership moved to this repository,
so the tool, its runner, its tests, its documentation and its evidence were
copied here.

The copy is deliberately quarantined:

- it is **not** imported by `jcheng_benchmark`;
- setuptools does not install it (only `src/` is packaged);
- CI runs only its host-only path, with `SKIP_ROBOT=1` and
  `SKIP_LAPTOP_ROS=1`, so no network call is made;
- it produces raw per-host JSON snapshots, **not** a `benchmark-report` v1
  document, and it never satisfies a suite threshold.

The offline harness keeps its own boundary: no ROS client library, no DDS, no
device, no subprocess. `tests/test_live_probe_boundary.py` enforces that this
directory contains no publisher, no device access and no motion path.

## Files

| File | Role |
|---|---|
| `host_benchmark.py` | Standalone read-only probe. `host` mode reads `/proc`, `/sys` and `shutil.disk_usage`; `ros` mode subscribes to topics for a fixed duration and summarizes receipt. |
| `run_benchmark.sh` | One-command collection: laptop host, ping, robot host over SSH, robot container ROS, laptop ROS. Writes an append-only evidence directory. |
| `tests/test_host_benchmark.py` | Unit tests for the interval statistics, host collection shape and CLI JSON output. |
| `tests/test_run_benchmark.py` | Bash syntax, laptop-only run, no-network assertion and the append-only guard. |

## Safety model

- **Read-only.** No publisher, no service call, no parameter write, no motion
  command, no lease. The ROS mode only creates subscriptions.
- **No device access.** No camera, serial, CAN, GPIO, servo or LiDAR device is
  opened. `host` mode reads host counters only.
- **No container restart.** `run_benchmark.sh` only runs `docker exec` to
  measure inside the already-running vendor container. Never restart the
  vendor container: its startup checks move the arm.
- **Operator-initiated.** Never run the robot steps from CI or unattended. The
  robot's SSH access uses `pi@10.42.0.218` with NOPASSWD sudo; treat every run
  as a hardware session and record who ran it.
- **Append-only evidence.** The runner refuses a non-empty output directory.
  A rerun needs a new directory.

## Usage

The probe targets Linux: it reads `/proc` and `/sys` and uses `ssh` plus
`docker`. Its host-only tests are skipped on other platforms.

Laptop-only (the path CI exercises; no robot, no ROS, no network):

```bash
SKIP_ROBOT=1 SKIP_LAPTOP_ROS=1 tools/live/run_benchmark.sh /tmp/host-probe
```

Full read-only collection (requires the robot and SSH key; hardware session):

```bash
tools/live/run_benchmark.sh evidence/host_benchmark_$(date -u +%Y%m%d)_live_$(date -u +%H%M%S)
```

Single probe, no runner:

```bash
python3 tools/live/host_benchmark.py --mode host --json-out /tmp/host.json

source /opt/ros/jazzy/setup.bash
python3 tools/live/host_benchmark.py --mode ros --topics /joint_states \
  --duration-s 10 --json-out /tmp/ros.json
```

Output files: `laptop_host.json/.txt`, `ping_robot.txt`, `robot_host.json/.txt`,
`robot_ros.json/.txt`, `laptop_ros.json/.txt`. The script skips the robot steps
when it is unreachable and skips the ROS steps when the container is absent;
check the `.txt` files for `WARN` lines.

## Tests

```bash
python3 -m pytest -q tools/live/tests tests/test_live_probe_boundary.py
```

The host-only tests run anywhere with Python. `ros` mode is not unit-tested
because it requires a live ROS graph; it was exercised on real hardware in the
baseline session (2026-11-17).

## Provenance

Copied from `jcheng-manipulation` at `v1.0.0-31-ga08b8b6`
(commit `a08b8b682e1dbdb721a986b9d9d23460a9fc22b4`, 2026-11-25). Source paths
and SHA-256 at copy time:

| Source | SHA-256 |
|---|---|
| `ros2_ws/src/armpi_analysis/armpi_analysis/host_benchmark.py` | `2cd6adc1b0b3b17c200539c33ebfe702e400a911088d785fc7599e0631144ce1` |
| `tools/phase4/run_benchmark.sh` | `6736742ba70b2469227919be60af5e1f43c32d767dbc7784f61f44655c3d8544` |
| `ros2_ws/src/armpi_analysis/test/test_host_benchmark.py` | `9e00d506d7367a9a7fe58acdd49f57b1d527c6693523e7bd95152e098eae3fd9` |
| `tools/phase4/tests/test_run_benchmark.py` | `e2b77e3353dbb6c0f11fe451d02e999d41f854da0598d35254af4da99f350306` |

Behaviour changes in the migration: the default output directory is
date-stamped, the non-empty-directory guard was added, `ping` moved under
`SKIP_ROBOT`, and the tests import the probe by path instead of through the
`armpi_analysis` package. The measurement code itself is unchanged.

## What this is not

- Not a benchmark suite and not a `benchmark-report` v1 result.
- Not an acceptance report and not a safety certification.
- Not a live acquisition adapter for the harness: it writes snapshots and does
  not export a dataset. That adapter remains M4 in the roadmap.

## Related

- [../../docs/HOST_BENCHMARK.md](../../docs/HOST_BENCHMARK.md) — the measured
  results and their limitations.
- [../../evidence/host_benchmark_20261117_session4/](../../evidence/host_benchmark_20261117_session4/)
  — raw 2026-11-17 snapshots.
- [../../docs/ARCHITECTURE.md](../../docs/ARCHITECTURE.md) — harness trust
  boundary.
