"""Static boundary checks for the quarantined live probe under tools/live/.

The probe may subscribe to a live ROS graph, but it must never publish, call a
service, open a device, command motion or restart a container. The offline
harness under src/ must not import or reference the probe, and setuptools must
not package it.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "tools" / "live"

# Tokens that would indicate a write, device or motion path. Subscription-only
# ROS imports (rclpy, rosidl) are expected in the probe and are not listed.
FORBIDDEN = (
    "create_publisher",
    "create_client",
    "executemotion",
    "publish(",
    "call_async",
    "spin_until_future",
    "/dev/",
    "pyserial",
    "serial.serial",
    "socketcan",
    "can0",
    "pigpio",
    "rpi.gpio",
    "gpiozero",
    "os.system",
    "docker restart",
    "docker stop",
    "docker rm",
    "systemctl restart",
)

PROBE_SOURCES = ("host_benchmark.py", "run_benchmark.sh")


def test_probe_has_no_write_device_or_motion_path() -> None:
    problems = []
    for name in PROBE_SOURCES:
        path = PROBE / name
        assert path.exists(), f"missing probe source: {path}"
        text = path.read_text(encoding="utf-8").lower()
        # /dev/null is a stream redirect, not a device access.
        text = text.replace("/dev/null", "")
        for token in FORBIDDEN:
            if token in text:
                problems.append(f"{path.relative_to(ROOT)}: {token}")
    assert not problems, "write/device/motion token in tools/live:\n" + "\n".join(problems)


def test_offline_harness_does_not_reference_the_probe() -> None:
    problems = []
    for path in sorted((ROOT / "src").rglob("*")):
        if path.is_file() and path.suffix in {".py", ".yaml", ".yml", ".toml"}:
            text = path.read_text(encoding="utf-8").lower()
            if "tools/live" in text or "host_benchmark" in text:
                problems.append(str(path.relative_to(ROOT)))
    assert not problems, "offline harness references the live probe:\n" + "\n".join(problems)


def test_probe_is_not_packaged() -> None:
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'package-dir = {"" = "src"}' in pyproject
    assert 'where = ["src"]' in pyproject
