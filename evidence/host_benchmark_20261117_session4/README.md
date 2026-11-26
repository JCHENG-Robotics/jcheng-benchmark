# Host/DDS benchmark snapshots — 2026-11-17 (Session 4)

Migrated 2026-11-26 from `jcheng-manipulation`
(`evidence/phase3/session4_20261117/`), baseline commit
`a08b8b682e1dbdb721a986b9d9d23460a9fc22b4` (`v1.0.0-31-ga08b8b6`). The raw
files were copied byte-for-byte and are **not** edited; this README is the only
new document in the directory.

## Scope

Read-only hardware measurement of the 2026-11-17 environment: one laptop and
one Raspberry Pi 5, one snapshot per host, no camera/load sweep. No robot
motion, grasp, calibration capture or vendor demo was executed. The camera
launch was started only for the `with_camera` run and stopped afterwards.

This is **not** a `benchmark-report` v1 result: there is no suite, no
pre-registered threshold and no dataset hash. The probe is documented in
[`../../docs/HOST_BENCHMARK.md`](../../docs/HOST_BENCHMARK.md) and
[`../../tools/live/README.md`](../../tools/live/README.md).

## Contents

| Path | Content |
|---|---|
| `no_camera/` | Laptop host, Pi host, Pi container ROS and laptop ROS; camera not running |
| `with_camera/` | The same collection while the RGB/depth camera was running |
| `commands.log` | Session 4 command record; the benchmark section is near the end. Covers error-budget and paired-trial commands too, which stayed in the baseline |
| `tests.txt` | Session 4 build/test summary (colcon 94 tests, pure-Python 49 passed) |

Each snapshot directory contains:

```text
laptop_host.json / .txt     host metrics, laptop
ping_robot.txt              ICMP RTT, laptop -> Pi
robot_host.json / .txt      host metrics, Pi host
robot_ros.json / .txt       topic receipt, Pi container (CycloneDDS)
laptop_ros.json / .txt      topic receipt, laptop (cross-host, Fast DDS)
```

## Key results (copied from the baseline report)

| Item | Result |
|---|---|
| Laptop host | Ryzen 7 5800H, 16 cores, 4.4–4.7% CPU, 27.9 GB, disk 14.3% |
| Pi host | Pi 5, 4 cores, 1.8% idle / 10.7% with camera, 8.05 GB, disk 84.7% (6.6 GB free), 46.9–48.0 °C |
| Ping | 0.239–0.254 ms avg, 0.281–0.298 ms max, 0% loss |
| `/joint_states` | 20.00 Hz, jitter 0.16 ms local / 0.30–0.60 ms cross-host |
| `/controller_manager/joint_states` | 48.8 Hz local / 48.5 Hz cross-host |
| Camera RGB | **~12 Hz cross-host**, 8.33 Hz in-container subscription, 7.0 Hz in-container `ros2 topic hz` |

## Rules

- Do not label these snapshots as a benchmark pass or a safety/accuracy
  certification.
- Do not quote the in-container camera FPS as the sensor rate; use the
  cross-host measurement and state the location.
- These files are append-only evidence. A rerun creates a new directory; do not
  edit or overwrite the JSON here.
- `commands.log` and `tests.txt` are the baseline records for the whole
  Session 4, not only the benchmark. Their error-budget and paired-trial
  entries refer to files that remain in `jcheng-manipulation`.
